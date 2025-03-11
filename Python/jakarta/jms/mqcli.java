package com.example.mq;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;
import javax.jms.JMSException;
import com.sun.net.httpserver.HttpServer;

public class MqHttpServer {
    private static JmsClient jmsClient;

    public static void main(String[] args) {
        try {
            // Determine which MQ to use (default: IBM MQ)
            String mqType = System.getProperty("mq.type", "ibmmq").toLowerCase();

            if (mqType.equals("activemq")) {
                System.out.println("Connecting to ActiveMQ...");
                jmsClient = new ActiveMqClient("tcp://localhost:61616", "TEST.QUEUE");
            } else {
                System.out.println("Connecting to IBM MQ...");
                jmsClient = new IbmMqClient("your-mq-host", 1414, "QM1", "DEV.APP.SVRCONN", "TEST.QUEUE");
            }

            HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);

            // Send Message Handler
            server.createContext("/send", exchange -> {
                if (!"POST".equals(exchange.getRequestMethod())) {
                    sendResponse(exchange, 405, "Use POST to send messages");
                    return;
                }

                byte[] requestBody = exchange.getRequestBody().readAllBytes();
                String message = new String(requestBody);
                try {
                    jmsClient.sendMessage(message);
                    sendResponse(exchange, 200, "Message Sent: " + message);
                } catch (Exception e) {  // Catch generic Exception instead of JMSException
                    sendResponse(exchange, 500, "Error sending message: " + e.getMessage());
                }
            });

            // Receive Message Handler
            server.createContext("/receive", exchange -> {
                try {
                    String response = jmsClient.receiveMessage();
                    sendResponse(exchange, 200, response);
                } catch (Exception e) {  // Catch generic Exception instead of JMSException
                    sendResponse(exchange, 500, "Error receiving message: " + e.getMessage());
                }
            });

            server.setExecutor(Executors.newFixedThreadPool(4));
            server.start();
            System.out.println("MQ HTTP Server running on port 8080...");

        } catch (Exception e) {
            System.err.println("Error starting MQ HTTP Server: " + e.getMessage());
            e.printStackTrace();
        }
    }

    // Utility method to send HTTP responses
    private static void sendResponse(com.sun.net.httpserver.HttpExchange exchange, int statusCode, String response)
            throws IOException {
        exchange.sendResponseHeaders(statusCode, response.length());
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(response.getBytes());
        }
    }
}
