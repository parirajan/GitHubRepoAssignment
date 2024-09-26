package org.company.group;

import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import javax.net.ssl.SSLContext;

import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.ssl.SSLContextBuilder;
import org.apache.hc.core5.ssl.NoopHostnameVerifier;
import org.apache.hc.core5.ssl.TrustAllStrategy;
import org.apache.hc.core5.util.Timeout;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.client5.http.socket.ConnectionSocketFactory;
import org.apache.hc.client5.http.ssl.SSLConnectionSocketFactory;
import org.apache.hc.core5.http.io.entity.EntityUtils;

@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) throws Exception {
        // Create an SSLContext that trusts all certificates
        SSLContext sslContext = SSLContextBuilder.create()
            .loadTrustMaterial(new TrustAllStrategy())  // Trust all certificates
            .build();

        // Create the SSL connection socket factory
        SSLConnectionSocketFactory sslSocketFactory = new SSLConnectionSocketFactory(
            sslContext, NoopHostnameVerifier.INSTANCE);

        // Create the connection manager and register the SSL socket factory
        PoolingHttpClientConnectionManager connectionManager = new PoolingHttpClientConnectionManager();
        connectionManager.setDefaultSocketConfig(
            org.apache.hc.core5.http.io.SocketConfig.custom()
                .setSoTimeout(Timeout.ofSeconds(60))  // Set socket timeout
                .build()
        );
        connectionManager.setSSLSocketFactory(sslSocketFactory);

        // Create HttpClient with the connection manager
        CloseableHttpClient httpClient = HttpClients.custom()
            .setConnectionManager(connectionManager)
            .build();

        // Set up the RestTemplate using HttpClient
        HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory(httpClient);
        return builder.requestFactory(() -> factory).build();
    }
}
