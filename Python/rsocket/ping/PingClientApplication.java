package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Mono;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
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

    @Value("${ping.client.threads:5}") // Default to 5 threads if not set
    private int numThreads;

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) {
        RSocketRequester requester = requesterBuilder
                .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
                .tcp(host, port);

        // Create a scheduled thread pool to send 100 pings per second
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(numThreads);

        AtomicInteger threadIdCounter = new AtomicInteger(1);

        for (int i = 0; i < numThreads; i++) {
            int threadId = threadIdCounter.getAndIncrement();
            scheduler.scheduleAtFixedRate(() -> sendPing(requester, threadId), 0, 10, TimeUnit.MILLISECONDS);
        }
    }

    private void sendPing(RSocketRequester requester, int threadId) {
        String message = "ping-" + nodeId + "-thread-" + threadId;
        System.out.println("Sending message: " + message);

        Mono<String> response = requester.route("ping")
                .data(message)
                .retrieveMono(String.class);

        response
                .doOnError(e -> System.err.println("Client error: " + e.getMessage()))
                .subscribe(responseMessage ->
                        System.out.println("Received response: " + responseMessage)
                );
    }
}
