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

    // Payload template with placeholders, defined in application.yml
    @Value("${ping.client.payload-template:ping-$$\\{nodeId}-thread-$$\\{threadId}-count-$$\\{count}}")
    private String payloadTemplate;

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

        // Start multiple threads to send streaming requests
        for (int i = 0; i < numThreads; i++) {
            int threadId = threadIdCounter.getAndIncrement();
            sendStreamingRequest(requester, threadId, intervalMillis);
        }

        // Keep the application running
        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /**
     * Sends a streaming request at the configured rate.
     */
    private void sendStreamingRequest(RSocketRequester requester, int threadId, long intervalMillis) {
        AtomicInteger count = new AtomicInteger(1);

        Flux.interval(Duration.ofMillis(intervalMillis))
            .flatMap(i -> {
                String message = formatPayload(nodeId, threadId, count.getAndIncrement());
                System.out.println("Sending message: " + message);
                return requester.route("ping")
                        .data(message)
                        .retrieveFlux(String.class)
                        .doOnNext(response -> System.out.println("Received response: " + response))
                        .doOnError(e -> System.err.println("Client error: " + e.getMessage()));
            })
            .subscribe();
    }

    /**
     * Formats the payload using the template defined in application.yml.
     */
    private String formatPayload(String nodeId, int threadId, int count) {
        return payloadTemplate
                .replace("$$\\{nodeId}", nodeId)
                .replace("$$\\{threadId}", String.valueOf(threadId))
                .replace("$$\\{count}", String.valueOf(count));
    }
}
