package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.messaging.rsocket.annotation.ConnectMapping;
import org.springframework.messaging.rsocket.annotation.MessageMapping;
import org.springframework.messaging.rsocket.annotation.RSocketController;
import reactor.core.publisher.Mono;

import java.util.zip.CRC32;

@SpringBootApplication
public class PongServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }
}

@RSocketController
class PongController {

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    @MessageMapping("ping")
    public Mono<String> handlePing(String message) {
        System.out.println("Received Ping: " + message);

        String[] parts = message.split("-");
        String padding = parts[parts.length - 2];
        long clientChecksum = Long.parseLong(parts[parts.length - 1]);

        long serverChecksum = calculateChecksum(padding);
        String response = message.replace("ping", "pong") +
                "-server-" + serverNodeId + "-checksum-" + serverChecksum;

        System.out.println("Sending Pong: " + response);
        return Mono.just(response);
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }
}
