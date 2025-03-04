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

        return new Pacs008Message(messageId, creationDate, instructionId, endToEndId,
                amount, currency, instructingAgent, instructedAgent, debtorName, creditorName);
    }
}
