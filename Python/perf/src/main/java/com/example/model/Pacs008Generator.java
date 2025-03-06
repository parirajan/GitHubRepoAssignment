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

        // ✅ Ensure no null values are passed
        if (messageId == null || messageId.isEmpty()) messageId = "DEFAULT_MSG_ID";
        if (creationDate == null || creationDate.isEmpty()) creationDate = "1970-01-01T00:00:00";
        if (instructionId == null || instructionId.isEmpty()) instructionId = "INST_DEFAULT";
        if (endToEndId == null || endToEndId.isEmpty()) endToEndId = "E2E_DEFAULT";
        if (currency == null || currency.isEmpty()) currency = "USD";
        if (instructingAgent == null || instructingAgent.isEmpty()) instructingAgent = "BANK000";
        if (instructedAgent == null || instructedAgent.isEmpty()) instructedAgent = "BANK999";
        if (debtorName == null || debtorName.isEmpty()) debtorName = "Default_Debtor";
        if (creditorName == null || creditorName.isEmpty()) creditorName = "Default_Creditor";

        return new Pacs008Message(messageId, creationDate, instructionId, endToEndId,
                amount, currency, instructingAgent, instructedAgent, debtorName, creditorName);
    }
}
