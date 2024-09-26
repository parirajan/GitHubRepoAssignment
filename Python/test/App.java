package com.example;

import org.apache.hc.client5.http.async.methods.SimpleHttpRequest;
import org.apache.hc.client5.http.async.methods.SimpleHttpRequests;
import org.apache.hc.client5.http.impl.async.CloseableHttpAsyncClient;
import org.apache.hc.client5.http.impl.async.HttpAsyncClients;
import org.apache.hc.core5.ssl.SSLContextBuilder;
import org.apache.hc.core5.ssl.NoopHostnameVerifier;
import org.apache.hc.core5.ssl.TrustAllStrategy;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.HttpResponse;

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

            // Create HttpClient that uses the custom SSLContext and disables hostname verification
            CloseableHttpAsyncClient httpClient = HttpAsyncClients.custom()
                .setSSLContext(sslContext)
                .setHostnameVerifier(NoopHostnameVerifier.INSTANCE)  // Disable hostname verification
                .build();

            // Start the HttpClient
            httpClient.start();

            // Create a GET request using the async API
            SimpleHttpRequest request = SimpleHttpRequests.get(fullUrl);

            // Execute the request asynchronously and handle the response
            Future<HttpResponse> futureResponse = httpClient.execute(request, null);

            // Wait for the response and process it
            HttpResponse response = futureResponse.get();
            String responseBody = EntityUtils.toString(response.getEntity());
            System.out.println("Response: " + responseBody);

            // Shutdown the client
            httpClient.close();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
