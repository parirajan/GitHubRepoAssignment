package com.mycompany.pingservice;

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

    public PingClient(RSocketRequester.Builder requesterBuilder) {
        this.requesterBuilder = requesterBuilder;
    }

    @Override
    public void run(String... args) throws Exception {
        RSocketRequester requester = requesterBuilder
            .dataMimeType(MimeTypeUtils.TEXT_PLAIN)
            .tcp("localhost", 7010); // Connect through Envoy sidecar on 7010

        Mono<String> response = requester
            .route("ping")
            .data("Ping")
            .retrieveMono(String.class);

        response.subscribe(responseMessage -> System.out.println("Received: " + responseMessage));
    }
}
