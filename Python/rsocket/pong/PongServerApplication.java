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

    // Track total counts
    private static final AtomicInteger totalPingsReceivedCounter = new AtomicInteger(0);
    private static final AtomicInteger totalPongsSentCounter = new AtomicInteger(0);

    // Track counts for the current interval
    private final AtomicInteger intervalPingsReceivedCounter = new AtomicInteger(0);
    private final AtomicInteger intervalPongsSentCounter = new AtomicInteger(0);

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                    .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort);
            startSummaryLogging();
            Thread.currentThread().join();
        };
    }

    private void startSummaryLogging() {
        Flux.interval(Duration.ofSeconds(summaryIntervalSeconds))
                .doOnNext(i -> {
                    int pingsReceived = intervalPingsReceivedCounter.getAndSet(0);
                    int pongsSent = intervalPongsSentCounter.getAndSet(0);
                    System.out.println("Summary (Last " + summaryIntervalSeconds + "s) - " +
                            "Server Node ID: " + serverNodeId +
                            " | Pings Received: " + pingsReceived +
                            ", Pongs Sent: " + pongsSent);
                })
                .subscribe();
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received: " + receivedMessage);

        totalPingsReceivedCounter.incrementAndGet();
        intervalPingsReceivedCounter.incrementAndGet();

        String[] parts = receivedMessage.split("-");
        String padding = parts[parts.length - 2];
        long clientChecksum = Long.parseLong(parts[parts.length - 1]);

        long serverChecksum = calculateChecksum(padding);

        String responseMessage = receivedMessage.replace("ping", "pong") +
                "-nodeId:" + serverNodeId + "-" + serverChecksum;

        totalPongsSentCounter.incrementAndGet();
        intervalPongsSentCounter.incrementAndGet();

        return Flux.just(DefaultPayload.create(responseMessage));
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }

    @RestController
    class HealthCheckController {

        @Value("${health.server.node-id}")
        private String healthServerNodeId;

        @GetMapping("/health")
        public String getHealthStatus() {
            int totalPingsReceived = totalPingsReceivedCounter.get();
            int totalPongsSent = totalPongsSentCounter.get();
            return "Health Status: OK | Server Node ID: " + healthServerNodeId +
                    " | Total Pings Received: " + totalPingsReceived +
                    ", Total Pongs Sent: " + totalPongsSent;
        }

        @GetMapping("/summary")
        public String getSummary() {
            int intervalPingsReceived = intervalPingsReceivedCounter.get();
            int intervalPongsSent = intervalPongsSentCounter.get();
            return "Summary (Last " + summaryIntervalSeconds + "s) - " +
                    "Server Node ID: " + healthServerNodeId +
                    " | Pings Received: " + intervalPingsReceived +
                    ", Pongs Sent: " + intervalPongsSent;
        }
    }
}
