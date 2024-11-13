package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Flux;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;

import java.time.Duration;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${pong.server.node-id}")
    private String nodeId;

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            // Set up the RSocket server with requestStream handler
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                         .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort + "...");
            Thread.currentThread().join(); // Keep the server running
        };
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received: " + receivedMessage);

        // Generate a stream of responses for each incoming request
        return Flux.interval(Duration.ofMillis(100)) // Respond every 100 ms
                   .map(i -> {
                       String responseMessage = "pong-" + nodeId + "-count-" + i;
                       System.out.println("Responding with: " + responseMessage);
                       return DefaultPayload.create(responseMessage);
                   });
    }
}
