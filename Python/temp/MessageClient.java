package com.example.client;

import com.example.common.Message;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.rsocket.RSocketRequester;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import javax.annotation.PostConstruct;
import java.time.Duration;

@Component
public class MessageClient {

    private final RSocketRequester rSocketRequester;

    @Autowired
    public MessageClient(RSocketRequester.Builder requesterBuilder) {
        this.rSocketRequester = requesterBuilder
                .connectTcp("localhost", 7000)
                .block();
    }

    @PostConstruct
    private void requestResponseExample() {
        this.rSocketRequester.route("request-response")
            .data(new Message("Hello, Server! From Request-Response"))
            .retrieveMono(Message.class)
            .subscribe(response -> System.out.println("Received response: " + response.getContent()));
    }

    @PostConstruct
    private void fireAndForgetExample() {
        this.rSocketRequester.route("fire-and-forget")
            .data(new Message("Hello, Server! From Fire-and-Forget"))
            .send()
            .subscribe();
    }

    @PostConstruct
    private void requestStreamExample() {
        this.rSocketRequester.route("stream")
            .data(new Message("Hello, Server! From Stream"))
            .retrieveFlux(Message.class)
            .subscribe(response -> System.out.println("Received stream response: " + response.getContent()));
    }

    @PostConstruct
    private void channelExample() {
        Flux<Message> settingsFlux = Flux.interval(Duration.ofSeconds(1))
                                         .map(index -> new Message("Hello, Server! From Channel " + index))
                                         .take(5);

        this.rSocketRequester.route("channel")
            .data(settingsFlux, Message.class)
            .retrieveFlux(Message.class)
            .subscribe(response -> System.out.println("Received channel response: " + response.getContent()));
    }
}
