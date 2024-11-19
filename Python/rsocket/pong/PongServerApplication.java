package com.example.pongserver;

import io.rsocket.transport.netty.server.TcpServerTransport;
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
import reactor.netty.DisposableServer;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class PongServerApplication {

    @Value("${server.rsocketPort}")
    private int rsocketPort;

    public static void main(String[] args) {
        Hooks.onErrorDropped(error -> {}); // Suppress Reactor's unhandled error warnings
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public DisposableServer rSocketServer(RSocketMessageHandler messageHandler) {
        // Bind the RSocket server and block the thread to keep the application running
        return io.rsocket.core.RSocketServer.create(messageHandler.responder())
                .bindNow(TcpServerTransport.create(rsocketPort));
    }

    @Bean
    public RSocketMessageHandler rSocketMessageHandler() {
        return new RSocketMessageHandler(); // Register the RSocket message handlers
    }

    @Bean
    public Runnable blockMainThread(DisposableServer disposableServer) {
        // Block the main thread to ensure the server remains active
        return () -> {
            try {
                disposableServer.onDispose().block();
            } catch (Exception e) {
                throw new RuntimeException("Error while running PongServer", e);
            }
        };
    }

    // Component for handling RSocket requests
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

    // REST Controller for Health Endpoint
    @RestController
    public static class PongHealthController {
        private final PingHandler pingHandler;

        public PongHealthController(PingHandler pingHandler) {
            this.pingHandler = pingHandler;
        }

        @GetMapping("/health") // Expose health endpoint
        public Map<String, Integer> getHealth() {
            return pingHandler.getMetrics();
        }
    }

    // Record for RSocket request data
    public static record PingRequest(String nodeId, String threadId, String payload, String checksum) {}

    // Record for RSocket response data
    public static record PongResponse(String serverId, String payload, String checksum, long timestamp) {}
}
