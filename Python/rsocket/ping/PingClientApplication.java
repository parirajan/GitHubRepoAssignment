package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class PingClientApplication {
    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }
}

@Component
class PingClient implements CommandLineRunner {

    private final RSocketRequester.Builder requesterBuilder;

    @Value("${ping.server.host}")
    private String host;

    @Value("${ping.server.port}")
    private int port;

    @Value("${ping.client.node-id}")
    private String nodeId;

    @Value("${ping.client.threads:5}")
    private int numThreads;

    @Value("${ping.client.pings-per-second:10}")
    private int pingsPerSecond;

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) {
        RSocketRequester requester = requesterBuilder
                .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
                .tcp(host, port);

        AtomicInteger threadIdCounter = new AtomicInteger(1);

        // Calculate the interval between pings per thread
        long intervalMillis = 1000L / pingsPerSecond;

        System.out.println("Sending " + pingsPerSecond + " pings per second per thread across " + numThreads + " threads...");

        // Create multiple threads to send pings
        for (int i = 0; i < numThreads; i++) {
            int threadId = threadIdCounter.getAndIncrement();
            sendPingsAtFixedRate(requester, threadId, intervalMillis);
        }

        // Keep the application running
        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private void sendPingsAtFixedRate(RSocketRequester requester, int threadId, long intervalMillis) {
        Flux.interval(Duration.ofMillis(intervalMillis))
                .flatMap(i -> sendPing(requester, threadId))
                .subscribe();
    }

    private Mono<Void> sendPing(RSocketRequester requester, int threadId) {
        String message = "ping-" + nodeId + "-thread-" + threadId;
        System.out.println("Sending message: " + message);

        return requester.route("ping")
                .data(message)
                .retrieveMono(String.class)
                .doOnNext(response -> System.out.println("Received response: " + response))
                .doOnError(e -> System.err.println("Client error: " + e.getMessage()))
                .then();
    }
}
