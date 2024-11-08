package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;

@SpringBootApplication
public class PongServerApplication {

    // Inject the port value from application.yml
    @Value("${pong.server.port}")
    private int port;

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            // Create the RSocket server using the injected port value
            RSocketServer.create(SocketAcceptor.forRequestResponse(payload -> {
                String receivedMessage = payload.getDataUtf8();
                System.out.println("Received: " + receivedMessage);
                return Mono.just(DefaultPayload.create("Pong"));
            }))
            .bindNow(TcpServerTransport.create(port));

            System.out.println("RSocket server is running on port " + port + "...");
            Thread.currentThread().join(); // Keep the server running
        };
    }
}
