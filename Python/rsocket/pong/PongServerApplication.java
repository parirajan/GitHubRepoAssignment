package com.mycompany.pongservice;

package com.mycompany.pongservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Mono;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.RSocketFactory;
import io.rsocket.Payload;
import io.rsocket.util.DefaultPayload;

@SpringBootApplication
public class PongServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            // Create an RSocket server that listens on port 7000
            RSocketServer.create((setup, sendingSocket) -> Mono.just(new PongResponder()))
                    .bindNow(TcpServerTransport.create(7000));

            System.out.println("RSocket server is running on port 7000...");
        };
    }

