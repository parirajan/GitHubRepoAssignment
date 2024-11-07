package com.mycompany.pongservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Mono;

@SpringBootApplication
public class PongServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
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
