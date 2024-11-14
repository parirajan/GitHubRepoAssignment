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

    @Value("${ping.client.payload-template:ping-node-{nodeId}-thread-{threadId}-count-{count}}")
    private String payloadTemplate;

    @Value("${ping.client.padding-size:150}")
    private int paddingSize;

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

        // Keep the application running
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

                // Add padding and calculate checksum
                String paddingData = generatePadding(paddingSize);
                long clientChecksum = calculateChecksum(paddingData);
                String paddedMessage = message + "-" + paddingData + "-" + clientChecksum;

                // Capture start time for RTT
                Instant startTime = Instant.now();

                System.out.println("Sending message: " + paddedMessage);

                return requester.route("ping")
                        .data(paddedMessage)
                        .retrieveFlux(String.class)
                        .doOnNext(response -> {
                            // Calculate RTT
                            long rtt = Duration.between(startTime, Instant.now()).toMillis();

                            // Extract server response and checksum
                            String[] parts = response.split("-");
                            StringBuilder serverResponse = new StringBuilder();

                            // Reconstruct the server response without the checksum part
                            for (int j = 0; j < parts.length - 1; j++) {
                                serverResponse.append(parts[j]);
                                if (j < parts.length - 2) {
                                    serverResponse.append("-");
                                }
                            }

                            long serverChecksum = Long.parseLong(parts[parts.length - 1]);

                            // Validate checksum
                            boolean isChecksumValid = (clientChecksum == serverChecksum);

                            // Log RTT and validation
                            System.out.println(serverResponse.toString());
                            System.out.println("RTT: " + rtt + "ms, Validation: " + isChecksumValid +
                                    ", Thread: " + threadId + ", Count: " + count.get() +
                                    ", Src Cksum: " + clientChecksum + ", Target Cksum: " + serverChecksum);
                        })
                        .doOnError(e -> System.err.println("Client error: " + e.getMessage()));
            })
            .subscribe();
    }

    private String formatPayload(String nodeId, int threadId, int count) {
        return payloadTemplate
                .replace("{nodeId}", nodeId)
                .replace("{threadId}", String.valueOf(threadId))
                .replace("{count}", String.valueOf(count));
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
