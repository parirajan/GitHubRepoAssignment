package org.demo.producer;
import jakarta.annotation.PostConstruct;
import jakarta.jms.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import com.ibm.mq.jms.MQConnectionFactory;
import com.ibm.msg.client.wmq.WMQConstants;

@Component
public class MqSender {
  @Value("${ibm.mq.queue-manager}") String qmgr;
  @Value("${ibm.mq.channel}") String channel;
  @Value("${ibm.mq.conn-name}") String connName;
  @Value("${ibm.mq.user}") String user;
  @Value("${ibm.mq.password}") String pass;
  @Value("${ibm.mq.request-queue}") String queueName;

  @PostConstruct
  public void start() throws Exception {
    MQConnectionFactory f = new MQConnectionFactory();
    f.setTransportType(WMQConstants.WMQ_CM_CLIENT);
    f.setQueueManager(qmgr);
    f.setConnectionNameList(connName);
    f.setChannel(channel);
    try (Connection c = f.createConnection(user, pass)) {
      Session s = c.createSession(false, Session.AUTO_ACKNOWLEDGE);
      Queue q = s.createQueue("queue:///" + queueName);
      MessageProducer p = s.createProducer(q);
      c.start();
      int i = 0;
      while (true) {
        String msg = "PAYMENT-" + (++i);
        p.send(s.createTextMessage(msg));
        System.out.println("[PRODUCER] Sent: " + msg);
        Thread.sleep(2000);
      }
    }
  }
}
