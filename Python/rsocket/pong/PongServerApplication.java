package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Flux;
import reactor.netty.DisposableServer;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.SocketAcceptor;
import io.rsocket.Payload;
import io.rsocket.util.DefaultPayload;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            // Start the RSocket server using DisposableServer
            DisposableServer server = RSocketServer.create()
                    .acceptor(SocketAcceptor.forRequestStream(this::handleRequestStream))
                    .bind(TcpServerTransport.create(rSocketPort))
                    .block();

            if (server != null) {
                System.out.println("RSocket server is running on port " + rSocketPort);
                server.onDispose().block();
            } else {
                System.err.println("Failed to start RSocket server!");
            }
        };
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received Ping: " + receivedMessage);

        String responseMessage = receivedMessage.replace("ping", "pong");
        return Flux.just(DefaultPayload.create(responseMessage));
    }
}
