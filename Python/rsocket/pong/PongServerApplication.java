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
import reactor.core.publisher.Flux;

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

    public static void main(String[] args) {
        SpringApplication.run(PongServerApplication.class, args);
    }

    @Bean
    public CommandLineRunner startRSocketServer() {
        return args -> {
            EventLoopGroup bossGroup = createEventLoopGroup(bossThreads);
            EventLoopGroup workerGroup = createEventLoopGroup(workerThreads);

            // Report Netty configuration
            System.out.printf("Netty Configurations:%n");
            System.out.printf("  Boss Threads: %d%n", bossThreads);
            System.out.printf("  Worker Threads: %d%n", workerThreads);
            System.out.printf("  Using Epoll: %b%n", useEpoll);

            RSocketServer.create(SocketAcceptor.forRequestStream(this::handleRequestStream))
                .bindNow(TcpServerTransport.create(rSocketPort));

            System.out.println("RSocket server is running on port " + rSocketPort);
            Thread.currentThread().join(); // Keep the server running
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
        System.out.println("Received: " + receivedMessage);

        String responseMessage = receivedMessage.replace("ping", "pong") + "-server-" + serverNodeId;

        System.out.println("Responding with: " + responseMessage);

        totalPongsSent.incrementAndGet();

        return Flux.just(responseMessage).map(DefaultPayload::create);
    }

    public Map<String, Integer> getMetrics() {
        return Map.of(
            "totalPingsReceived", totalPingsReceived.get(),
            "totalPongsSent", totalPongsSent.get()
        );
    }

    // Periodic Reporting
    @Scheduled(fixedRateString = "${reporting.interval.ms:5000}")
    public void reportMetrics() {
        System.out.println("Metrics Report:");
        System.out.printf("  Total Pings Received: %d%n", totalPingsReceived.get());
        System.out.printf("  Total Pongs Sent: %d%n", totalPongsSent.get());
    }
}
