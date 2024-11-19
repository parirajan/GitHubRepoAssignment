package com.mycompany;

import io.rsocket.Payload;
import io.rsocket.SocketAcceptor;
import io.rsocket.core.RSocketServer;
import io.rsocket.transport.netty.server.TcpServerTransport;
import io.rsocket.util.DefaultPayload;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Flux;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    private final AtomicInteger totalPingsReceived = new AtomicInteger();
    private final AtomicInteger totalPongsSent = new AtomicInteger();
    private final AtomicInteger checksumFailures = new AtomicInteger();

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort);
            Thread.currentThread().join(); // Keep the server running
        };
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        totalPingsReceived.incrementAndGet(); // Increment total pings received

        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received: " + receivedMessage);

        // Parse the received payload
        String[] parts = receivedMessage.split(",");
        String nodeId = parts[0]; // Node ID of the client
        String threadId = parts[1]; // Thread ID from the client
        String payloadData = parts[2]; // Payload data
        String clientChecksum = parts[3]; // Checksum sent by the client

        // Calculate server checksum
        String serverChecksum = calculateChecksum(payloadData);
        boolean checksumValid = serverChecksum.equals(clientChecksum);

        if (!checksumValid) {
            checksumFailures.incrementAndGet();
            System.err.println("Checksum mismatch for nodeId: " + nodeId + ", threadId: " + threadId);
        }

        // Create pong response
        String responseMessage = String.format(
            "nodeId:%s,threadId:%s,payload:%s,checksum:%s,serverId:%s",
            nodeId, threadId, payloadData, serverChecksum, serverNodeId
        );

        System.out.println("Responding with: " + responseMessage);

        totalPongsSent.incrementAndGet(); // Increment total pongs sent

        // Send response
        return Flux.just(responseMessage).map(DefaultPayload::create);
    }

    private String calculateChecksum(String data) {
        return Integer.toHexString(data.hashCode());
    }

    public Map<String, Integer> getMetrics() {
        return Map.of(
            "totalPingsReceived", totalPingsReceived.get(),
            "totalPongsSent", totalPongsSent.get(),
            "checksumFailures", checksumFailures.get()
        );
    }
}
