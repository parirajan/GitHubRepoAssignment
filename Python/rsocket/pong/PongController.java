package com.mycompany.pongservice;

import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Mono;

@Controller
class PongController {

    @MessageMapping("ping")
    public Mono<String> respondToPing(String message) {
        System.out.println("Received: " + message);
        return Mono.just("Pong");
    }
}
