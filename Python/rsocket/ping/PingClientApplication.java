package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Flux;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

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

    @Value("${ping.client.summary-interval-seconds:60}")
    private int summaryIntervalSeconds;

    private final AtomicInteger pingsSentCounter = new AtomicInteger(0);
    private final AtomicInteger pongsReceivedCounter = new AtomicInteger(0);

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

        // Log summary of pings sent and pongs received based on the configured interval
        Flux.interval(Duration.ofSeconds(summaryIntervalSeconds))
                .subscribe(i -> {
                    int pingsSent = pingsSentCounter.getAndSet(0);
                    int pongsReceived = pongsReceivedCounter.getAndSet(0);
                    System.out.println("Client Summary - Pings Sent: " + pingsSent + ", Pongs Received: " + pongsReceived);
                });
    }

    private void sendStreamingRequest(RSocketRequester requester, int threadId, long intervalMillis) {
        AtomicInteger count = new AtomicInteger(1);

        Flux.interval(Duration.ofMillis(intervalMillis))
                .flatMap(i -> {
                    String message = "ping-node-" + nodeId + "-thread-" + threadId + "-count-" + count.getAndIncrement();
                    pingsSentCounter.incrementAndGet();

                    return requester.route("ping")
                            .data(message)
                            .retrieveFlux(String.class)
                            .doOnNext(response -> {
                                System.out.println("Received: " + response);
                                pongsReceivedCounter.incrementAndGet();
                            })
                            .doOnError(e -> System.err.println("Client error: " + e.getMessage()));
                })
                .subscribe();
    }
}
