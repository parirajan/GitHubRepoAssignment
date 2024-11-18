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

import java.util.zip.CRC32;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            DisposableServer server = RSocketServer.create(
                    SocketAcceptor.forRequestStream(this::handleRequestStream)
            ).bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server running on port " + rSocketPort);

            // Keep the server running
            server.onDispose().block();
        };
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received Ping: " + receivedMessage);

        // Generate a pong response with checksum
        String responseMessage = receivedMessage.replace("ping", "pong");
        return Flux.just(DefaultPayload.create(responseMessage));
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }
}
