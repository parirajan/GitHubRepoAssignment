package com.example;

import org.apache.hc.client5.http.impl.async.CloseableHttpAsyncClient;
import org.apache.hc.client5.http.impl.async.HttpAsyncClients;
import org.apache.hc.core5.ssl.SSLContextBuilder;
import org.apache.hc.core5.ssl.NoopHostnameVerifier;
import org.apache.hc.core5.ssl.TrustAllStrategy;
import org.apache.hc.core5.http.nio.support.BasicResponseConsumer;
import org.apache.hc.core5.http.nio.support.ClassicRequestProducer;
import org.apache.hc.core5.http.nio.AsyncResponseConsumer;
import org.apache.hc.core5.http.HttpResponse;
import org.apache.hc.core5.io.CloseMode;

import javax.net.ssl.SSLContext;
import java.io.IOException;
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
            SSLContext sslContext = SSLContextBuilder.create()
                .loadTrustMaterial(new TrustAllStrategy())  // Trust all certificates
                .build();

            // Create HttpClient that uses the custom SSLContext and disables hostname verification
            CloseableHttpAsyncClient httpClient = HttpAsyncClients.custom()
                .setSSLContext(sslContext)
                .setHostnameVerifier(NoopHostnameVerifier.INSTANCE)  // Disable hostname verification
                .build();

            // Start the HttpClient
            httpClient.start();

            // Create a GET request
            ClassicRequestProducer requestProducer = ClassicRequestProducer.createGet(fullUrl);
            AsyncResponseConsumer<HttpResponse> responseConsumer = BasicResponseConsumer.create();

            // Execute the request asynchronously
            Future<HttpResponse> futureResponse = httpClient.execute(requestProducer, responseConsumer, null);

            // Get the response
            HttpResponse response = futureResponse.get();
            System.out.println("Response Code: " + response.getCode());

            // Shut down the client
            httpClient.close(CloseMode.GRACEFUL);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
