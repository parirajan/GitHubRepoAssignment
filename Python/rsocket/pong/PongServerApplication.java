package com.mycompany.pongservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Mono;
import io.rsocket.RSocket;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;

@SpringBootApplication
public class PongServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public void startRSocketServer() {
        RSocketServer.create((setup, sendingSocket) ->
                Mono.just(new PongResponder()))
                .bind(TcpServerTransport.create(7000))
                .block(); // Ensure the server runs continuously
    }
}

class PongResponder extends RSocket {
    @Override
    public Mono<String> requestResponse(io.rsocket.Payload payload) {
        System.out.println("Received: " + payload.getDataUtf8());
        return Mono.just("Pong");
    }
}
