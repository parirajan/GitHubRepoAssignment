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

    @Value("${ping.client.pings-per-second:10000}")
    private int pingsPerSecond;

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) {
        RSocketRequester requester = requesterBuilder
                .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
                .tcp(host, port);

        // Calculate the interval between pings in nanoseconds
        long intervalNanos = 1_000_000_000L / pingsPerSecond;

        System.out.println("Sending " + pingsPerSecond + " pings per second across " + numThreads + " threads...");

        AtomicInteger threadIdCounter = new AtomicInteger(1);

        // Create multiple threads based on the configured number of threads
        for (int i = 0; i < numThreads; i++) {
            int threadId = threadIdCounter.getAndIncrement();

            // Use Flux to send pings at the specified rate
            Flux.interval(Duration.ofNanos(intervalNanos))
                    .flatMap(i1 -> sendPing(requester, threadId))
                    .subscribe();
        }
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
