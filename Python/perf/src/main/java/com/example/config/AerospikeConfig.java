package com.example.config;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.Log;
import com.aerospike.client.policy.AuthMode;
import com.aerospike.client.policy.ClientPolicy;
import com.aerospike.client.policy.TlsPolicy;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import javax.net.ssl.SSLContext;
import java.io.IOException;
import java.io.InputStream;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.List;
import java.util.Properties;

public class AerospikeConfig {
    private static final Logger logger = LogManager.getLogger(AerospikeConfig.class);
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

            // Enable Aerospike debug logs
            Log.setCallback(new AerospikeLogCallback());
            Log.setLevel(Log.Level.INFO);

            logger.info("Connecting to Aerospike...");
            logger.info(" - Host: {}", host);
            logger.info(" - Port: {}", port);
            logger.info(" - TLS Enabled: {}", useTLS);
            logger.info(" - TLS Name: {}", tlsName);
            logger.info(" - Authentication Mode: {}", authMethod);

            // Initialize Client Policy
            ClientPolicy policy = new ClientPolicy();
            policy.failIfNotConnected = true;
            policy.timeout = 10000; // Increase timeout
            policy.authMode = "pki".equalsIgnoreCase(authMethod) ? AuthMode.PKI : AuthMode.INTERNAL;

            // ✅ Performance tuning
            policy.maxConnsPerNode = 500;  // Increase max connections
            policy.minConnsPerNode = 50;   // Maintain some idle connections
            policy.readPolicyDefault.totalTimeout = 5000;
            policy.writePolicyDefault.totalTimeout = 5000;
            
            // ✅ Define Read Policy
            ReadPolicy readPolicy = new ReadPolicy();
            readPolicy.totalTimeout = 5000;
            readPolicy.maxRetries = 3;  // ✅ Move maxRetries here
            readPolicy.sleepBetweenRetries = 100; // ✅ Move sleepBetweenRetries here
    
            // ✅ Define Write Policy
            WritePolicy writePolicy = new WritePolicy();
            writePolicy.totalTimeout = 5000;
            writePolicy.maxRetries = 3;  // ✅ Set retries here
            writePolicy.sleepBetweenRetries = 100; // ✅ Set retry delay
    
            // Apply policies to client
            clientPolicy.readPolicyDefault = readPolicy;
            clientPolicy.writePolicyDefault = writePolicy;

            // Apply policies to client
            clientPolicy.readPolicyDefault = readPolicy;
            clientPolicy.writePolicyDefault = writePolicy;

            if (useTLS) {
                TlsPolicy tlsPolicy = new TlsPolicy();

                // Recommended ciphers
                String[] ciphers = {
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
                };
                tlsPolicy.ciphers = ciphers;

                policy.tlsPolicy = tlsPolicy;
                logger.info("Aerospike TLS Security Enabled.");
                printCiphers(ciphers);
            }

            // ✅ Define host with TLS Name if TLS is enabled
            Host[] hosts;
            if (useTLS && !tlsName.isEmpty()) {
                hosts = new Host[] { new Host(host, tlsName, port) };
                logger.info("Using TLS Name for Connection: {}", tlsName);
            } else {
                hosts = new Host[] { new Host(host, port) };
            }

            try {
                client = new AerospikeClient(policy, hosts);
                logger.info("✅ Successfully connected to Aerospike!");
            } catch (Exception e) {
                logger.error("❌ ERROR: Unable to connect to Aerospike", e);
                throw new RuntimeException("Failed to initialize Aerospike client", e);
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
            logger.info("Aerospike client connection closed.");
        }
    }

    private static void printCiphers(String[] ciphers) {
        logger.info("Available Cipher Suites:");
        List<String> selectedCiphers = Arrays.asList(ciphers);

        try {
            String[] allCiphers = SSLContext.getDefault().getSocketFactory().getSupportedCipherSuites();
            for (String cipher : allCiphers) {
                String indicator = selectedCiphers.contains(cipher) ? "✔" : " ";
                logger.info(" [{}] {}", indicator, cipher);
            }
        } catch (NoSuchAlgorithmException e) {
            logger.warn("Failed to get default SSL context.");
        }
    }
}
