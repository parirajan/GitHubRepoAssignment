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

    private final AtomicInteger totalPingsReceived = new AtomicInteger(0);
    private final AtomicInteger totalResponsesSent = new AtomicInteger(0);
    private final ConcurrentHashMap<Long, Integer> recentActivity = new ConcurrentHashMap<>();

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

    @Bean
    public CommandLineRunner exposeMetricsEndpoints() {
        return args -> {
            System.out.println("\nMetrics Endpoints Available:");
            System.out.println("Health Endpoint: http://localhost:" + (rSocketPort + 1) + "/health");
            System.out.println("Summary Endpoint: http://localhost:" + (rSocketPort + 1) + "/summary");
        };
    }

    @Bean
    public org.springframework.boot.web.embedded.netty.NettyReactiveWebServerFactory webServerFactory() {
        return new org.springframework.boot.web.embedded.netty.NettyReactiveWebServerFactory(rSocketPort + 1);
    }

    @Bean
    public org.springframework.web.reactive.function.server.RouterFunction<org.springframework.web.reactive.function.server.ServerResponse> routerFunction() {
        return org.springframework.web.reactive.function.server.RouterFunctions.route()
                .GET("/health", request -> {
                    Map<String, Object> healthMetrics = Map.of(
                            "totalPingsReceived", totalPingsReceived.get(),
                            "totalResponsesSent", totalResponsesSent.get()
                    );
                    return org.springframework.web.reactive.function.server.ServerResponse.ok().bodyValue(healthMetrics);
                })
                .GET("/summary", request -> {
                    int totalActivity = recentActivity.values().stream().mapToInt(Integer::intValue).sum();
                    Map<String, Object> summaryMetrics = Map.of(
                            "totalActivityInLastMinute", totalActivity,
                            "recentActivity", recentActivity
                    );
                    return org.springframework.web.reactive.function.server.ServerResponse.ok().bodyValue(summaryMetrics);
                })
                .build();
    }
}
