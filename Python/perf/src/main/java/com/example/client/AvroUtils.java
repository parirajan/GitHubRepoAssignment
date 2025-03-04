package com.example.client;

import com.example.avro.Pacs008Message;
import org.apache.avro.io.*;
import org.apache.avro.specific.*;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class AvroUtils {

    public static byte[] serializeToAvro(Pacs008Message message) {
        try (ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            DatumWriter<Pacs008Message> datumWriter = new SpecificDatumWriter<>(Pacs008Message.class);
            BinaryEncoder encoder = EncoderFactory.get().binaryEncoder(outputStream, null);
            datumWriter.write(message, encoder);
            encoder.flush();
            return outputStream.toByteArray();
        } catch (IOException e) {
            throw new RuntimeException("Error serializing Avro data", e);
        }
    }
}
