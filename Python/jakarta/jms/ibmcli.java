import com.ibm.mq.jms.MQQueueConnectionFactory;
import jakarta.jms.*;

import javax.net.ssl.SSLContext;
import java.io.FileInputStream;
import java.security.KeyStore;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.TrustManagerFactory;

public class IbmMqClient {
    private Connection connection;
    private Session session;
    private Queue queue;

    public IbmMqClient(String host, int port, String queueManager, String channel, String queueName, 
                       String keystorePath, String keystorePassword) throws Exception {
        
        MQQueueConnectionFactory factory = new MQQueueConnectionFactory();
        factory.setHostName(host);
        factory.setPort(port);
        factory.setQueueManager(queueManager);
        factory.setChannel(channel);
        factory.setTransportType(com.ibm.msg.client.wmq.common.CommonConstants.WMQ_CM_CLIENT);
        
        // Set SSL Context
        SSLContext sslContext = createSSLContext(keystorePath, keystorePassword);
        factory.setSSLCipherSuite("TLS_RSA_WITH_AES_256_CBC_SHA");
        factory.setSSLContext(sslContext);

        ConnectionFactory connectionFactory = factory;
        connection = connectionFactory.createConnection();  // No username/password required
        session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
        queue = session.createQueue(queueName);
        connection.start();
    }

    private SSLContext createSSLContext(String keystorePath, String keystorePassword) throws Exception {
        KeyStore keyStore = KeyStore.getInstance("JKS");
        keyStore.load(new FileInputStream(keystorePath), keystorePassword.toCharArray());

        KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
        kmf.init(keyStore, keystorePassword.toCharArray());

        TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(keyStore);

        SSLContext sslContext = SSLContext.getInstance("TLS");
        sslContext.init(kmf.getKeyManagers(), tmf.getTrustManagers(), null);
        return sslContext;
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
