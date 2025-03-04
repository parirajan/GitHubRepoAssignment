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

    // Default Constructor (Required by Avro)
    public Pacs008Message() {}

    // Parameterized Constructor
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

    // Getters
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

    // Avro Schema Definition
    public static final Schema SCHEMA$ = new Schema.Parser().parse(
        "{ \"type\": \"record\", \"name\": \"Pacs008Message\", \"fields\": [" +
        "{\"name\": \"messageId\", \"type\": \"string\"}," +
        "{\"name\": \"creationDate\", \"type\": \"string\"}," +
        "{\"name\": \"instructionId\", \"type\": \"string\"}," +
        "{\"name\": \"endToEndId\", \"type\": \"string\"}," +
        "{\"name\": \"amount\", \"type\": \"double\"}," +
        "{\"name\": \"currency\", \"type\": \"string\"}," +
        "{\"name\": \"instructingAgent\", \"type\": \"string\"}," +
        "{\"name\": \"instructedAgent\", \"type\": \"string\"}," +
        "{\"name\": \"debtorName\", \"type\": \"string\"}," +
        "{\"name\": \"creditorName\", \"type\": \"string\"}" +
        "] }");

    @Override
    public Schema getSchema() {
        return SCHEMA$;
    }

    @Override
    public Object get(int field) {
        switch (field) {
            case 0: return messageId;
            case 1: return creationDate;
            case 2: return instructionId;
            case 3: return endToEndId;
            case 4: return amount;
            case 5: return currency;
            case 6: return instructingAgent;
            case 7: return instructedAgent;
            case 8: return debtorName;
            case 9: return creditorName;
            default: throw new IllegalArgumentException("Invalid field index");
        }
    }

    @Override
    public void put(int field, Object value) {
        switch (field) {
            case 0: messageId = value.toString(); break;
            case 1: creationDate = value.toString(); break;
            case 2: instructionId = value.toString(); break;
            case 3: endToEndId = value.toString(); break;
            case 4: amount = (double) value; break;
            case 5: currency = value.toString(); break;
            case 6: instructingAgent = value.toString(); break;
            case 7: instructedAgent = value.toString(); break;
            case 8: debtorName = value.toString(); break;
            case 9: creditorName = value.toString(); break;
            default: throw new IllegalArgumentException("Invalid field index");
        }
    }
}
