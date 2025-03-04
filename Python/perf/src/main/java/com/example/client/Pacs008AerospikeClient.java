import com.aerospike.client.*;
import com.aerospike.client.policy.*;
import com.example.avro.Pacs008Message;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class Pacs008AerospikeClient {
    private final AerospikeClient client;
    private final ExecutorService executor;

    public Pacs008AerospikeClient(String host, int port, int threadPoolSize) {
        ClientPolicy policy = new ClientPolicy();
        policy.failIfNotConnected = true;
        policy.tlsPolicy = new TlsPolicy();

        this.client = new AerospikeClient(policy, host, port);
        this.executor = Executors.newFixedThreadPool(threadPoolSize);
    }

    public void pushMessages(int messageCount) {
        for (int i = 0; i < messageCount; i++) {
            executor.submit(() -> {
                try {
                    storeMessage(Pacs008Generator.generate());
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
    }

    private void storeMessage(Pacs008Message message) {
        Key key = new Key("payments", "pacs008", message.getMessageId());
        Bin binContent = new Bin("content", AvroUtils.serializeToAvro(message));

        WritePolicy writePolicy = new WritePolicy();
        writePolicy.commitLevel = CommitLevel.COMMIT_ALL;

        client.put(writePolicy, key, binContent);
        System.out.println("Stored: " + message.getMessageId());
    }

    public void shutdown() {
        try {
            executor.shutdown();
            executor.awaitTermination(10, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        client.close();
    }

    public static void main(String[] args) {
        Pacs008AerospikeClient client = new Pacs008AerospikeClient("192.168.1.100", 3000, 10);
        client.pushMessages(10000);
        client.shutdown();
    }
}
