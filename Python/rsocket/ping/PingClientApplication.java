package com.mycompany.pingclient;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;
import io.rsocket.core.RSocketConnector;
import io.rsocket.transport.netty.client.TcpClientTransport;
import io.rsocket.Payload;
import io.rsocket.util.DefaultPayload;

import java.time.Duration;
import java.util.Random;
import java.util.zip.CRC32;

@SpringBootApplication
public class PingClientApplication {

    @Value("${ping.server.host}")
    private String serverHost;

    @Value("${ping.server.port}")
    private int serverPort;

    @Value("${ping.client.threads:4}")
    private int threads;

    @Value("${ping.client.pings-per-second:100}")
    private int pingsPerSecond;

    @Value("${ping.padding-size:20}")
    private int paddingSize;

    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }

    @Bean
    public CommandLineRunner startPingClient() {
        return args -> {
            RSocketConnector.create()
                    .connect(TcpClientTransport.create(serverHost, serverPort))
                    .doOnNext(rSocket -> {
                        for (int i = 0; i < threads; i++) {
                            sendPings(rSocket);
                        }
                    })
                    .subscribe();
        };
    }

    private void sendPings(io.rsocket.RSocket rSocket) {
        Flux.interval(Duration.ofMillis(1000 / pingsPerSecond))
                .flatMap(i -> {
                    String padding = generateRandomPadding();
                    long checksum = calculateChecksum(padding);
                    String message = "ping-node-thread-" + padding + "-" + checksum;
                    return rSocket.requestStream(DefaultPayload.create(message))
                            .doOnNext(response -> {
                                System.out.println("Received: " + response.getDataUtf8());
                            })
                            .onErrorResume(e -> {
                                System.err.println("Error: " + e.getMessage());
                                return Mono.empty();
                            });
                })
                .subscribeOn(Schedulers.boundedElastic())
                .subscribe();
    }

    private String generateRandomPadding() {
        Random random = new Random();
        return random.ints(48, 122)
                .limit(paddingSize)
                .collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append)
                .toString();
    }

    private long calculateChecksum(String data) {
        CRC32 crc = new CRC32();
        crc.update(data.getBytes());
        return crc.getValue();
    }
}
