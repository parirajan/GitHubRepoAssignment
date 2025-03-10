import jakarta.jms.*;
import jakarta.naming.InitialContext;
import jakarta.naming.NamingException;
import java.util.Properties;

public class SecureJMSClient {
    public static void main(String[] args) {
        try {
            // Set system properties for SSL authentication
            System.setProperty("javax.net.ssl.keyStore", "client-keystore.jks");
            System.setProperty("javax.net.ssl.keyStorePassword", "changeit");
            System.setProperty("javax.net.ssl.trustStore", "client-truststore.jks");
            System.setProperty("javax.net.ssl.trustStorePassword", "changeit");

            // Set JNDI properties for JMS connection
            Properties props = new Properties();
            props.setProperty("java.naming.factory.initial", "org.apache.activemq.jndi.ActiveMQInitialContextFactory");
            props.setProperty("connectionFactoryNames", "ConnectionFactory");
            props.setProperty("queue.MyQueue", "jms.queue.MyQueue");
            props.setProperty("java.naming.provider.url", "ssl://localhost:61617"); // Use SSL URL

            InitialContext ctx = new InitialContext(props);

            // Lookup JMS connection factory and queue
            ConnectionFactory connectionFactory = (ConnectionFactory) ctx.lookup("ConnectionFactory");
            Queue queue = (Queue) ctx.lookup("MyQueue");

            // Create connection, session, producer, and consumer
            try (Connection connection = connectionFactory.createConnection();
                 Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE)) {

                MessageProducer producer = session.createProducer(queue);
                MessageConsumer consumer = session.createConsumer(queue);

                connection.start();

                // Send a message
                TextMessage message = session.createTextMessage("Secure Hello, JMS Jakarta!");
                producer.send(message);
                System.out.println("Sent: " + message.getText());

                // Receive a message
                Message receivedMessage = consumer.receive(5000);
                if (receivedMessage instanceof TextMessage) {
                    System.out.println("Received: " + ((TextMessage) receivedMessage).getText());
                } else {
                    System.out.println("No message received.");
                }
            }
        } catch (NamingException | JMSException e) {
            e.printStackTrace();
        }
    }
}
