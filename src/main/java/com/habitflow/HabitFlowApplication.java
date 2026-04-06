package com.habitflow;

import com.habitflow.entity.User;
import com.habitflow.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.password.PasswordEncoder;

@SpringBootApplication
public class HabitFlowApplication {
    public static void main(String[] args) {
        SpringApplication.run(HabitFlowApplication.class, args);
    }

    @Bean
    @SuppressWarnings("unused")
    CommandLineRunner seedDevUser(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        return args -> {
            if (userRepository.count() == 0) {
                User user = new User();
                user.setName("Demo User");
                user.setEmail("demo@habitflow.local");
                user.setPassword(passwordEncoder.encode("demo123"));
                userRepository.save(user);
            }
        };
    }
}
