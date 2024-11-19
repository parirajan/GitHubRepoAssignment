package com.example.pongserver;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.rsocket.annotation.support.RSocketMessageHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Hooks;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class PongServerApplication {

    public static void main(String[] args) {
        Hooks.onErrorDropped(error -> {}); // Prevent Reactor from logging unhandled exceptions
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public RSocketMessageHandler rSocketMessageHandler() {
        return new RSocketMessageHandler(); // Registers the RSocket endpoint
    }
    
    @Component
    public static class PingHandler {
        private final AtomicInteger totalPingsReceived = new AtomicInteger();
        private final AtomicInteger totalPongsSent = new AtomicInteger();
        private final AtomicInteger checksumFailures = new AtomicInteger();

        @Value("${server.id}")
        private int serverId;

        @MessageMapping("ping") // RSocket message handler for "ping"
        public PongResponse handlePing(PingRequest request) {
            totalPingsReceived.incrementAndGet();
            String calculatedChecksum = calculateChecksum(request.payload());

            if (!calculatedChecksum.equals(request.checksum())) {
                checksumFailures.incrementAndGet();
                throw new IllegalArgumentException("Checksum mismatch");
            }

            totalPongsSent.incrementAndGet();
            return new PongResponse("pong-server-" + serverId, request.payload(), calculatedChecksum, System.currentTimeMillis());
        }

        private String calculateChecksum(String payload) {
            return Integer.toHexString(payload.hashCode());
        }

        public Map<String, Integer> getMetrics() {
            Map<String, Integer> metrics = new HashMap<>();
            metrics.put("totalPingsReceived", totalPingsReceived.get());
            metrics.put("totalPongsSent", totalPongsSent.get());
            metrics.put("checksumFailures", checksumFailures.get());
            return metrics;
        }
    }

    @RestController
    public static class PongHealthController {
        private final PingHandler pingHandler;

        public PongHealthController(PingHandler pingHandler) {
            this.pingHandler = pingHandler;
        }

        @GetMapping("/health")
        public Map<String, Integer> getHealth() {
            return pingHandler.getMetrics();
        }
    }

    public static record PingRequest(String nodeId, String threadId, String payload, String checksum) {}
    public static record PongResponse(String serverId, String payload, String checksum, long timestamp) {}
}
