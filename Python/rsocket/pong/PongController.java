package com.mycompany.pongservice;

import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Mono;

@Controller
public class PongController {

    /**
     * Handles incoming "Ping" messages and responds with "Pong".
     * The @MessageMapping annotation binds this method to the "ping" route.
     */
    @MessageMapping("ping")
    public Mono<String> respondToPing(String message) {
        System.out.println("Received: " + message);
        return Mono.just("Pong");
    }
}
