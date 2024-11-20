package com.mycompany.pongserver;

import io.netty.channel.ChannelOption;
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
import org.springframework.boot.web.context.WebServerInitializedEvent;
import org.springframework.context.annotation.Bean;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.netty.tcp.TcpServer;

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

    private final AtomicInteger totalPingsReceived = new AtomicInteger();
    private final AtomicInteger totalPongsSent = new AtomicInteger();
    private final AtomicInteger pingsReceivedPerSecond = new AtomicInteger();
    private final AtomicInteger pongsSentPerSecond = new AtomicInteger();

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }
    public void configureServer() {
        // EventLoopGroups for Boss and Worker threads
        EventLoopGroup bossGroup = new EpollEventLoopGroup(1); // 1 Boss thread
        EventLoopGroup workerGroup = new EpollEventLoopGroup(8); // 8 Worker threads

        // Create the RSocket server with Netty's TcpServer
        RSocketServer.create()
            .bindNow(TcpServerTransport.create(
                TcpServer.create()
                    .runOn(bossGroup, workerGroup)                        // Use custom EventLoopGroups
                    .option(ChannelOption.SO_BACKLOG, 65535)              // Backlog for connection queue
                    .option(ChannelOption.SO_RCVBUF, 16 * 1024 * 1024)    // Receive buffer size (16MB)
                    .option(ChannelOption.SO_SNDBUF, 16 * 1024 * 1024)    // Send buffer size (16MB)
                    .option(ChannelOption.TCP_NODELAY, true)              // Disable Nagle's algorithm
                    .option(ChannelOption.SO_KEEPALIVE, true)             // Enable TCP Keep-Alive
            ));
        
        System.out.println("Netty server started with custom configuration.");
    }    

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            EventLoopGroup bossGroup = createEventLoopGroup(bossThreads);
            EventLoopGroup workerGroup = createEventLoopGroup(workerThreads);

            System.out.printf("Starting RSocket server on port %d%n", rSocketPort);
            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server started.");
        };
    }

    private EventLoopGroup createEventLoopGroup(int threads) {
        return useEpoll ? new EpollEventLoopGroup(threads) : new NioEventLoopGroup(threads);
    }

    private Flux<Payload> handleRequestStream(Payload payload) {
        totalPingsReceived.incrementAndGet();
        pingsReceivedPerSecond.incrementAndGet();

        String receivedMessage = payload.getDataUtf8();
        System.out.printf("Received: %s%n", receivedMessage);

        String responseMessage = receivedMessage.replace("ping", "pong") + "-server-" + serverNodeId;
        System.out.printf("Responding with: %s%n", responseMessage);

        totalPongsSent.incrementAndGet();
        pongsSentPerSecond.incrementAndGet();

        return Flux.just(responseMessage).map(DefaultPayload::create);
    }

    @EventListener(WebServerInitializedEvent.class)
    public void logServerDetails(WebServerInitializedEvent event) {
        int port = event.getWebServer().getPort();
        System.out.printf("Tomcat server started on port %d%n", port);
        System.out.println("Available REST Endpoints:");
        System.out.printf("  - Summary: http://localhost:%d/summary%n", port);
        System.out.printf("  - Health: http://localhost:%d/health%n", port);
    }

    public Map<String, Object> getMetrics() {
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("totalPingsReceived", totalPingsReceived.get());
        metrics.put("totalPongsSent", totalPongsSent.get());
        metrics.put("pingsPerSecond", pingsReceivedPerSecond.get());
        metrics.put("pongsPerSecond", pongsSentPerSecond.get());
        return metrics;
    }

    @Scheduled(fixedRate = 1000) // Reset per-second counters every second
    public void resetPerSecondCounters() {
        pingsReceivedPerSecond.set(0);
        pongsSentPerSecond.set(0);
    }

    @Scheduled(fixedRateString = "${reporting.interval.ms:5000}")
    public void reportMetricsToConsole() {
        System.out.println("Metrics Report:");
        System.out.printf("  Total Pings Received: %d%n", totalPingsReceived.get());
        System.out.printf("  Total Pongs Sent: %d%n", totalPongsSent.get());
        System.out.printf("  Pings Received Per Second: %d%n", pingsReceivedPerSecond.get());
        System.out.printf("  Pongs Sent Per Second: %d%n", pongsSentPerSecond.get());
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
        return Map.of("status", "UP", "description", "Server is healthy");
    }
}
