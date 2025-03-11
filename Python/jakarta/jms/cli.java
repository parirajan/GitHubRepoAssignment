import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import jakarta.jms.*;

public class ActiveMqClient {
    private Connection connection;
    private Session session;
    private Queue queue;

    public ActiveMqClient(String brokerUrl, String queueName) throws JMSException {
        ActiveMQConnectionFactory factory = new ActiveMQConnectionFactory(brokerUrl);
        connection = factory.createConnection();  // No username/password required
        session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
        queue = session.createQueue(queueName);
        connection.start();
    }

    public void sendMessage(String messageText) throws JMSException {
        MessageProducer producer = session.createProducer(queue);
        TextMessage message = session.createTextMessage(messageText);
        producer.send(message);
    }

    public String receiveMessage() throws JMSException {
        MessageConsumer consumer = session.createConsumer(queue);
        Message message = consumer.receive(5000);
        return (message instanceof TextMessage) ? ((TextMessage) message).getText() : "No message received";
    }

    public void close() throws JMSException {
        connection.close();
    }
}
