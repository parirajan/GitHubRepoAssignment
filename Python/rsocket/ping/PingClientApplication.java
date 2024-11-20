package com.mycompany.pingclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.context.WebServerInitializedEvent;
import org.springframework.context.annotation.Bean;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Flux;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.epoll.EpollEventLoopGroup;
import io.rsocket.transport.netty.client.TcpClientTransport;
import reactor.netty.tcp.TcpClient;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
@EnableScheduling
public class PingClientApplication {

    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }

    @Bean
    public RSocketRequester.Builder rSocketRequesterBuilder() {
        return RSocketRequester.builder();
    }

    @EventListener(WebServerInitializedEvent.class)
    public void logServerDetails(WebServerInitializedEvent event) {
        int port = event.getWebServer().getPort();
        System.out.printf("Tomcat server started on port %d%n", port);
        System.out.println("Available REST Endpoints:");
        System.out.printf("  - Summary: http://localhost:%d/summary%n", port);
        System.out.printf("  - Health: http://localhost:%d/health%n", port);
    }
}

@Component
class PingClient implements CommandLineRunner {

    private final RSocketRequester.Builder requesterBuilder;

    @Value("${ping.server.host}")
    private String host;

    @Value("${ping.server.port}")
    private int port;

    @Value("${ping.client.node-id}")
    private String nodeId;

    @Value("${ping.client.threads}")
    private int numThreads;

    @Value("${ping.client.pings-per-second}")
    private int pingsPerSecond;

    @Value("${ping.client.payload-template}")
    private String payloadTemplate;

    @Value("${ping.client.padding-size}")
    private int paddingSize;

    private final AtomicInteger totalPingsSent = new AtomicInteger();
    private final AtomicInteger totalPongsReceived = new AtomicInteger();
    private final AtomicInteger totalFailures = new AtomicInteger();
    private final AtomicInteger totalRTT = new AtomicInteger();

    private final AtomicInteger pingsSentPerSecond = new AtomicInteger();
    private final AtomicInteger pongsReceivedPerSecond = new AtomicInteger();

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) {
        EventLoopGroup eventLoopGroup = new EpollEventLoopGroup(numThreads);

        RSocketRequester requester = requesterBuilder.dataMimeType(MimeTypeUtils.TEXT_PLAIN)
            .transport(TcpClientTransport.create(
                TcpClient.create()
                    .host(host)
                    .port(port)
                    .runOn(eventLoopGroup)                               // Use custom EventLoopGroup
                    .option(ChannelOption.SO_RCVBUF, 16 * 1024 * 1024)  // Set receive buffer size
                    .option(ChannelOption.SO_SNDBUF, 16 * 1024 * 1024)  // Set send buffer size
                    .option(ChannelOption.TCP_NODELAY, true)            // Disable Nagle's algorithm
                    .option(ChannelOption.SO_KEEPALIVE, true)           // Enable TCP Keep-Alive
            ));

        AtomicInteger threadIdCounter = new AtomicInteger(1);
        long intervalMillis = 1000 / pingsPerSecond;

        for (int i = 0; i < numThreads; i++) {
            int threadId = threadIdCounter.getAndIncrement();
            sendStreamingRequest(requester, threadId, intervalMillis);
        }

        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private void sendStreamingRequest(RSocketRequester requester, int threadId, long intervalMillis) {
        AtomicInteger count = new AtomicInteger(1);

        Flux.interval(Duration.ofMillis(intervalMillis))
            .flatMap(i -> {
                String message = formatPayload(nodeId, threadId, count.getAndIncrement());
                String paddedMessage = addExtraBytes(message, paddingSize);
                Instant startTime = Instant.now(); // Record start time for RTT

                System.out.println("Sending message: " + paddedMessage);
                totalPingsSent.incrementAndGet();
                pingsSentPerSecond.incrementAndGet();

                return requester
                    .route("ping")
                    .data(paddedMessage)
                    .retrieveFlux(String.class)
                    .doOnNext(response -> {
                        Instant endTime = Instant.now(); // Record end time for RTT
                        int rtt = (int) Duration.between(startTime, endTime).toMillis(); // Calculate RTT

                        System.out.printf("Received response: %s | RTT: %d ms%n", response, rtt);
                        totalPongsReceived.incrementAndGet();
                        pongsReceivedPerSecond.incrementAndGet();
                        totalRTT.addAndGet(rtt); // Accumulate RTT
                    })
                    .doOnError(e -> {
                        System.err.println("Failed to send ping: " + e.getMessage());
                        totalFailures.incrementAndGet();
                    });
            })
            .subscribe();
    }

    private String formatPayload(String nodeId, int threadId, int count) {
        return payloadTemplate
            .replace("{nodeId}", nodeId)
            .replace("{threadId}", String.valueOf(threadId))
            .replace("{count}", String.valueOf(count));
    }

    private String addExtraBytes(String message, int extraBytes) {
        StringBuilder builder = new StringBuilder(message);
        Random random = new Random();
        for (int i = 0; i < extraBytes; i++) {
            builder.append((char) (random.nextInt(26) + 'a'));
        }
        return builder.toString();
    }

    public Map<String, Object> getMetrics() {
        int averageRTT = totalPongsReceived.get() == 0 ? 0 : totalRTT.get() / totalPongsReceived.get();

        return Map.of(
            "totalPingsSent", totalPingsSent.get(),
            "totalPongsReceived", totalPongsReceived.get(),
            "totalFailures", totalFailures.get(),
            "pingsPerSecond", pingsSentPerSecond.get(),
            "pongsPerSecond", pongsReceivedPerSecond.get(),
            "averageRTT", averageRTT
        );
    }

    @Scheduled(fixedRate = 1000) // Reset per-second counters every second
    public void resetPerSecondCounters() {
        pingsSentPerSecond.set(0);
        pongsReceivedPerSecond.set(0);
    }

    @Scheduled(fixedRateString = "${reporting.interval.ms:5000}")
    public void reportMetricsToConsole() {
        System.out.println("Metrics Report:");
        System.out.printf("  Total Pings Sent: %d%n", totalPingsSent.get());
        System.out.printf("  Total Pongs Received: %d%n", totalPongsReceived.get());
        System.out.printf("  Total Failures: %d%n", totalFailures.get());
        System.out.printf("  Pings Sent Per Second: %d%n", pingsSentPerSecond.get());
        System.out.printf("  Pongs Received Per Second: %d%n", pongsReceivedPerSecond.get());
        int averageRTT = totalPongsReceived.get() == 0 ? 0 : totalRTT.get() / totalPongsReceived.get();
        System.out.printf("  Average RTT: %d ms%n", averageRTT);
   
