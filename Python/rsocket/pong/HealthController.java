package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class HealthCheckServer {

    public static void main(String[] args) {
        SpringApplication.run(HealthCheckServer.class, args);
    }
}

@RestController
class HealthCheckController {

    @Value("${health.server.node-id}")
    private String serverNodeId;

    @GetMapping("/health")
    public String getHealthStatus() {
        int pingsReceived = PongServerApplication.pingsReceivedCounter.get();
        int pongsSent = PongServerApplication.pongsSentCounter.get();
        return "Health Status: OK | Server Node ID: " + serverNodeId +
                " | Pings Received: " + pingsReceived +
                ", Pongs Sent: " + pongsSent;
    }
}
