import javax.net.ssl.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.security.SecureRandom;
import java.security.cert.X509Certificate;

public class HttpGetWithLoop {
    public static void main(String[] args) {
        try {
            // Base URL and port
            String baseUrl = "https://example"; // The base part of the URL
            int port = 8080; // Replace with the port number
            String jsonQuery = "{\"request\": \"ping\"}"; // Raw JSON query string

            // Loop through example1 to example6
            for (int i = 1; i <= 6; i++) {
                // Construct the URL dynamically for each example (example1, example2, ..., example6)
                String currentUrl = baseUrl + i; // Concatenate to create "example1", "example2", etc.

                // Encode the JSON query parameter
                String encodedJsonQuery = URLEncoder.encode(jsonQuery, "UTF-8");

                // Full URL with port and encoded JSON query
                String fullUrl = currentUrl + ":" + port + "/?" + encodedJsonQuery;

                // Print the encoded full URL
                System.out.println("Encoded Full URL: " + fullUrl);

                // Create URL object
                URL url = new URL(fullUrl);

                // Disable SSL certificate verification
                disableSSLCertificateChecking();

                // Open connection
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();

                // Set request method to GET
                connection.setRequestMethod("GET");

                // Get response code
                int responseCode = connection.getResponseCode();
                System.out.println("Response Code for " + currentUrl + ": " + responseCode);

                // Read response
                BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                String inputLine;
                StringBuilder content = new StringBuilder();
                while ((inputLine = in.readLine()) != null) {
                    content.append(inputLine);
                }

                // Close the streams
                in.close();

                // Print the response content
                System.out.println("Response for " + currentUrl + ": " + content.toString());
                System.out.println("------------------------------------");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Method to disable SSL certificate checking
    private static void disableSSLCertificateChecking() {
        try {
            TrustManager[] trustAllCerts = new TrustManager[]{
                new X509TrustManager() {
                    public X509Certificate[] getAcceptedIssuers() {
                        return null;
                    }

                    public void checkClientTrusted(X509Certificate[] certs, String authType) {
                    }

                    public void checkServerTrusted(X509Certificate[] certs, String authType) {
                    }
                }
            };

            SSLContext sc = SSLContext.getInstance("TLS");
            sc.init(null, trustAllCerts, new SecureRandom());
            HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());

            // Create all-trusting host name verifier
            HostnameVerifier allHostsValid = (hostname, session) -> true;

            // Set the default hostname verifier
            HttpsURLConnection.setDefaultHostnameVerifier(allHostsValid);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
