package com.mycompany.pongservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;
import io.rsocket.Payload;
import io.rsocket.RSocket;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;

@SpringBootApplication
public class PongServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            RSocketServer.create((setup, sendingSocket) -> Mono.just(new PongResponder()))
                         .bindNow(TcpServerTransport.create(7000));
            System.out.println("RSocket server is running on port 7000...");
            Thread.currentThread().join(); // Keep the server running
        };
    }

    // Custom RSocket responder class
    static class PongResponder extends RSocket {
        @Override
        public Mono<Payload> requestResponse(Payload payload) {
            String receivedMessage = payload.getDataUtf8();
            System.out.println("Received: " + receivedMessage);
            return Mono.just(io.rsocket.util.DefaultPayload.create("Pong"));
        }
    }
}
