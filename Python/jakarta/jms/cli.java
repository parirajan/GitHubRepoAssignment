package com.example.mq;

import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import javax.jms.*;

public class ActiveMqClient implements JmsClient {
    private Connection connection;
    private Session session;
    private Queue queue;

    public ActiveMqClient(String brokerUrl, String queueName) throws JMSException {
        try {
            ActiveMQConnectionFactory factory = new ActiveMQConnectionFactory(brokerUrl);
            connection = factory.createConnection(); // No username/password required
            session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            queue = session.createQueue(queueName);
            connection.start();
            System.out.println("Connected to ActiveMQ successfully.");
        } catch (JMSException e) {
            System.err.println("Failed to connect to ActiveMQ: " + e.getMessage());
            throw e; // Re-throwing so calling code can handle it
        }
    }

    @Override
    public void sendMessage(String messageText) throws JMSException {
        try {
            MessageProducer producer = session.createProducer(queue);
            TextMessage message = session.createTextMessage(messageText);
            producer.send(message);
            System.out.println("Message sent to ActiveMQ: " + messageText);
        } catch (JMSException e) {
            System.err.println("Error sending message to ActiveMQ: " + e.getMessage());
            throw e;
        }
    }

    @Override
    public String receiveMessage() throws JMSException {
        try {
            MessageConsumer consumer = session.createConsumer(queue);
            Message message = consumer.receive(5000); // Wait up to 5 seconds for a message
            if (message instanceof TextMessage) {
                String receivedText = ((TextMessage) message).getText();
                System.out.println("Received message from ActiveMQ: " + receivedText);
                return receivedText;
            }
            return "No message received";
        } catch (JMSException e) {
            System.err.println("Error receiving message from ActiveMQ: " + e.getMessage());
            throw e;
        }
    }

    @Override
    public void close() throws JMSException {
        try {
            if (session != null) session.close();
            if (connection != null) connection.close();
            System.out.println("ActiveMQ connection closed.");
        } catch (JMSException e) {
            System.err.println("Error closing ActiveMQ connection: " + e.getMessage());
            throw e;
        }
    }
}
