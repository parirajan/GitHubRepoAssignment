package org.frb.fednow.consumer;

import javax.jms.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.event.EventListener;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.stereotype.Component;

import com.ibm.mq.jms.MQConnectionFactory;
import com.ibm.msg.client.wmq.WMQConstants;

@Component
public class MqListener {

    @Value("${ibm.mq.queue-manager}")       private String qmgr;
    @Value("${ibm.mq.channel}")             private String channel;
    @Value("${ibm.mq.conn-name}")           private String connName;   // host(port) or list
    @Value("${ibm.mq.user:}")               private String user;
    @Value("${ibm.mq.password:}")           private String pass;

    @Value("${ibm.mq.request-queue}")       private String requestQueue;
    @Value("${ibm.mq.response-queue:}")     private String responseQueue; // optional

    @Value("${listener.poll-ms:1000}")      private long pollMs;

    @EventListener(ApplicationReadyEvent.class)
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

                MessageProducer replyProducer = null;
                Queue outQ = null;
                if (responseQueue != null && !responseQueue.isBlank()) {
                    outQ = session.createQueue("queue:///" + responseQueue);
                    replyProducer = session.createProducer(outQ);
                }

                connection.start();
                System.out.println("[CONSUMER] Connected. Listening on " + requestQueue +
                                   (replyProducer != null ? (" ; replying to " + responseQueue) : "") + "...");

                attempt = 0; // reset backoff on success

                // Simple receive loop (blocking with timeout)
                while (true) {
                    Message m = consumer.receive(pollMs); // null on timeout -> loop again
                    if (m == null) continue;

                    if (m instanceof TextMessage tm) {
                        String text = tm.getText();
                        System.out.println("[CONSUMER] Received: " + text);

                        // Optional: send a response/ACK
                        if (replyProducer != null) {
                            TextMessage resp = session.createTextMessage("ACK:" + text);
                            // correlate with request if you want
                            resp.setJMSCorrelationID(m.getJMSMessageID());
                            replyProducer.send(resp);
                            System.out.println("[CONSUMER] Replied: " + resp.getText());
                        }
                    } else {
                        System.out.println("[CONSUMER] Non-text message type: " + m.getClass().getName());
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
