package com.example.config;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.Log;
import com.aerospike.client.policy.AuthMode;
import com.aerospike.client.policy.ClientPolicy;
import com.aerospike.client.policy.TlsPolicy;
import javax.net.ssl.SSLContext;
import java.io.IOException;
import java.io.InputStream;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.List;
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
            int port = Integer.parseInt(properties.getProperty("aerospike.port", "4333"));
            namespace = properties.getProperty("aerospike.namespace", "payments");
            setName = properties.getProperty("aerospike.set", "pacs008");
            binName = properties.getProperty("aerospike.bin", "content");
            useTLS = Boolean.parseBoolean(properties.getProperty("aerospike.tls.enabled", "false"));
            String tlsName = properties.getProperty("aerospike.tls.name", "");

            // Read authentication method (PKI or standard user/pass)
            String authMethod = properties.getProperty("aerospike.auth.method", "none");
            String user = properties.getProperty("aerospike.auth.user", "");

            // Enable Aerospike client debug logs
            Log.setCallback(new AerospikeLogCallback());
            Log.setLevel(Log.Level.DEBUG);

            System.out.println("Connecting to Aerospike with:");
            System.out.println(" - Host: " + host);
            System.out.println(" - Port: " + port);
            System.out.println(" - TLS Enabled: " + useTLS);
            System.out.println(" - TLS Name: " + tlsName);
            System.out.println(" - Authentication Mode: " + authMethod);

            // Initialize Client Policy
            ClientPolicy policy = new ClientPolicy();
            policy.failIfNotConnected = true;
            policy.timeout = 10000;  // Increase timeout
            policy.authMode = "pki".equalsIgnoreCase(authMethod) ? AuthMode.PKI : AuthMode.INTERNAL;
            policy.user = user;

            if (useTLS) {
                TlsPolicy tlsPolicy = new TlsPolicy();

                // Add recommended ciphers for better security
                String[] ciphers = {
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
                };
                tlsPolicy.ciphers = ciphers;

                policy.tlsPolicy = tlsPolicy;
                System.out.println("Aerospike TLS Security Enabled.");
                printCiphers(ciphers);
            }

            // Define host with TLS Name if TLS is enabled
            Host[] hosts;
            if (useTLS && !tlsName.isEmpty()) {
                hosts = new Host[] { new Host(host, tlsName, port) };
                System.out.println("Using TLS Name for Connection: " + tlsName);
            } else {
                hosts = new Host[] { new Host(host, port) };
            }

            try {
                client = new AerospikeClient(policy, hosts);
                System.out.println("✅ Successfully connected to Aerospike!");
            } catch (Exception e) {
                System.err.println("❌ ERROR: Unable to connect to Aerospike");
                e.printStackTrace();
            }
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

    private static void printCiphers(String[] ciphers) {
        System.out.println("Available Cipher Suites:");
        List<String> selectedCiphers = Arrays.asList(ciphers);

        try {
            String[] allCiphers = SSLContext.getDefault().getSocketFactory().getSupportedCipherSuites();
            for (String cipher : allCiphers) {
                String indicator = selectedCiphers.contains(cipher) ? "x" : " ";
                System.out.println(" [" + indicator + "] " + cipher);
            }
        } catch (NoSuchAlgorithmException e) {
            System.out.println("Failed to get default SSL context.");
        }
    }
}
