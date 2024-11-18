package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;
import reactor.netty.DisposableServer;

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
            DisposableServer server = RSocketServer.create(
                    SocketAcceptor.forRequestStream(this::handleRequestStream)
            )
            .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server running on port " + rSocketPort);

            // Add a shutdown hook to gracefully stop the server
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("Shutting down RSocket server...");
                server.dispose();
            }));

            // Keep the server running until it's manually stopped
            server.onDispose().block();
        };
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received Ping: " + receivedMessage);

        String[] parts = receivedMessage.split("-");
        String padding = parts[parts.length - 2];
        long clientChecksum = Long.parseLong(parts[parts.length - 1]);

        long serverChecksum = calculateChecksum(padding);

        return Flux.interval(Duration.ofMillis(200))
                .map(i -> {
                    String responseMessage = receivedMessage.replace("ping", "pong") +
                            "-server-" + serverNodeId + "-checksum-" + serverChecksum;
                    System.out.println("Sending Pong: " + responseMessage);
                    addTimestamp(pongsTimestamps);
                    return DefaultPayload.create(responseMessage);
                });
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }

    private void addTimestamp(List<Instant> timestamps) {
        lock.lock();
        try {
            timestamps.add(Instant.now());
        } finally {
            lock.unlock();
        }
    }

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
