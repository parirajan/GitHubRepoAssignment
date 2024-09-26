package com.example;

import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.HttpClients;
import org.apache.hc.client5.http.classic.CloseableHttpClient;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.ClassicHttpResponse;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class App {
    public static void main(String[] args) {
        String url = "http://url:port/?";
        String queryParam = "{\"request\": \"ping\"}";

        try {
            // URL encode the query parameter
            String encodedQuery = URLEncoder.encode(queryParam, StandardCharsets.UTF_8.toString());

            // Full URL with encoded query
            String fullUrl = url + encodedQuery;

            // Create HttpClient instance
            CloseableHttpClient httpClient = HttpClients.createDefault();

            // Create HttpGet request
            HttpGet request = new HttpGet(fullUrl);

            // Execute the request and get the response
            try (CloseableHttpResponse response = httpClient.execute(request)) {
                // Print the response
                String responseBody = EntityUtils.toString(response.getEntity());
                System.out.println("Response: " + responseBody);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
