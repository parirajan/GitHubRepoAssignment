package com.example.mq;

import com.ibm.mq.jms.MQQueueConnectionFactory;
import com.ibm.msg.client.wmq.common.CommonConstants;
import javax.jms.*;

public class IbmMqClient implements JmsClient {
    private Connection connection;
    private Session session;
    private Queue queue;

    public IbmMqClient(String host, int port, String queueManager, String channel, String queueName) throws JMSException {
        try {
            MQQueueConnectionFactory factory = new MQQueueConnectionFactory();
            factory.setHostName(host);
            factory.setPort(port);
            factory.setQueueManager(queueManager);
            factory.setChannel(channel);
            factory.setTransportType(CommonConstants.WMQ_CM_CLIENT);

            connection = factory.createConnection(); // No username/password needed
            session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
            queue = session.createQueue(queueName);
            connection.start();
            System.out.println("Connected to IBM MQ successfully.");
        } catch (JMSException e) {
            System.err.println("Failed to connect to IBM MQ: " + e.getMessage());
            throw e; // Re-throwing so calling code can handle it
        }
    }

    @Override
    public void sendMessage(String messageText) throws JMSException {
        try {
            MessageProducer producer = session.createProducer(queue);
            TextMessage message = session.createTextMessage(messageText);
            producer.send(message);
            System.out.println("Message sent to IBM MQ: " + messageText);
        } catch (JMSException e) {
            System.err.println("Error sending message to IBM MQ: " + e.getMessage());
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
                System.out.println("Received message from IBM MQ: " + receivedText);
                return receivedText;
            }
            return "No message received";
        } catch (JMSException e) {
            System.err.println("Error receiving message from IBM MQ: " + e.getMessage());
            throw e;
        }
    }

    @Override
    public void close() throws JMSException {
        try {
            if (session != null) session.close();
            if (connection != null) connection.close();
            System.out.println("IBM MQ connection closed.");
        } catch (JMSException e) {
            System.err.println("Error closing IBM MQ connection: " + e.getMessage());
            throw e;
        }
    }
}
