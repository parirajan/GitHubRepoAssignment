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
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                         .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort);
            Thread.currentThread().join();
        };
    }

private Flux<Payload> handleRequestStream(Payload payload) {
    String receivedMessage = payload.getDataUtf8();
    System.out.println("Received: " + receivedMessage);

    String[] parts = receivedMessage.split("-");
    String paddingData = parts[parts.length - 2];
    long clientChecksum = Long.parseLong(parts[parts.length - 1]);

    // Calculate checksum on the server side
    long serverChecksum = calculateChecksum(paddingData);

    // Construct the response message with explicit Node ID
    String responseMessage = receivedMessage.replace("ping", "pong") +
                             "-nodeId:" + serverNodeId + "-server-" + serverChecksum;

    System.out.println("Responding with: " + responseMessage);
    return Flux.just(responseMessage).map(DefaultPayload::create);
}

private long calculateChecksum(String data) {
    CRC32 crc = new CRC32();
    crc.update(data.getBytes());
    return crc.getValue();
}

}
