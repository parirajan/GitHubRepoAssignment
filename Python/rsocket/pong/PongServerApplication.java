package com.mycompany.pongservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Mono;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;

@SpringBootApplication
public class PongServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public RSocketServer rSocketServer() {
        return RSocketServer.create()
            .bindNow(TcpServerTransport.create(7000)); // Binds the server to port 7000
    }
}

@Controller
class PongController {

    @MessageMapping("ping")
    public Mono<String> respondToPing(String message) {
        System.out.println("Received: " + message);
        return Mono.just("Pong");
    }
}
