package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Mono;

import java.util.Scanner;

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

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) {
        try (Scanner scanner = new Scanner(System.in)) {
            RSocketRequester requester = requesterBuilder
                    .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
                    .tcp(host, port);

            while (true) {
                // Automatically send a message using the node ID
                String message = "ping-" + nodeId;
                sendPing(requester, message);
                Thread.sleep(2000);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void sendPing(RSocketRequester requester, String message) {
        Mono<String> response = requester
                .route("ping")
                .data(message)
                .retrieveMono(String.class);

        response
                .doOnError(e -> System.err.println("Client error: " + e.getMessage()))
                .subscribe(
                        responseMessage -> System.out.println("Received: " + responseMessage),
                        error -> System.err.println("Subscription error: " + error.getMessage())
                );
    }
}
