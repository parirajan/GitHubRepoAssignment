package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Flux;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.CRC32;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    @Value("${pong.summary-interval-seconds:60}")
    private int summaryIntervalSeconds;

    private final AtomicInteger pingsReceivedCounter = new AtomicInteger(0);
    private final AtomicInteger pongsSentCounter = new AtomicInteger(0);

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                    .bindNow(TcpServerTransport.create(rSocketPort));

            // Log summary of pings received and pongs sent every configured interval
            Flux.interval(Duration.ofSeconds(summaryIntervalSeconds))
                    .subscribe(i -> {
                        int pingsReceived = pingsReceivedCounter.getAndSet(0);
                        int pongsSent = pongsSentCounter.getAndSet(0);
                        System.out.println("Server Node ID: " + serverNodeId +
                                " | Pings Received: " + pingsReceived +
                                ", Pongs Sent: " + pongsSent);
                    });

            System.out.println("RSocket server running on port " + rSocketPort);
            Thread.currentThread().join();
        };
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received: " + receivedMessage);

        pingsReceivedCounter.incrementAndGet();

        // Extract client info from the message
        String[] parts = receivedMessage.split("-");
        if (parts.length < 6) {
            System.err.println("Invalid message format");
            return Flux.empty();
        }

        String clientNodeId = parts[1];
        String clientThreadId = parts[3];
        String clientCount = parts[5];
        String padding = parts[parts.length - 2];
        long clientChecksum;

        try {
            clientChecksum = Long.parseLong(parts[parts.length - 1]);
        } catch (NumberFormatException e) {
            System.err.println("Invalid checksum in message");
            return Flux.empty();
        }

        System.out.println("Client Node ID: " + clientNodeId + 
                ", Thread ID: " + clientThreadId + 
                ", Count: " + clientCount + 
                ", Client Checksum: " + clientChecksum);

        // Calculate the server-side checksum for the received padding
        long serverChecksum = calculateChecksum(padding);

        // Construct the response message
        String responseMessage = receivedMessage.replace("ping", "pong") +
                "-nodeId:" + serverNodeId + "-" + serverChecksum;

        pongsSentCounter.incrementAndGet();

        return Flux.just(DefaultPayload.create(responseMessage));
    }

    // Method to calculate the checksum using CRC32
    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }
}
