package org.company.group;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

@Service
public class ApiService {

    @Autowired
    private RestTemplate restTemplate;

    public String sendRequest() throws UnsupportedEncodingException {
        // The JSON-like query parameter
        String jsonQuery = "{\"request\":\"ping\"}";

        // URL-encode the JSON-like query parameter
        String encodedQuery = URLEncoder.encode(jsonQuery, StandardCharsets.UTF_8.toString());

        // Construct the full URL with the encoded query
        String url = "https://url:port/?" + encodedQuery;

        // Make the request and get the response
        ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

        // Return the response body
        return response.getBody();
    }
}
