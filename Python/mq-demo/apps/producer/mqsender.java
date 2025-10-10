// javax JMS version (since you chose javax)
import javax.jms.*;
import javax.annotation.PostConstruct; // not used now, can be removed
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.event.EventListener;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.stereotype.Component;
import com.ibm.mq.jms.MQConnectionFactory;
import com.ibm.msg.client.wmq.WMQConstants;

@Component
public class MqSender {

  @Value("${ibm.mq.queue-manager}") private String qmgr;
  @Value("${ibm.mq.channel}") private String channel;
  @Value("${ibm.mq.conn-name}") private String connName; // e.g. "mq1(1414)"
  @Value("${ibm.mq.user}") private String user;
  @Value("${ibm.mq.password}") private String pass;
  @Value("${ibm.mq.request-queue}") private String queueName;
  @Value("${ibm.mq.interval-ms:2000}") private long intervalMs;

  @EventListener(ApplicationReadyEvent.class)
  public void onAppReady() {
    Thread t = new Thread(this::runLoop, "mq-producer-loop");
    t.setDaemon(false);
    t.start();
  }

  private void runLoop() {
    int attempt = 0;
    while (true) {
      MQConnectionFactory f = new MQConnectionFactory();
      try {
        f.setTransportType(WMQConstants.WMQ_CM_CLIENT);
        f.setQueueManager(qmgr);
        f.setConnectionNameList(connName);
        f.setChannel(channel);

        try (Connection c = f.createConnection(user, pass)) {
          Session s = c.createSession(false, Session.AUTO_ACKNOWLEDGE);
          Queue q = s.createQueue("queue:///" + queueName);
          MessageProducer p = s.createProducer(q);
          c.start();
          System.out.println("[PRODUCER] Connected to MQ. Sending messages...");
          int i = 0;
          attempt = 0; // reset backoff
          while (true) {
            TextMessage m = s.createTextMessage("PAYMENT-" + (++i));
            p.send(m);
            System.out.println("[PRODUCER] Sent: " + m.getText());
            Thread.sleep(Math.max(200, intervalMs));
          }
        }
      } catch (Exception e) {
        attempt++;
        long backoff = Math.min(30000, 1000L * attempt);
        System.err.println("[PRODUCER] MQ failure (attempt " + attempt + "): " + e.getMessage());
        try { Thread.sleep(backoff); } catch (InterruptedException ignored) {}
      }
    }
  }
}
