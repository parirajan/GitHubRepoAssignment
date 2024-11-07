package com.mycompany.pongservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;
import io.rsocket.Payload;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.core.RSocketConnector;
import io.rsocket.util.DefaultPayload;
import io.rsocket.RSocket;

@SpringBootApplication
public class PongServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            // Create an RSocket server that listens on port 7000
            RSocketServer.create((setupPayload, sendingSocket) ->
                Mono.just(new PongResponder()))
                .bind(TcpServerTransport.create(7000))
                .block();

            System.out.println("RSocket server is running on port 7000...");
        };
    }

    // Custom RSocket responder class
    static class PongResponder extends RSocket {
        @Override
        public Mono<Payload> requestResponse(Payload payload) {
            String receivedMessage = payload.getDataUtf8();
            System.out.println("Received: " + receivedMessage);
            return Mono.just(DefaultPayload.create("Pong"));
        }
    }
}
