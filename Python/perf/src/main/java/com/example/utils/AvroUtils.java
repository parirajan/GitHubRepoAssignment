package com.example.utils;

import org.apache.avro.io.*;
import org.apache.avro.specific.SpecificDatumReader;
import org.apache.avro.specific.SpecificDatumWriter;
import com.example.avro.Pacs008Message;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class AvroUtils {

    // ✅ Serialize Pacs008Message to Avro binary format
    public static byte[] serializeToAvro(Pacs008Message message) {
        try (ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            DatumWriter<Pacs008Message> datumWriter = new SpecificDatumWriter<>(Pacs008Message.class);
            BinaryEncoder encoder = EncoderFactory.get().binaryEncoder(outputStream, null);
            datumWriter.write(message, encoder);
            encoder.flush();
            return outputStream.toByteArray();
        } catch (IOException e) {
            throw new RuntimeException("❌ Failed to serialize Avro message", e);
        }
    }

    // ✅ Deserialize Avro binary data back to Pacs008Message
    public static Pacs008Message deserializeFromAvro(byte[] avroData) {
        try (ByteArrayInputStream inputStream = new ByteArrayInputStream(avroData)) {
            DatumReader<Pacs008Message> datumReader = new SpecificDatumReader<>(Pacs008Message.class);
            BinaryDecoder decoder = DecoderFactory.get().binaryDecoder(inputStream, null);
            return datumReader.read(null, decoder);
        } catch (IOException e) {
            throw new RuntimeException("❌ Failed to deserialize Avro message", e);
        }
    }
}
