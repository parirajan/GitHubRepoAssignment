import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;
import javax.jms.JMSException;
import com.sun.net.httpserver.HttpServer;

public class MqHttpServer {
    private static IbmMqClient mqClient;

    public static void main(String[] args) throws Exception {
        mqClient = new IbmMqClient(
                "your-mq-host", 1414, "QM1", "DEV.APP.SVRCONN",
                "TEST.QUEUE", "keystore.jks", "changeit"
        );

        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        
        // Fix: Wrap in try-catch to handle JMSException
        server.createContext("/send", exchange -> {
            String response;
            if ("POST".equals(exchange.getRequestMethod())) {
                byte[] requestBody = exchange.getRequestBody().readAllBytes();
                String message = new String(requestBody);
                try {
                    mqClient.sendMessage(message);
                    response = "Message Sent: " + message;
                    exchange.sendResponseHeaders(200, response.length());
                } catch (JMSException e) {
                    response = "Error sending message: " + e.getMessage();
                    exchange.sendResponseHeaders(500, response.length());
                }
            } else {
                response = "Use POST to send messages";
                exchange.sendResponseHeaders(405, response.length()); // 405 Method Not Allowed
            }
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });

        server.createContext("/receive", exchange -> {
            String response;
            try {
                response = mqClient.receiveMessage();
                exchange.sendResponseHeaders(200, response.length());
            } catch (JMSException e) {
                response = "Error receiving message: " + e.getMessage();
                exchange.sendResponseHeaders(500, response.length());
            }
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });

        server.setExecutor(Executors.newFixedThreadPool(4));
        server.start();
        System.out.println("MQ HTTP Server running on port 8080...");
    }
}
