package com.example.client;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Bin;
import com.aerospike.client.Key;
import com.aerospike.client.Value;
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
                    System.err.println("Error while pushing message:");
                    e.printStackTrace();
                }
            });
        }
    }

    private void storeMessage(Pacs008Message message) {
        try {
            // Debugging logs before serialization
            System.out.println("Message Before Serialization: " + message);

            // Ensure messageId is valid and not null
            if (message.getMessageId() == null || message.getMessageId().isEmpty()) {
                System.err.println("Error: messageId is null or empty!");
                return;
            }

            // Ensure all other required fields are valid
            if (message.getCreationDate() == null || message.getCreationDate().isEmpty()) {
                System.err.println("Error: creationDate is null or empty!");
                return;
            }
            if (message.getInstructionId() == null || message.getInstructionId().isEmpty()) {
                System.err.println("Error: instructionId is null or empty!");
                return;
            }
            if (message.getEndToEndId() == null || message.getEndToEndId().isEmpty()) {
                System.err.println("Error: endToEndId is null or empty!");
                return;
            }
            if (message.getCurrency() == null || message.getCurrency().isEmpty()) {
                System.err.println("Error: currency is null or empty!");
                return;
            }
            if (message.getInstructingAgent() == null || message.getInstructingAgent().isEmpty()) {
                System.err.println("Error: instructingAgent is null or empty!");
                return;
            }
            if (message.getInstructedAgent() == null || message.getInstructedAgent().isEmpty()) {
                System.err.println("Error: instructedAgent is null or empty!");
                return;
            }
            if (message.getDebtorName() == null || message.getDebtorName().isEmpty()) {
                System.err.println("Error: debtorName is null or empty!");
                return;
            }
            if (message.getCreditorName() == null || message.getCreditorName().isEmpty()) {
                System.err.println("Error: creditorName is null or empty!");
                return;
            }

            // Fix Key constructor issue (Ensure key value is properly converted)
            Key key = new Key(NAMESPACE, SET_NAME, Value.get(message.getMessageId()));

            // Serialize message to Avro format
            byte[] serializedData = AvroUtils.serializeToAvro(message);
            Bin binContent = new Bin(BIN_NAME, serializedData);

            // Define Write Policy
            WritePolicy writePolicy = new WritePolicy();
            writePolicy.sendKey = true; // Ensure key is stored with the record

            // Store in Aerospike
            client.put(writePolicy, key, binContent);
            System.out.println("Stored Message ID: " + message.getMessageId());

        } catch (Exception e) {
            System.err.println("Failed to store message: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public void shutdown() {
        try {
            executor.shutdown();
            if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                System.err.println("Executor did not terminate in the allotted time.");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        int threadPoolSize = 10;
        int messageCount = 10000;

        System.out.println("Using Aerospike Client from AerospikeConfig");
        System.out.println("Namespace: " + NAMESPACE + ", Set: " + SET_NAME + ", Bin: " + BIN_NAME);

        Pacs008AerospikeClient client = new Pacs008AerospikeClient(threadPoolSize);
        client.pushMessages(messageCount);
        client.shutdown();
    }
}
