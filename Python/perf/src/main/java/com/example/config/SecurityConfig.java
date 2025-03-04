package com.example.config;

import com.aerospike.client.policy.TlsPolicy;
import java.io.FileInputStream;
import java.io.IOException;
import java.security.KeyStore;
import javax.net.ssl.*;

public class SecurityConfig {
    private static TlsPolicy tlsPolicy;

    static {
        try {
            loadSecurityConfig();
        } catch (Exception e) {
            throw new RuntimeException("Failed to configure TLS security", e);
        }
    }

    private static void loadSecurityConfig() throws Exception {
        String keystorePath = "src/main/resources/keystore.jks";
        String keystorePassword = "changeit";
        String truststorePath = "src/main/resources/truststore.jks";
        String truststorePassword = "changeit";

        KeyStore keyStore = KeyStore.getInstance("JKS");
        keyStore.load(new FileInputStream(keystorePath), keystorePassword.toCharArray());

        KeyStore trustStore = KeyStore.getInstance("JKS");
        trustStore.load(new FileInputStream(truststorePath), truststorePassword.toCharArray());

        KeyManagerFactory keyManagerFactory = KeyManagerFactory.getInstance("SunX509");
        keyManagerFactory.init(keyStore, keystorePassword.toCharArray());

        TrustManagerFactory trustManagerFactory = TrustManagerFactory.getInstance("SunX509");
        trustManagerFactory.init(trustStore);

        SSLContext sslContext = SSLContext.getInstance("TLS");
        sslContext.init(keyManagerFactory.getKeyManagers(), trustManagerFactory.getTrustManagers(), null);

        tlsPolicy = new TlsPolicy();
        tlsPolicy.context = sslContext;
    }

    public static TlsPolicy getTlsPolicy() {
        return tlsPolicy;
    }
}
