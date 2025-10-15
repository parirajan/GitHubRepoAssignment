import javax.jms.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import com.ibm.mq.jms.MQConnectionFactory;
import com.ibm.msg.client.wmq.WMQConstants;

@Component
public class MqListener {

    @Value("${ibm.mq.queue-manager}") private String qmgr;
    @Value("${ibm.mq.channel}") private String channel;
    @Value("${ibm.mq.conn-name}") private String connName;
    @Value("${ibm.mq.user:}") private String user;
    @Value("${ibm.mq.password:}") private String pass;

    @Value("${ibm.mq.request-queue}") private String requestQueue;
    @Value("${listener.poll-ms:1000}") private long pollMs;

    public void startAsync() {
        System.out.println("MqListener starting thread...");
        Thread t = new Thread(this::runLoop, "mq-consumer-loop");
        t.setDaemon(false);
        t.start();
    }

    private void runLoop() {
        int attempt = 0;

        while (true) {
            MQConnectionFactory f = new MQConnectionFactory();
            try {
                f.setTransportType(WMQConstants.WMQ_CM_CLIENT);
                f.setConnectionNameList(connName);
                f.setChannel(channel);
                f.setQueueManager(qmgr);

                Connection connection = (user != null && !user.isBlank())
                        ? f.createConnection(user, pass)
                        : f.createConnection();

                Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
                Queue inQ = session.createQueue("queue:///" + requestQueue);
                MessageConsumer consumer = session.createConsumer(inQ);

                connection.start();
                System.out.println("[CONSUMER] Connected to MQ; listening on " + requestQueue + "...");

                attempt = 0; // reset backoff
                while (true) {
                    Message m = consumer.receive(pollMs);
                    if (m == null) continue;

                    if (m instanceof TextMessage tm) {
                        System.out.println("[CONSUMER] Received: " + tm.getText());
                    } else {
                        System.out.println("[CONSUMER] Received non-text message: " + m.getClass().getSimpleName());
                    }
                }

            } catch (Exception e) {
                attempt++;
                long backoffMs = Math.min(30000, 1000L * attempt);
                System.err.println("[CONSUMER] MQ failure (attempt " + attempt + "): " + e.getMessage());
                try { Thread.sleep(backoffMs); } catch (InterruptedException ignored) {}
            }
        }
    }
}
