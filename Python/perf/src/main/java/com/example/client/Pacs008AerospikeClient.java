package com.example.client;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Bin;
import com.aerospike.client.Key;
import com.aerospike.client.Value;
import com.aerospike.client.policy.CommitLevel;
import com.aerospike.client.policy.RecordExistsAction;
import com.aerospike.client.policy.WritePolicy;
import com.example.avro.Pacs008Message;
import com.example.config.AerospikeConfig;
import com.example.model.Pacs008Generator;
import com.example.utils.AvroUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class Pacs008AerospikeClient {
    private static final Logger logger = LogManager.getLogger(Pacs008AerospikeClient.class);
    private final AerospikeClient client;
    private final ExecutorService executor;
    private static final String NAMESPACE;
    private static final String SET_NAME;
    private static final String BIN_NAME;
    private static final int THREAD_POOL_SIZE;
    private static final int MESSAGE_COUNT;
    private static final int TARGET_MPS;

    static {
        Properties properties = new Properties();
        try (InputStream input = Pacs008AerospikeClient.class.getClassLoader().getResourceAsStream("application.properties")) {
            if (input == null) {
                throw new RuntimeException("Configuration file application.properties not found");
            }
            properties.load(input);
        } catch (IOException ex) {
            throw new RuntimeException("Error loading application.properties", ex);
        }

        // Load configuration values
        NAMESPACE = properties.getProperty("aerospike.namespace", "payments");
        SET_NAME = properties.getProperty("aerospike.set", "pacs008");

        // Ensure bin name is ≤ 15 characters
        String binFromConfig = properties.getProperty("aerospike.bin", "content");
        BIN_NAME = (binFromConfig.length() > 15) ? binFromConfig.substring(0, 15) : binFromConfig;

        THREAD_POOL_SIZE = Integer.parseInt(properties.getProperty("aerospike.threadPoolSize", "50"));
        MESSAGE_COUNT = Integer.parseInt(properties.getProperty("aerospike.messageCount", "10000"));
        TARGET_MPS = Integer.parseInt(properties.getProperty("aerospike.targetMPS", "10000"));
    }

    public Pacs008AerospikeClient() {
        this.client = AerospikeConfig.getClient();
        this.executor = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
    }

    public void pushMessages() {
        long startTime = System.nanoTime();
        int batchSize = TARGET_MPS / THREAD_POOL_SIZE;

        logger.info("Starting message push. Target: {} messages/sec", TARGET_MPS);

        for (int i = 0; i < THREAD_POOL_SIZE; i++) {
            executor.submit(() -> {
                for (int j = 0; j < batchSize; j++) {
                    try {
                        Pacs008Message message = Pacs008Generator.generate();
                        storeMessage(message);
                    } catch (Exception e) {
                        logger.error("Error while pushing message: ", e);
                    }
                }
            });
        }

        executor.shutdown();
        try {
            if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {
                logger.error("Executor did not terminate in the allotted time.");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        long endTime = System.nanoTime();
        double elapsedTimeInSec = (endTime - startTime) / 1_000_000_000.0;
        logger.info("Total Time Taken: {} seconds", elapsedTimeInSec);
        logger.info("Achieved Throughput: {} messages/sec", (MESSAGE_COUNT / elapsedTimeInSec));
    }

    private void storeMessage(Pacs008Message message) {
        try {
            Key key = new Key(NAMESPACE, SET_NAME, Value.get(message.getMessageId()));
            byte[] serializedData = AvroUtils.serializeToAvro(message);
            Bin binContent = new Bin(BIN_NAME, serializedData);

            WritePolicy writePolicy = new WritePolicy();
            writePolicy.commitLevel = CommitLevel.COMMIT_ALL;
            writePolicy.recordExistsAction = RecordExistsAction.REPLACE;
            writePolicy.sendKey = true;
            writePolicy.timeout = 10;

            client.put(writePolicy, key, binContent);
        } catch (Exception e) {
            logger.error("Failed to store message: ", e);
        }
    }

    public static void main(String[] args) {
        logger.info("Using Aerospike Client from AerospikeConfig");
        logger.info("Namespace: {}, Set: {}, Bin: {}", NAMESPACE, SET_NAME, BIN_NAME);
        logger.info("Thread Pool Size: {}, Target MPS: {}", THREAD_POOL_SIZE, TARGET_MPS);

        Pacs008AerospikeClient client = new Pacs008AerospikeClient();
        client.pushMessages();
    }
}
