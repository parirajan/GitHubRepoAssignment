package com.mycompany.pingclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;
import io.rsocket.core.RSocketConnector;
import io.rsocket.transport.netty.client.TcpClientTransport;
import io.rsocket.Payload;
import io.rsocket.util.DefaultPayload;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.CRC32;

@SpringBootApplication
public class PingClientApplication {

    @Value("${ping.server.host}")
    private String serverHost;

    @Value("${ping.server.port}")
    private int serverPort;

    @Value("${ping.client.node-id}")
    private String clientNodeId;

    @Value("${ping.client.threads:6}")
    private int threads;

    @Value("${ping.client.pings-per-second:300}")
    private int pingsPerSecond;

    @Value("${ping.client.padding-size:100}")
    private int paddingSize;

    @Value("${ping.summary-interval-seconds:60}")
    private int summaryIntervalSeconds;

    private final List<Instant> pingsTimestamps = new LinkedList<>();
    private final List<Instant> pongsTimestamps = new LinkedList<>();
    private final ReentrantLock lock = new ReentrantLock();

    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }

    @Bean
    public CommandLineRunner startPingClient() {
        return args -> {
            RSocketConnector.create()
                    .connect(TcpClientTransport.create(serverHost, serverPort))
                    .flatMapMany(rSocket -> Flux.interval(Duration.ofMillis(1000 / (threads * pingsPerSecond)))
                            .flatMap(i -> sendPing(rSocket)))
                    .subscribeOn(Schedulers.boundedElastic())
                    .subscribe();

            Thread.currentThread().join();
        };
    }

    private Mono<Void> sendPing(io.rsocket.RSocket rSocket) {
        String padding = generatePadding();
        long checksum = calculateChecksum(padding);
        String message = "ping-node-" + clientNodeId + "-thread-" + Thread.currentThread().getId() +
                "-count-" + System.currentTimeMillis() + "-" + padding + "-" + checksum;

        addTimestamp(pingsTimestamps);

        return rSocket.requestStream(DefaultPayload.create(message))
                .doOnNext(response -> {
                    String responseMessage = response.getDataUtf8();
                    System.out.println("Received Pong: " + responseMessage);
                    addTimestamp(pongsTimestamps);
                })
                .onErrorResume(e -> {
                    System.err.println("Error sending ping: " + e.getMessage());
                    return Mono.empty();
                })
                .then();
    }

    private String generatePadding() {
        return "X".repeat(paddingSize);
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

    @RestController
    class ClientSummaryController {
        @GetMapping("/summary")
        public String getClientSummary() {
            int pingsSent = getRecentCount(pingsTimestamps);
            int pongsReceived = getRecentCount(pongsTimestamps);
            return "Client Summary (Last " + summaryIntervalSeconds + "s) - " +
                    "Node ID: " + clientNodeId +
                    " | Pings Sent: " + pingsSent +
                    ", Pongs Received: " + pongsReceived;
        }
    }
}
