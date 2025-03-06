package com.example.client;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Bin;
import com.aerospike.client.Key;
import com.aerospike.client.policy.WritePolicy;
import com.example.avro.Pacs008Message;
import com.example.config.AerospikeConfig;
import com.example.model.Pacs008Generator;
import com.example.utils.AvroUtils;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class Pacs008AerospikeClient {
    private final AerospikeClient client;
    private final ExecutorService executor;
    private static final String NAMESPACE;
    private static final String SET_NAME;
    private static final String BIN_NAME;

    static {
        // Load namespace, set, and bin properties from AerospikeConfig
        NAMESPACE = AerospikeConfig.getNamespace();
        SET_NAME = AerospikeConfig.getSetName();
        BIN_NAME = AerospikeConfig.getBinName();
    }

    public Pacs008AerospikeClient(int threadPoolSize) {
        // Use the existing Aerospike client from AerospikeConfig
        this.client = AerospikeConfig.getClient();
        this.executor = Executors.newFixedThreadPool(threadPoolSize);
    }

    public void pushMessages(int messageCount) {
        for (int i = 0; i < messageCount; i++) {
            executor.submit(() -> {
                try {
                    Pacs008Message message = Pacs008Generator.generate();
                    storeMessage(message);
                } catch (Exception e) {
                    System.err.println("❌ Error while pushing message:");
                    e.printStackTrace();
                }
            });
        }
    }

    private void storeMessage(Pacs008Message message) {
        try {
            // ✅ Debugging logs
            System.out.println("🔍 Message Before Serialization: " + message);

            if (message.getMessageId() == null) {
                System.err.println("❌ Error: messageId is null!");
                return;
            }

            Key key = new Key(NAMESPACE, SET_NAME, message.getMessageId());
            Bin binContent = new Bin(BIN_NAME, AvroUtils.serializeToAvro(message));

            WritePolicy writePolicy = new WritePolicy();
            writePolicy.sendKey = true; // ✅ Ensure key is properly stored

            client.put(writePolicy, key, binContent);
            System.out.println("✅ Stored Message ID: " + message.getMessageId());
        } catch (Exception e) {
            System.err.println("❌ Failed to store message: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public void shutdown() {
        try {
            executor.shutdown();
            if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                System.err.println("❌ Executor did not terminate in the allotted time.");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        int threadPoolSize = 10;
        int messageCount = 10000;

        System.out.println("✅ Using Aerospike Client from AerospikeConfig");
        System.out.println("✅ Namespace: " + NAMESPACE + ", Set: " + SET_NAME + ", Bin: " + BIN_NAME);

        Pacs008AerospikeClient client = new Pacs008AerospikeClient(threadPoolSize);
        client.pushMessages(messageCount);
        client.shutdown();
    }
}
