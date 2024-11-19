package com.mycompany;

import io.netty.channel.EventLoopGroup;
import io.netty.channel.epoll.EpollEventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
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
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
@EnableScheduling
public class PongServerApplication {

    @Value("${pong.server.port}")
    private int rSocketPort;

    @Value("${pong.server.node-id}")
    private String serverNodeId;

    @Value("${netty.config.use-epoll:false}")
    private boolean useEpoll;

    @Value("${netty.config.boss-threads:1}")
    private int bossThreads;

    @Value("${netty.config.worker-threads:4}")
    private int workerThreads;

    @Value("${metrics.server.port}")
    private int metricsPort;

    private final AtomicInteger totalPingsReceived = new AtomicInteger();
    private final AtomicInteger totalPongsSent = new AtomicInteger();

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            EventLoopGroup bossGroup = createEventLoopGroup(bossThreads);
            EventLoopGroup workerGroup = createEventLoopGroup(workerThreads);

            System.out.printf("Starting RSocket server on port %d%n", rSocketPort);
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                .bindNow(TcpServerTransport.create(rSocketPort));

            Thread.currentThread().join(); // Keep the server running
        };
    }

    @Bean
    public CommandLineRunner logMetricsServerDetails() {
        return args -> {
            System.out.printf("Metrics server is running on port %d%n", metricsPort);
            System.out.println("Available Metrics Endpoints:");
            System.out.printf("  - Summary: http://localhost:%d/summary%n", metricsPort);
            System.out.printf("  - Health: http://localhost:%d/health%n", metricsPort);
        };
    }

    private EventLoopGroup createEventLoopGroup(int threads) {
        if (useEpoll) {
            return new EpollEventLoopGroup(threads);
        } else {
            return new NioEventLoopGroup(threads);
        }
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        totalPingsReceived.incrementAndGet();

        String receivedMessage = payload.getDataUtf8();
        System.out.printf("Received: %s%n", receivedMessage);

        String responseMessage = receivedMessage.replace("ping", "pong") + "-server-" + serverNodeId;
        System.out.printf("Responding with: %s%n", responseMessage);

        totalPongsSent.incrementAndGet();

        return Flux.just(responseMessage).map(DefaultPayload::create);
    }

    public Map<String, Object> getMetrics() {
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("totalPingsReceived", totalPingsReceived.get());
        metrics.put("totalPongsSent", totalPongsSent.get());
        metrics.put("serverNodeId", serverNodeId);
        return metrics;
    }

    public boolean isHealthy() {
        // Example health check logic; always healthy for this example
        return true;
    }

    @Scheduled(fixedRateString = "${reporting.interval.ms:5000}")
    public void reportMetricsToConsole() {
        System.out.println("Metrics Report:");
        System.out.printf("  Total Pings Received: %d%n", totalPingsReceived.get());
        System.out.printf("  Total Pongs Sent: %d%n", totalPongsSent.get());
    }
}

@RestController
class MetricsController {
    private final PongServerApplication pongServer;

    public MetricsController(PongServerApplication pongServer) {
        this.pongServer = pongServer;
    }

    @GetMapping("/summary")
    public Map<String, Object> getMetricsSummary() {
        return pongServer.getMetrics();
    }

    @GetMapping("/health")
    public Map<String, String> getHealthStatus() {
        boolean healthy = pongServer.isHealthy();
        return Map.of(
            "status", healthy ? "UP" : "DOWN",
            "description", healthy ? "Server is healthy" : "Server has issues"
        );
    }
}
