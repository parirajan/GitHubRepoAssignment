package com.mycompany.pingservice;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.stereotype.Component;

@SpringBootApplication
public class PingClientApplication {
    public static void main(String[] args) {
        SpringApplication.run(PingClientApplication.class, args);
    }
}
