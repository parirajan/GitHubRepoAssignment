import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;
import com.sun.net.httpserver.HttpServer;

public class MqHttpServer {
    private static IbmMqClient mqClient;

    public static void main(String[] args) throws Exception {
        mqClient = new IbmMqClient(
                "your-mq-host", 1414, "QM1", "DEV.APP.SVRCONN",
                "TEST.QUEUE", "keystore.jks", "changeit"
        );

        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/send", exchange -> {
            String response;
            if ("POST".equals(exchange.getRequestMethod())) {
                byte[] requestBody = exchange.getRequestBody().readAllBytes();
                String message = new String(requestBody);
                mqClient.sendMessage(message);
                response = "Message Sent: " + message;
            } else {
                response = "Use POST to send messages";
            }
            exchange.sendResponseHeaders(200, response.length());
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });

        server.createContext("/receive", exchange -> {
            String response = mqClient.receiveMessage();
            exchange.sendResponseHeaders(200, response.length());
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });

        server.setExecutor(Executors.newFixedThreadPool(4));
        server.start();
        System.out.println("MQ HTTP Server running on port 8080...");
    }
}
