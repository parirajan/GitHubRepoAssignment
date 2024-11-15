package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;

import java.time.Instant;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.CRC32;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    @Value("${pong.summary-interval-seconds:60}")
    private int summaryIntervalSeconds;

    private final List<Instant> pingsTimestamps = new LinkedList<>();
    private final List<Instant> pongsTimestamps = new LinkedList<>();
    private final ReentrantLock lock = new ReentrantLock();

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    /**
     * Method to start the RSocket server.
     */
    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                    .bindNow(TcpServerTransport.create(rSocketPort));
            System.out.println("RSocket server is running on port " + rSocketPort);
            Thread.currentThread().join();
        };
    }

    /**
     * Method to handle incoming RSocket streams.
     */
    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received Ping: " + receivedMessage);

        String[] parts = receivedMessage.split("-");
        String padding = parts[parts.length - 2];
        long clientChecksum = Long.parseLong(parts[parts.length - 1]);

        long serverChecksum = calculateChecksum(padding);
        String responseMessage = receivedMessage.replace("ping", "pong") +
                "-server-" + serverNodeId + "-checksum-" + serverChecksum;

        System.out.println("Sending Pong: " + responseMessage);
        addTimestamp(pongsTimestamps);
        return Flux.just(DefaultPayload.create(responseMessage));
    }

    /**
     * Calculates the checksum of the given data.
     */
    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }

    /**
     * Adds a timestamp to the list.
     */
    private void addTimestamp(List<Instant> timestamps) {
        lock.lock();
        try {
            timestamps.add(Instant.now());
        } finally {
            lock.unlock();
        }
    }

    /**
     * Returns the count of timestamps within the summary interval.
     */
    private int getRecentCount(List<Instant> timestamps) {
        Instant cutoffTime = Instant.now().minusSeconds(summaryIntervalSeconds);
        lock.lock();
        try {
            timestamps.removeIf(timestamp -> timestamp.isBefore(cutoffTime));
            return timestamps.size();
        } finally {
            lock.unlock();
        }
    }

    @RestController
    class HealthCheckController {
        @GetMapping("/summary")
        public String getSummary() {
            int pingsReceived = getRecentCount(pingsTimestamps);
            int pongsSent = getRecentCount(pongsTimestamps);
            return "Summary (Last " + summaryIntervalSeconds + "s) - " +
                    "Server Node ID: " + serverNodeId +
                    " | Pings Received: " + pingsReceived +
                    ", Pongs Sent: " + pongsSent;
        }

        @GetMapping("/health")
        public String getHealthStatus() {
            return "Health Status: OK | Server Node ID: " + serverNodeId;
        }
    }
}
