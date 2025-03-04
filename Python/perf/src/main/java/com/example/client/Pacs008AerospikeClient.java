package com.example.client;

import com.aerospike.client.*;
import com.aerospike.client.policy.*;
import com.example.avro.Pacs008Message;
import com.example.model.Pacs008Generator;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class Pacs008AerospikeClient {
    private final AerospikeClient client;
    private final ExecutorService executor;
    private static String NAMESPACE;
    private static String SET_NAME;

    public Pacs008AerospikeClient(String host, int port, int threadPoolSize) {
        ClientPolicy policy = new ClientPolicy();
        policy.failIfNotConnected = true;

        this.client = new AerospikeClient(policy, host, port);
        this.executor = Executors.newFixedThreadPool(threadPoolSize);
    }

    public void pushMessages(int messageCount) {
        for (int i = 0; i < messageCount; i++) {
            executor.submit(() -> {
                try {
                    Pacs008Message message = Pacs008Generator.generate();
                    storeMessage(message);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
    }

    private void storeMessage(Pacs008Message message) {
        Key key = new Key(NAMESPACE, SET_NAME, message.getMessageId());
        Bin binContent = new Bin("content", AvroUtils.serializeToAvro(message));

        WritePolicy writePolicy = new WritePolicy();
        writePolicy.commitLevel = CommitLevel.COMMIT_ALL;

        client.put(writePolicy, key, binContent);
        System.out.println("Stored Message ID: " + message.getMessageId());
    }

    public void shutdown() {
        try {
            executor.shutdown();
            if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                System.err.println("Executor did not terminate in the allotted time.");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            client.close();
        }
    }

    private static Properties loadProperties() {
        Properties properties = new Properties();
        try (InputStream input = Pacs008AerospikeClient.class.getClassLoader().getResourceAsStream("application.properties")) {
            if (input == null) {
                throw new RuntimeException("Configuration file application.properties not found");
            }
            properties.load(input);
        } catch (IOException ex) {
            throw new RuntimeException("Error loading application.properties", ex);
        }
        return properties;
    }

    public static void main(String[] args) {
        Properties properties = loadProperties();

        String aerospikeHost = properties.getProperty("aerospike.host", "127.0.0.1");
        int aerospikePort = Integer.parseInt(properties.getProperty("aerospike.port", "3000"));
        NAMESPACE = properties.getProperty("aerospike.namespace", "payments");
        SET_NAME = properties.getProperty("aerospike.set", "pacs008");
        int threadPoolSize = Integer.parseInt(properties.getProperty("aerospike.threadPoolSize", "10"));
        int messageCount = Integer.parseInt(properties.getProperty("aerospike.messageCount", "10000"));

        System.out.println("Connecting to Aerospike at " + aerospikeHost + ":" + aerospikePort);
        System.out.println("Using namespace: " + NAMESPACE + ", set: " + SET_NAME);
        System.out.println("Thread Pool Size: " + threadPoolSize + ", Message Count: " + messageCount);

        Pacs008AerospikeClient client = new Pacs008AerospikeClient(aerospikeHost, aerospikePort, threadPoolSize);
        client.pushMessages(messageCount);
        client.shutdown();
    }
}
