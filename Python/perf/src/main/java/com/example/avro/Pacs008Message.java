package com.example.avro;

import org.apache.avro.Schema;
import org.apache.avro.specific.SpecificRecordBase;
import org.apache.avro.specific.SpecificRecord;

import java.io.Serializable;

public class Pacs008Message extends SpecificRecordBase implements SpecificRecord, Serializable {
    private String messageId;
    private String creationDate;
    private String instructionId;
    private String endToEndId;
    private double amount;
    private String currency;
    private String instructingAgent;
    private String instructedAgent;
    private String debtorName;
    private String creditorName;

    public Pacs008Message() {}

    public Pacs008Message(String messageId, String creationDate, String instructionId, String endToEndId,
                          double amount, String currency, String instructingAgent, String instructedAgent,
                          String debtorName, String creditorName) {
        this.messageId = messageId;
        this.creationDate = creationDate;
        this.instructionId = instructionId;
        this.endToEndId = endToEndId;
        this.amount = amount;
        this.currency = currency;
        this.instructingAgent = instructingAgent;
        this.instructedAgent = instructedAgent;
        this.debtorName = debtorName;
        this.creditorName = creditorName;
    }

    public String getMessageId() { return messageId; }
    public String getCreationDate() { return creationDate; }
    public String getInstructionId() { return instructionId; }
    public String getEndToEndId() { return endToEndId; }
    public double getAmount() { return amount; }
    public String getCurrency() { return currency; }
    public String getInstructingAgent() { return instructingAgent; }
    public String getInstructedAgent() { return instructedAgent; }
    public String getDebtorName() { return debtorName; }
    public String getCreditorName() { return creditorName; }
}
