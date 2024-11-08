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

    // Load the port value from application.yml
    @Value("${pong.server.port}")
    private int port;

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            // Create the RSocket server using SocketAcceptor and the port from application.yml
            RSocketServer.create(SocketAcceptor.forRequestResponse(this::handleRequest))
                         .bindNow(TcpServerTransport.create(port));

            System.out.println("RSocket server is running on port " + port + "...");
            Thread.currentThread().join(); // Keep the server running
        };
    }

    /**
     * Method to handle request-response interactions.
     */
    private Mono<Payload> handleRequest(Payload payload) {
        try {
            String receivedMessage = payload.getDataUtf8();

            // Check if the message is "Ping"
            if ("Ping".equalsIgnoreCase(receivedMessage)) {
                System.out.println("Received valid Ping request");
                return Mono.just(DefaultPayload.create("Pong"));
            } else {
                // Handle unrecognized requests gracefully
                System.out.println("Received unknown message: " + receivedMessage);
                return Mono.just(DefaultPayload.create("Error: Unrecognized request"));
            }
        } catch (Exception e) {
            // Log any errors that occur during request processing
            System.err.println("Error while handling request: " + e.getMessage());

            // Respond with a generic error message to the client
            return Mono.just(DefaultPayload.create("Error: Internal server error"));
        }
    }
}
