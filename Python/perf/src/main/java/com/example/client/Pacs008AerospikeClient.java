package com.example.client;

import com.aerospike.client.*;
import com.aerospike.client.policy.*;
import com.example.avro.Pacs008Message;
import com.example.model.Pacs008Generator;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class Pacs008AerospikeClient {
    private final AerospikeClient client;
    private final ExecutorService executor;
    private static final String NAMESPACE = "payments";
    private static final String SET_NAME = "pacs008";

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

    public static void main(String[] args) {
        String aerospikeHost = "192.168.1.100";
        int aerospikePort = 3000;
        int threadPoolSize = 10;
        int messageCount = 10000;

        Pacs008AerospikeClient client = new Pacs008AerospikeClient(aerospikeHost, aerospikePort, threadPoolSize);
        client.pushMessages(messageCount);
        client.shutdown();
    }
}
