package com.example.model;

import com.example.avro.Pacs008Message;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;
import java.util.UUID;

public class Pacs008Generator {
    private static final Random random = new Random();

    public static Pacs008Message generate() {
        String messageId = UUID.randomUUID().toString();
        String creationDate = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
        String instructionId = "INST" + random.nextInt(100000);
        String endToEndId = "E2E" + random.nextInt(100000);
        double amount = 100 + (random.nextDouble() * 10000);
        String currency = "USD";
        String instructingAgent = "BANK" + random.nextInt(1000);
        String instructedAgent = "BANK" + random.nextInt(1000);
        String debtorName = "Debtor_" + random.nextInt(1000);
        String creditorName = "Creditor_" + random.nextInt(1000);

        // Ensure all fields are properly initialized
        messageId = (messageId == null || messageId.isEmpty()) ? "DEFAULT_MSG_ID" : messageId;
        creationDate = (creationDate == null || creationDate.isEmpty()) ? "1970-01-01T00:00:00" : creationDate;
        instructionId = (instructionId == null || instructionId.isEmpty()) ? "INST_DEFAULT" : instructionId;
        endToEndId = (endToEndId == null || endToEndId.isEmpty()) ? "E2E_DEFAULT" : endToEndId;
        currency = (currency == null || currency.isEmpty()) ? "USD" : currency;
        instructingAgent = (instructingAgent == null || instructingAgent.isEmpty()) ? "BANK000" : instructingAgent;
        instructedAgent = (instructedAgent == null || instructedAgent.isEmpty()) ? "BANK999" : instructedAgent;
        debtorName = (debtorName == null || debtorName.isEmpty()) ? "Default_Debtor" : debtorName;
        creditorName = (creditorName == null || creditorName.isEmpty()) ? "Default_Creditor" : creditorName;

        return new Pacs008Message(messageId, creationDate, instructionId, endToEndId,
                amount, currency, instructingAgent, instructedAgent, debtorName, creditorName);
    }
}
