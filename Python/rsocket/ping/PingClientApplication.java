package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.CRC32;
import java.util.Random;

@SpringBootApplication
public class PingClientApplication {
    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
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

    @Value("${ping.client.threads:5}")
    private int numThreads;

    @Value("${ping.client.pings-per-second:10}")
    private int pingsPerSecond;

    @Value("${ping.client.padding-size:150}")
    private int paddingSize;

    @Value("${ping.client.summary-interval-seconds:60}")
    private int summaryIntervalSeconds;

    private final AtomicInteger pingsSentCounter = new AtomicInteger(0);
    private final AtomicInteger pongsReceivedCounter = new AtomicInteger(0);
    private final AtomicInteger checksumFailures = new AtomicInteger(0);

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) {
        RSocketRequester requester = requesterBuilder
                .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
                .tcp(host, port);

        AtomicInteger threadIdCounter = new AtomicInteger(1);
        long intervalMillis = 1000L / pingsPerSecond;

        for (int i = 0; i < numThreads; i++) {
            int threadId = threadIdCounter.getAndIncrement();
            sendStreamingRequest(requester, threadId, intervalMillis);
        }

        // Log summary every configured interval
        Flux.interval(Duration.ofSeconds(summaryIntervalSeconds))
                .subscribeOn(Schedulers.boundedElastic())
                .doOnNext(i -> {
                    int pingsSent = pingsSentCounter.getAndSet(0);
                    int pongsReceived = pongsReceivedCounter.getAndSet(0);
                    int checksumErrors = checksumFailures.getAndSet(0);
                    System.out.println("Client Summary - Pings Sent: " + pingsSent +
                            ", Pongs Received: " + pongsReceived + ", Checksum Errors: " + checksumErrors);
                })
                .subscribe();

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
                    String message = "ping-node-" + nodeId + "-thread-" + threadId + "-count-" + count.getAndIncrement();
                    String padding = generatePadding(paddingSize);
                    long clientChecksum = calculateChecksum(padding);
                    String paddedMessage = message + "-" + padding + "-" + clientChecksum;

                    Instant startTime = Instant.now();
                    pingsSentCounter.incrementAndGet();

                    System.out.println("Sending: " + paddedMessage);

                    return requester.route("ping")
                            .data(paddedMessage)
                            .retrieveFlux(String.class)
                            .doOnNext(response -> {
                                Instant endTime = Instant.now();
                                long rtt = Duration.between(startTime, endTime).toMillis();
                                String[] parts = response.split("-");
                                String serverNodeId = parts[parts.length - 2];
                                long serverChecksum = Long.parseLong(parts[parts.length - 1]);

                                boolean isValid = clientChecksum == serverChecksum;
                                if (!isValid) checksumFailures.incrementAndGet();

                                System.out.println("Received from server " + serverNodeId +
                                        " | RTT: " + rtt + "ms, Checksum Valid: " + isValid);
                                pongsReceivedCounter.incrementAndGet();
                            })
                            .doOnError(e -> System.err.println("Client error: " + e.getMessage()));
                })
                .subscribeOn(Schedulers.boundedElastic())
                .subscribe();
    }

    private String generatePadding(int size) {
        StringBuilder builder = new StringBuilder();
        Random random = new Random();
        for (int i = 0; i < size; i++) {
            builder.append((char) (random.nextInt(26) + 'a'));
        }
        return builder.toString();
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }
}
