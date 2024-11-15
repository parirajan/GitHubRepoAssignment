package com.mycompany.pongservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.util.DefaultPayload;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.CRC32;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${management.server.port}")
    private int managementPort;

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    @Value("${pong.summary-interval-seconds:60}")
    private int summaryIntervalSeconds;

    private final List<Instant> pingsTimestamps = new LinkedList<>();
    private final List<Instant> pongsTimestamps = new LinkedList<>();
    private final ReentrantLock lock = new ReentrantLock();

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        String receivedMessage = payload.getDataUtf8();
        String[] parts = receivedMessage.split("-");
        String padding = parts[parts.length - 2];
        long clientChecksum = Long.parseLong(parts[parts.length - 1]);

        long serverChecksum = calculateChecksum(padding);
        String responseMessage = receivedMessage.replace("ping", "pong") + "-server-" + serverNodeId + "-" + serverChecksum;

        return Flux.just(DefaultPayload.create(responseMessage));
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }
}
