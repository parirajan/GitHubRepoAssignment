package com.example.config;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.policy.ClientPolicy;
import com.aerospike.client.policy.TlsPolicy;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public class AerospikeConfig {
    private static AerospikeClient client;
    private static String namespace;
    private static String setName;
    private static String binName;
    private static boolean useTLS;

    static {
        loadConfig();
    }

    private static void loadConfig() {
        Properties properties = new Properties();
        try (InputStream input = AerospikeConfig.class.getClassLoader().getResourceAsStream("application.properties")) {
            if (input == null) {
                throw new RuntimeException("Configuration file application.properties not found");
            }
            properties.load(input);

            String host = properties.getProperty("aerospike.host", "127.0.0.1");
            int port = Integer.parseInt(properties.getProperty("aerospike.port", "3000"));
            namespace = properties.getProperty("aerospike.namespace", "payments");
            setName = properties.getProperty("aerospike.set", "pacs008");
            binName = properties.getProperty("aerospike.bin", "content");
            useTLS = Boolean.parseBoolean(properties.getProperty("aerospike.tls.enabled", "false"));

            // Read authentication method (PKI or standard user/pass)
            String authMethod = properties.getProperty("aerospike.auth.method", "none");
            String user = properties.getProperty("aerospike.auth.user", "");

            // Read Rack Awareness settings
            int rackId = Integer.parseInt(properties.getProperty("aerospike.rackId", "1"));
            boolean rackAware = Boolean.parseBoolean(properties.getProperty("aerospike.rackAware", "true"));

            ClientPolicy policy = new ClientPolicy();
            policy.failIfNotConnected = true;
            policy.rackAware = rackAware;
            policy.rackId = rackId;

            if ("pki".equalsIgnoreCase(authMethod) && !user.isEmpty()) {
                policy.user = user; // No password needed for PKI
                System.out.println("Using PKI Authentication for Aerospike.");
            }

            if (useTLS) {
                policy.tlsPolicy = SecurityConfig.getTlsPolicy();
                System.out.println("Aerospike TLS Security Enabled.");
            }

            client = new AerospikeClient(policy, new Host(host, port));
            System.out.println("Aerospike Client Connected to " + host + ":" + port);
            System.out.println("Rack Awareness Enabled: " + rackAware + ", Preferred Rack ID: " + rackId);
        } catch (IOException e) {
            throw new RuntimeException("Failed to load Aerospike configuration", e);
        }
    }

    public static AerospikeClient getClient() {
        return client;
    }

    public static String getNamespace() {
        return namespace;
    }

    public static String getSetName() {
        return setName;
    }

    public static String getBinName() {
        return binName;
    }

    public static void closeClient() {
        if (client != null) {
            client.close();
        }
    }
}
