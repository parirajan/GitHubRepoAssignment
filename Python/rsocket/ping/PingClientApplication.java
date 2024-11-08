package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Mono;

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

    // Interval in milliseconds between each "Ping" request
    private static final long INTERVAL_MS = 2000;

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) throws Exception {
        RSocketRequester requester = requesterBuilder
            .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
            .tcp(host, port);

        // Loop to continuously send "Ping" requests
        while (true) {
            sendPing(requester);
            Thread.sleep(INTERVAL_MS); // Wait for the specified interval before sending the next "Ping"
        }
    }

    private void sendPing(RSocketRequester requester) {
        Mono<String> response = requester
            .route("ping")
            .data("Ping")
            .retrieveMono(String.class);

        response.subscribe(responseMessage -> 
            System.out.println("Received: " + responseMessage),
            error -> System.err.println("Error: " + error.getMessage())
        );
    }
}
