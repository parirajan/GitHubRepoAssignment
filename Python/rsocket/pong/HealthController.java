package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class HealthCheckServer {

    public static void main(String[] args) {
        SpringApplication.run(HealthCheckServer.class, args);
    }
}

@RestController
class HealthCheckController {

    private final AtomicInteger pingsReceivedCounter;
    private final AtomicInteger pongsSentCounter;
    private final String serverNodeId;

    public HealthCheckController(
            PongServerApplication pongServerApplication,
            @Value("${health.server.node-id}") String serverNodeId) {
        this.pingsReceivedCounter = pongServerApplication.pingsReceivedCounter;
        this.pongsSentCounter = pongServerApplication.pongsSentCounter;
        this.serverNodeId = serverNodeId;
    }

    @GetMapping("/health")
    public String getHealthStatus() {
        int pingsReceived = pingsReceivedCounter.get();
        int pongsSent = pongsSentCounter.get();
        return "Health Status: OK | Server Node ID: " + serverNodeId +
                " | Pings Received: " + pingsReceived +
                ", Pongs Sent: " + pongsSent;
    }
}
