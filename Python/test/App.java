package com.example;

import org.apache.hc.client5.http.async.methods.SimpleHttpRequest;
import org.apache.hc.client5.http.async.methods.SimpleHttpRequests;
import org.apache.hc.client5.http.impl.async.CloseableHttpAsyncClient;
import org.apache.hc.client5.http.impl.async.HttpAsyncClients;
import org.apache.hc.client5.http.impl.nio.PoolingAsyncClientConnectionManager;
import org.apache.hc.core5.ssl.SSLContextBuilder;
import org.apache.hc.core5.ssl.NoopHostnameVerifier;
import org.apache.hc.core5.ssl.TrustAllStrategy;
import org.apache.hc.core5.ssl.SSLConnectionSocketFactory;
import org.apache.hc.core5.http.nio.support.AsyncRequestBuilder;
import org.apache.hc.core5.http.nio.AsyncEntityProducer;
import org.apache.hc.core5.http.nio.support.BasicResponseConsumer;
import org.apache.hc.core5.http.nio.AsyncResponseConsumer;
import org.apache.hc.core5.http.nio.entity.StringAsyncEntityConsumer;
import org.apache.hc.core5.http.HttpResponse;
import org.apache.hc.core5.http.ContentType;

import javax.net.ssl.SSLContext;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Future;

public class App {
    public static void main(String[] args) {
        String url = "https://url:port/?";
        String queryParam = "{\"request\": \"ping\"}";

        try {
            // URL encode the query parameter
            String encodedQuery = URLEncoder.encode(queryParam, StandardCharsets.UTF_8.toString());

            // Full URL with encoded query
            String fullUrl = url + encodedQuery;

            // Create an SSLContext that trusts all certificates
            SSLContext sslContext = new SSLContextBuilder()
                .loadTrustMaterial(new TrustAllStrategy())  // Trust all certificates
                .build();

            // Create the SSLConnectionSocketFactory
            SSLConnectionSocketFactory sslSocketFactory = new SSLConnectionSocketFactory(sslContext, NoopHostnameVerifier.INSTANCE);

            // Create a connection manager with the SSL factory
            PoolingAsyncClientConnectionManager connectionManager = PoolingAsyncClientConnectionManager.builder()
                .setTlsStrategy(sslSocketFactory.getTlsStrategy())
                .build();

            // Create HttpClient that uses the custom connection manager
            CloseableHttpAsyncClient httpClient = HttpAsyncClients.custom()
                .setConnectionManager(connectionManager)
                .build();

            // Start the HttpClient
            httpClient.start();

            // Create a GET request using the async API
            SimpleHttpRequest request = SimpleHttpRequests.get(fullUrl);

            // Execute the request asynchronously and handle the response
            Future<Void> futureResponse = httpClient.execute(
                request,
                new StringAsyncEntityConsumer(),
                (response, entity) -> {
                    // Process the response
                    System.out.println("Response Code: " + response.getCode());
                    System.out.println("Response Body: " + entity);
                });

            // Wait for the response
            futureResponse.get();

            // Shutdown the client
            httpClient.close();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
