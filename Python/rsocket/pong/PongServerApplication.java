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
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

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
    public CommandLineRunner startRSocketServer(PongHandler pongHandler) {
        return args -> {
            RSocketServer.create(SocketAcceptor.forRequestStream(pongHandler::handleRequestStream))
                .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort);
            Thread.currentThread().join(); // Keep the server running
        };
    }
}

@Component
class PongHandler {
    private final AtomicInteger totalPingsReceived = new AtomicInteger(0);
    private final AtomicInteger totalResponsesSent = new AtomicInteger(0);
    private final ConcurrentHashMap<Long, Integer> recentActivity = new ConcurrentHashMap<>();

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    public Flux<Payload> handleRequestStream(Payload payload) {
        // Increment pings received counter
        totalPingsReceived.incrementAndGet();
        recordActivity();

        // Read and process the payload
        String receivedMessage = payload.getDataUtf8();
        System.out.println("Received: " + receivedMessage);

        // Append the server ID to the response message
        String responseMessage = receivedMessage.replace("ping", "pong") + "-server-" + serverNodeId;

        System.out.println("Responding with: " + responseMessage);

        // Increment responses sent counter
        totalResponsesSent.incrementAndGet();

        // Respond with the modified message
        return Flux.just(responseMessage).map(DefaultPayload::create);
    }

    private void recordActivity() {
        long currentMinute = Instant.now().getEpochSecond() / 60;
        recentActivity.merge(currentMinute, 1, Integer::sum);
    }

    public int getTotalPingsReceived() {
        return totalPingsReceived.get();
    }

    public int getTotalResponsesSent() {
        return totalResponsesSent.get();
    }

    public Map<Long, Integer> getRecentActivity() {
        return recentActivity;
    }
}

@RestController
class MetricsController {
    private final PongHandler pongHandler;

    public MetricsController(PongHandler pongHandler) {
        this.pongHandler = pongHandler;
    }

    @GetMapping("/health")
    public Map<String, Integer> getHealth() {
        return Map.of(
            "totalPingsReceived", pongHandler.getTotalPingsReceived(),
            "totalResponsesSent", pongHandler.getTotalResponsesSent()
        );
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        int totalActivityInLastMinute = pongHandler.getRecentActivity().values().stream()
            .mapToInt(Integer::intValue)
            .sum();

        return Map.of(
            "totalActivityInLastMinute", totalActivityInLastMinute,
            "recentActivity", pongHandler.getRecentActivity()
        );
    }
}
