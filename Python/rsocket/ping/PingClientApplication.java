package com.mycompany.pingservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.util.MimeTypeUtils;
import reactor.core.publisher.Mono;

@SpringBootApplication
public class PingClientApplication implements CommandLineRunner {

    private final RSocketRequester.Builder requesterBuilder;

    @Value("${ping.server.host}")
    private String host;

    @Value("${ping.server.port}")
    private int port;

    public PingClientApplication(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }

    @Override
    public void run(String... args) {
        RSocketRequester requester = requesterBuilder
            .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
            .tcp(host, port);

        Mono<String> response = requester
            .route("ping")
            .data("Ping")
            .retrieveMono(String.class);

        response.subscribe(responseMessage -> System.out.println("Received: " + responseMessage));
    }
}
