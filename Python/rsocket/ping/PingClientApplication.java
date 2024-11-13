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

    @Value("${ping.client.payload-template:ping-node-$$\\{nodeId}-thread-$$\\{threadId}-count-$$\\{count}}")
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

                // Add extra 150 bytes of dummy data with a '-' after the count
                String paddedMessage = addExtraBytes(message + "-", 150);

                System.out.println("Sending message: " + paddedMessage);

                // Send the message and expect the same message back
                return requester.route("ping")
                        .data(paddedMessage)
                        .retrieveFlux(String.class)
                        .doOnNext(response -> System.out.println("Received response: " + response))
                        .doOnError(e -> System.err.println("Client error: " + e.getMessage()));
            })
            .subscribe();
    }

    private String formatPayload(String nodeId, int threadId, int count) {
        return payloadTemplate
                .replace("$$\\{nodeId}", nodeId)
                .replace("$$\\{threadId}", String.valueOf(threadId))
                .replace("$$\\{count}", String.valueOf(count));
    }

    private String addExtraBytes(String message, int extraBytes) {
        StringBuilder builder = new StringBuilder(message);
        Random random = new Random();

        for (int i = 0; i < extraBytes; i++) {
            // Add random ASCII characters to the message
            char randomChar = (char) (random.nextInt(26) + 'a');
            builder.append(randomChar);
        }

        return builder.toString();
    }
}
