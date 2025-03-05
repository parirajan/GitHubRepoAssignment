package com.example.config;

import com.aerospike.client.Log;

public class AerospikeLogCallback implements Log.Callback {
    @Override
    public void log(Log.Level level, String message) {
        System.out.println("Aerospike Client [" + level + "]: " + message);
    }
}
