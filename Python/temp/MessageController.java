package com.example.server;

import com.example.common.Message;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import java.time.Duration;

@Controller
public class MessageController {

    @MessageMapping("request-response")
    public Mono<Message> requestResponse(Message message) {
        // Respond with a simple message transformation
        return Mono.just(new Message("Server Response: " + message.getContent()));
    }

    @MessageMapping("fire-and-forget")
    public Mono<Void> fireAndForget(Message message) {
        // Handle the message without responding
        System.out.println("Received (Fire-and-Forget): " + message.getContent());
        return Mono.empty();
    }

    @MessageMapping("stream")
    public Flux<Message> stream(Message message) {
        // Return a stream of responses over time
        return Flux.interval(Duration.ofSeconds(1))
                   .map(index -> new Message("Stream Response " + index + ": " + message.getContent()));
    }

    @MessageMapping("channel")
    public Flux<Message> channel(Flux<Message> messages) {
        // Respond to a stream of messages with another stream
        return messages.index()
                       .map(data -> new Message("Channel Response " + data.getT1() + ": " + data.getT2().getContent()));
    }
}
