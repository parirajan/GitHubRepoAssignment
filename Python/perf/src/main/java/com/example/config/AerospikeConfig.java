package com.example.config;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.policy.ClientPolicy;
import java.io.IOException;
import java.util.Properties;

public class AerospikeConfig {
    private static AerospikeClient client;
    private static String host;
    private static int port;
    private static boolean useTLS;

    static {
        loadConfig();
    }

    private static void loadConfig() {
        try {
            Properties properties = new Properties();
            properties.load(AerospikeConfig.class.getClassLoader().getResourceAsStream("application.properties"));

            host = properties.getProperty("aerospike.host", "127.0.0.1");
            port = Integer.parseInt(properties.getProperty("aerospike.port", "3000"));
            useTLS = Boolean.parseBoolean(properties.getProperty("aerospike.tls.enabled", "false"));

            ClientPolicy policy = new ClientPolicy();
            policy.failIfNotConnected = true;

            if (useTLS) {
                policy.tlsPolicy = SecurityConfig.getTlsPolicy();
            }

            client = new AerospikeClient(policy, new Host(host, port));
            System.out.println("Aerospike Client Connected: " + host + ":" + port);

        } catch (IOException e) {
            throw new RuntimeException("Failed to load Aerospike configuration", e);
        }
    }

    public static AerospikeClient getClient() {
        return client;
    }

    public static void closeClient() {
        if (client != null) {
            client.close();
        }
    }
}
