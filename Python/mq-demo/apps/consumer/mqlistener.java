package org.demo.consumer;
import jakarta.annotation.PostConstruct;
import jakarta.jms.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import com.ibm.mq.jms.MQConnectionFactory;
import com.ibm.msg.client.wmq.WMQConstants;

@Component
public class MqListener {
  @Value("${ibm.mq.queue-manager}") String qmgr;
  @Value("${ibm.mq.channel}") String channel;
  @Value("${ibm.mq.conn-name}") String connName;
  @Value("${ibm.mq.user}") String user;
  @Value("${ibm.mq.password}") String pass;
  @Value("${ibm.mq.request-queue}") String queueName;

  @PostConstruct
  public void listen() throws Exception {
    MQConnectionFactory f = new MQConnectionFactory();
    f.setTransportType(WMQConstants.WMQ_CM_CLIENT);
    f.setQueueManager(qmgr);
    f.setConnectionNameList(connName);
    f.setChannel(channel);
    Connection c = f.createConnection(user, pass);
    Session s = c.createSession(false, Session.AUTO_ACKNOWLEDGE);
    Queue q = s.createQueue("queue:///" + queueName);
    MessageConsumer consumer = s.createConsumer(q);
    c.start();
    consumer.setMessageListener(m -> {
      try {
        if (m instanceof TextMessage t) System.out.println("[CONSUMER] Received: " + t.getText());
      } catch (JMSException e) { e.printStackTrace(); }
    });
  }
}
