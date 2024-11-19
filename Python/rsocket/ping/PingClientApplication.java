package com.mycompany.pingclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.LinkedList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.CRC32;

@SpringBootApplication
@EnableScheduling
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
    private final Random random = new Random();
    private final AtomicInteger pingCounter = new AtomicInteger(1);

    private RSocketRequester rSocketRequester;

    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }

    @Bean
    public CommandLineRunner startPingClient(RSocketRequester.Builder builder) {
        return args -> {
            this.rSocketRequester = builder
                    .tcp(serverHost, serverPort);

            for (int i = 0; i < threads; i++) {
                startSendingPings();
            }
        };
    }

    private void startSendingPings() {
        for (int i = 0; i < pingsPerSecond; i++) {
            sendPing();
        }
    }

    private void sendPing() {
        String padding = generateRandomString(paddingSize);
        long checksum = calculateChecksum(padding);
        int count = pingCounter.getAndIncrement();
        String message = "ping-node-" + clientNodeId + "-count-" + count + "-" + padding + "-" + checksum;

        addTimestamp(pingsTimestamps);

        rSocketRequester.route("ping")
                .data(message)
                .retrieveMono(String.class)
                .doOnNext(response -> {
                    System.out.println("Received Pong: " + response);
                    addTimestamp(pongsTimestamps);
                })
                .doOnError(e -> System.err.println("Error sending ping: " + e.getMessage()))
                .subscribe();
    }

    private String generateRandomString(int length) {
        return random.ints(48, 123)
                .filter(i -> (i <= 57 || i >= 65) && (i <= 90 || i >= 97))
                .limit(length)
                .collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append)
                .toString();
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
}
