package com.example.pingclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class PingClientApplication {

    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }

    @Bean
    CommandLineRunner runner(PingService pingService) {
        return args -> pingService.startPinging();
    }

    @Service
    public static class PingService {
        private final ScheduledExecutorService executorService;
        private final RSocketRequester rSocketRequester;

        private final AtomicInteger totalPingsSent = new AtomicInteger();
        private final AtomicInteger totalPongsReceived = new AtomicInteger();
        private final AtomicInteger checksumFailures = new AtomicInteger();
        private final AtomicInteger noResponseFailures = new AtomicInteger();

        private final String nodeId;

        private final int paddingSize;
        private final int ratePerSecond;
        private final int threadCount;

        public PingService(RSocketRequester.Builder builder,
                           @Value("${ping.nodeId}") int nodeId,
                           @Value("${ping.paddingSize}") int paddingSize,
                           @Value("${ping.ratePerSecond}") int ratePerSecond,
                           @Value("${ping.threadCount}") int threadCount,
                           @Value("${rsocket.serverAddress}") String serverAddress,
                           @Value("${rsocket.serverPort}") int serverPort) {
            this.executorService = Executors.newScheduledThreadPool(threadCount);
            this.nodeId = "node-" + nodeId; // Prefix the node ID dynamically
            this.paddingSize = paddingSize;
            this.ratePerSecond = ratePerSecond;
            this.threadCount = threadCount;
            this.rSocketRequester = builder.connectTcp(serverAddress, serverPort).block();
        }

        public void startPinging() {
            Runnable task = () -> {
                String payload = generatePayload();
                String checksum = calculateChecksum(payload);

                rSocketRequester
                    .route("ping")
                    .data(new PingRequest(nodeId, Thread.currentThread().getName(), payload, checksum))
                    .retrieveMono(PongResponse.class)
                    .timeout(Duration.ofSeconds(5))
                    .doOnNext(this::processResponse)
                    .doOnError(e -> handleFailure(e, payload, checksum))
                    .subscribe();

                totalPingsSent.incrementAndGet();
            };

            for (int i = 0; i < threadCount; i++) {
                executorService.scheduleAtFixedRate(task, 0, 1000 / ratePerSecond, TimeUnit.MILLISECONDS);
            }
        }

        private String generatePayload() {
            return "0".repeat(paddingSize);
        }

        private String calculateChecksum(String payload) {
            return Integer.toHexString(payload.hashCode());
        }

        private void processResponse(PongResponse response) {
            long rtt = System.currentTimeMillis() - response.timestamp(); // Access timestamp() directly
            if (!response.checksum().equals(calculateChecksum(response.payload()))) { // Use checksum() and payload()
                checksumFailures.incrementAndGet();
                System.err.printf("Checksum mismatch for pong from %s%n", response.serverId());
            } else {
                totalPongsReceived.incrementAndGet();
                System.out.printf("Pong from %s: RTT=%dms, Checksum=%s%n", response.serverId(), rtt, response.checksum());
            }
        }

        private void handleFailure(Throwable e, String payload, String checksum) {
            noResponseFailures.incrementAndGet();
            System.err.printf("Ping failed: Payload=%s, Checksum=%s, Error=%s%n", payload, checksum, e.getMessage());
        }
    }

    @RestController
    public static class PingHealthController {
        private final PingService pingService;

        public PingHealthController(PingService pingService) {
            this.pingService = pingService;
        }

        @GetMapping("/health")
        public Map<String, Object> getHealth() {
            Map<String, Object> metrics = new HashMap<>();
            metrics.put("totalPingsSent", pingService.totalPingsSent.get());
            metrics.put("totalPongsReceived", pingService.totalPongsReceived.get());
            metrics.put("checksumFailures", pingService.checksumFailures.get());
            metrics.put("noResponseFailures", pingService.noResponseFailures.get());
            return metrics;
        }
    }

    public static record PingRequest(String nodeId, String threadId, String payload, String checksum) {}
    public static record PongResponse(String serverId, String payload, String checksum, long timestamp) {}
}
