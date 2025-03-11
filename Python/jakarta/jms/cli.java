package com.example.mq;

import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import javax.jms.*;
import java.io.IOException;
import java.util.Properties;

public class ActiveMqClient implements JmsClient {
    private Connection connection;
    private Session session;
    private Queue queue;

    public ActiveMqClient() throws JMSException {
        try {
            // Load properties from application.properties
            Properties properties = new Properties();
            properties.load(getClass().getClassLoader().getResourceAsStream("application.properties"));

            String brokerUrl = properties.getProperty("activemq.server.url", "tcp://localhost:61616");
            String queueName = properties.getProperty("activemq.queue.name", "TEST.QUEUE");

            System.out.println("Connecting to ActiveMQ at: " + brokerUrl);
            System.out.println("Using queue: " + queueName);

            ActiveMQConnectionFactory factory = new ActiveMQConnectionFactory(brokerUrl);
            connection = factory.createConnection();
            session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            queue = session.createQueue(queueName);
            connection.start();

            System.out.println("Connected to ActiveMQ successfully.");
        } catch (IOException e) {
            throw new RuntimeException("Failed to load application.properties", e);
        } catch (JMSException e) {
            throw new RuntimeException("Failed to connect to ActiveMQ", e);
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
            Message message = consumer.receive(5000);
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
