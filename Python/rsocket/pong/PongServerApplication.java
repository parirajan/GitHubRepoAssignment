package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Flux;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.SocketAcceptor;
import io.rsocket.Payload;
import io.rsocket.util.DefaultPayload;

import java.time.Duration;
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

@Bean
public CommandLineRunner startRSocketServer() {
    return args -> {
        RSocketServer server = RSocketServer.create(
                SocketAcceptor.forRequestStream(this::handleRequestStream)
        )
        .bindNow(TcpServerTransport.create(rSocketPort));

        System.out.println("RSocket server running on port " + rSocketPort);

        // Add a shutdown hook to ensure proper cleanup
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutting down RSocket server...");
            server.dispose();
        }));

        // Keep the server running without blocking the event loop
        server.onClose().block();
    };
}


    // Handles the streaming pings from clients and continuously sends back responses
    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received Ping: " + receivedMessage);

        // Parse the incoming message to extract the checksum and padding
        String[] parts = receivedMessage.split("-");
        String padding = parts[parts.length - 2];
        long clientChecksum = Long.parseLong(parts[parts.length - 1]);

        // Calculate server-side checksum
        long serverChecksum = calculateChecksum(padding);

        // Stream a continuous response back to the client
        return Flux.interval(Duration.ofMillis(200))
                .map(i -> {
                    String responseMessage = receivedMessage.replace("ping", "pong") +
                            "-server-" + serverNodeId + "-checksum-" + serverChecksum;
                    System.out.println("Sending Pong: " + responseMessage);
                    addTimestamp(pongsTimestamps);
                    return DefaultPayload.create(responseMessage);
                });
    }

    // Calculate checksum for data integrity
    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }

    // Add a timestamp for received pings or sent pongs
    private void addTimestamp(List<Instant> timestamps) {
        lock.lock();
        try {
            timestamps.add(Instant.now());
        } finally {
            lock.unlock();
        }
    }

    // Logs summary statistics every interval defined in the configuration
    private void startSummaryLogging() {
        Flux.interval(Duration.ofSeconds(summaryIntervalSeconds))
                .doOnNext(i -> {
                    int pingsReceived = getRecentCount(pingsTimestamps);
                    int pongsSent = getRecentCount(pongsTimestamps);
                    System.out.println("Summary (Last " + summaryIntervalSeconds + "s) - " +
                            "Server Node ID: " + serverNodeId +
                            " | Pings Received: " + pingsReceived +
                            ", Pongs Sent: " + pongsSent);
                })
                .subscribe();
    }

    // Get the count of recent timestamps within the interval
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
}
