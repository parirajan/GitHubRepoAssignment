package com.example.config;

import com.aerospike.client.policy.TlsPolicy;
import java.io.FileInputStream;
import java.io.IOException;
import java.security.KeyStore;
import java.util.Properties;
import javax.net.ssl.*;

public class SecurityConfig {
    private static TlsPolicy tlsPolicy;
    private static boolean tlsEnabled;

    static {
        try {
            loadSecurityConfig();
        } catch (Exception e) {
            throw new RuntimeException("Failed to configure TLS security", e);
        }
    }

    private static void loadSecurityConfig() throws Exception {
        Properties properties = new Properties();
        try (FileInputStream input = new FileInputStream("src/main/resources/application.properties")) {
            properties.load(input);
        }

        // Read TLS settings from properties
        tlsEnabled = Boolean.parseBoolean(properties.getProperty("aerospike.tls.enabled", "false"));
        String keystorePath = properties.getProperty("aerospike.tls.keystore.path", "");
        String keystorePassword = properties.getProperty("aerospike.tls.keystore.password", "");
        String truststorePath = properties.getProperty("aerospike.tls.truststore.path", "");
        String truststorePassword = properties.getProperty("aerospike.tls.truststore.password", "");
        String keystoreType = properties.getProperty("aerospike.tls.keystore.type", "JKS"); // JKS or PKCS12
        String truststoreType = properties.getProperty("aerospike.tls.truststore.type", "JKS"); // JKS or PKCS12

        if (!tlsEnabled) {
            System.out.println("TLS is disabled, skipping TLS configuration.");
            return;
        }

        System.out.println("Configuring TLS Security...");

        KeyStore keyStore = KeyStore.getInstance(keystoreType);
        try (FileInputStream keyInput = new FileInputStream(keystorePath)) {
            keyStore.load(keyInput, keystorePassword.toCharArray());
        }

        KeyStore trustStore = KeyStore.getInstance(truststoreType);
        try (FileInputStream trustInput = new FileInputStream(truststorePath)) {
            trustStore.load(trustInput, truststorePassword.toCharArray());
        }

        KeyManagerFactory keyManagerFactory = KeyManagerFactory.getInstance("SunX509");
        keyManagerFactory.init(keyStore, keystorePassword.toCharArray());

        TrustManagerFactory trustManagerFactory = TrustManagerFactory.getInstance("SunX509");
        trustManagerFactory.init(trustStore);

        SSLContext sslContext = SSLContext.getInstance("TLS");
        sslContext.init(keyManagerFactory.getKeyManagers(), trustManagerFactory.getTrustManagers(), null);

        tlsPolicy = new TlsPolicy();
        tlsPolicy.context = sslContext;

        System.out.println("TLS Security Configured Successfully.");
    }

    public static TlsPolicy getTlsPolicy() {
        return tlsPolicy;
    }

    public static boolean isTlsEnabled() {
        return tlsEnabled;
    }
}
