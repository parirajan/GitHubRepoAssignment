package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            RSocketServer.create(SocketAcceptor.forRequestResponse(this::handleRequest))
                    .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort + "...");
            Thread.currentThread().join(); // Keep the server running
        };
    }

    private Mono<Payload> handleRequest(Payload payload) {
        return Mono.just(payload)
                .map(p -> {
                    String receivedMessage = p.getDataUtf8();
                    System.out.println("Received: " + receivedMessage);

                    // Respond with "pong" followed by the rest of the message after "ping"
                    if (receivedMessage.toLowerCase().startsWith("ping")) {
                        String responseMessage = "pong" + receivedMessage.substring(4);
                        System.out.println("Responding with: " + responseMessage);
                        return DefaultPayload.create(responseMessage);
                    } else {
                        return DefaultPayload.create("Error: Unrecognized request");
                    }
                })
                .onErrorResume(e -> {
                    System.err.println("Error occurred: " + e.getMessage());
                    return Mono.just(DefaultPayload.create("Error: Internal server error"));
                });
    }
}
