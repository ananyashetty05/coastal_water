package com.habitflow.service;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@Service
public class HuggingFaceService {
    public record AiResult(String content, boolean fallbackUsed, String fallbackReason) {}

    @Value("${huggingface.api.key:}")
    private String huggingFaceApiKey;

    @Value("${huggingface.model:Qwen/Qwen2.5-7B-Instruct-1M:featherless-ai}")
    private String huggingFaceModel;

    private final WebClient webClient = WebClient.builder().build();

    public AiResult coach(String userContext) {
        String normalizedContext = userContext == null ? "" : userContext.trim();
        String prompt = """
            You are a supportive habit coach.
            Give one practical, encouraging answer in 2 to 4 sentences.
            Keep it specific, light, and easy to follow.
            User request: %s
            """.formatted(normalizedContext);

        return complete(prompt, fallbackCoachSuggestion(normalizedContext));
    }

    public AiResult suggestHabit(String userContext) {
        String normalizedContext = userContext == null ? "" : userContext.trim();
        String prompt = """
            Suggest one realistic habit based on the user's context.
            Respond in plain text with:
            Habit: <short habit name>
            Why: <one sentence>
            First step: <one sentence>
            Reminder: <HH:MM>
            User context: %s
            """.formatted(normalizedContext);

        return complete(prompt, fallbackHabitSuggestion(normalizedContext));
    }

    private AiResult complete(String prompt, String fallbackText) {
        if (huggingFaceApiKey == null || huggingFaceApiKey.isBlank()) {
            return new AiResult(fallbackText, true, "Hugging Face API key is missing.");
        }

        JsonNode response;
        try {
            response = webClient.post()
                .uri("https://router.huggingface.co/v1/chat/completions")
                .header("Authorization", "Bearer " + huggingFaceApiKey)
                .bodyValue(Map.of(
                    "model", huggingFaceModel,
                    "messages", new Object[] {
                        Map.of(
                            "role", "user",
                            "content", prompt
                        )
                    },
                    "max_tokens", 220,
                    "temperature", 0.7
                ))
                .retrieve()
                .bodyToMono(JsonNode.class)
                .block();
        } catch (WebClientResponseException ex) {
            return new AiResult(
                fallbackText,
                true,
                "Hugging Face request failed with status %s.".formatted(ex.getStatusCode())
            );
        } catch (RuntimeException ex) {
            return new AiResult(fallbackText, true, "Could not reach Hugging Face inference service.");
        }

        if (response == null) {
            return new AiResult(fallbackText, true, "Hugging Face returned an empty response.");
        }

        String content = extractGeneratedText(response);
        if (content == null || content.isBlank()) {
            return new AiResult(fallbackText, true, "Hugging Face returned no usable generated text.");
        }

        return new AiResult(content.trim(), false, "");
    }

    private String extractGeneratedText(JsonNode response) {
        if (response.has("choices")
            && response.get("choices").isArray()
            && response.get("choices").size() > 0
            && response.get("choices").get(0).has("message")
            && response.get("choices").get(0).get("message").has("content")) {
            return response.get("choices").get(0).get("message").get("content").asText();
        }

        if (response.has("generated_text")) {
            return response.get("generated_text").asText();
        }

        if (response.isArray() && response.size() > 0 && response.get(0).has("generated_text")) {
            return response.get(0).get("generated_text").asText();
        }

        return response.toString();
    }

    private String fallbackCoachSuggestion(String userContext) {
        String normalized = userContext == null ? "" : userContext.toLowerCase();
        if (containsAny(normalized, "weekend", "saturday", "sunday")) {
            if (containsAny(normalized, "light activity", "easy", "gentle", "low energy")) {
                return "Try a 20-minute weekend reset: take an easy walk, do a few light stretches, and spend 5 minutes planning one thing you want to enjoy. Keep it relaxed so it feels refreshing instead of like another task.";
            }
            return "Pick one small weekend activity that feels restorative, like a walk, a short tidy-up, or a quiet coffee and journal session. The goal is to create a little momentum without overloading yourself.";
        }
        if (containsAny(normalized, "motivate", "motivation", "consistent", "routine")) {
            return "Make consistency easier by shrinking the goal until it feels almost too small to skip. A tiny action done every day builds more trust in yourself than a perfect plan done once.";
        }
        if (containsAny(normalized, "recover", "recovery", "missed", "reset")) {
            return "Treat recovery like a reset, not a punishment. Pick one simple action for tomorrow, do it early, and let that be enough to get back in motion.";
        }
        return "Choose one light action you can finish in under 20 minutes and do it at the same time you usually slow down. Keeping it simple is what makes it sustainable.";
    }

    private String fallbackHabitSuggestion(String userContext) {
        String normalized = userContext == null ? "" : userContext.toLowerCase();
        if (containsAny(normalized, "recover", "recovery", "injury", "healing")) {
            if (containsAny(normalized, "movement", "walk", "mobility", "stretch")) {
                return """
                    Habit: Gentle recovery walk
                    Why: A short, low-pressure walk helps you rebuild consistency without overloading your body.
                    First step: Walk slowly for 5 minutes and add 2 gentle stretches afterward.
                    Reminder: 18:00
                    """.trim();
            }
            return """
                Habit: Daily recovery reset
                Why: Light movement done consistently is easier to maintain while recovering.
                First step: Spend 10 minutes on easy mobility or a calm walk and note how you feel after.
                Reminder: 18:00
                """.trim();
        }
        if (containsAny(normalized, "movement", "exercise", "walk", "stretch", "mobility")) {
            return """
                Habit: 10-minute movement break
                Why: A short movement block is easier to repeat than a full workout plan.
                First step: Take a 5-minute walk, then do 5 easy stretches.
                Reminder: 08:00
                """.trim();
        }
        if (containsAny(normalized, "productive", "productivity", "focus", "deep work")) {
            return """
                Habit: Morning focus sprint
                Why: Starting with one clear priority reduces friction and builds momentum early.
                First step: Set a 25-minute timer and work on one task before opening messages.
                Reminder: 09:00
                """.trim();
        }
        if (containsAny(normalized, "study", "exam", "learn", "reading")) {
            return """
                Habit: 20-minute study block
                Why: Short focused sessions make studying feel approachable and repeatable.
                First step: Read for 20 minutes, then spend 5 minutes recalling key points without notes.
                Reminder: 19:00
                """.trim();
        }
        if (containsAny(normalized, "stress", "anxious", "overwhelmed", "burnout")) {
            return """
                Habit: Calm reset pause
                Why: A short pause can lower overwhelm and help you restart with more clarity.
                First step: Take 3 slow breaths, write one priority, and work on it for 10 minutes.
                Reminder: 15:00
                """.trim();
        }
        if (containsAny(normalized, "sleep", "rest", "bedtime")) {
            return """
                Habit: Evening wind-down
                Why: A repeatable pre-sleep routine makes falling asleep feel more natural.
                First step: Dim lights and stay off your phone for 30 minutes before bed.
                Reminder: 22:00
                """.trim();
        }
        if (containsAny(normalized, "healthy", "health", "fitness")) {
            return """
                Habit: After-meal walk
                Why: Linking movement to a meal makes the habit easier to remember.
                First step: Walk for 10 minutes after one meal each day this week.
                Reminder: 13:00
                """.trim();
        }
        if (containsAny(normalized, "consistent", "routine", "habit")) {
            return """
                Habit: Two-minute anchor habit
                Why: Tiny habits are easier to repeat and help you build consistency.
                First step: Attach one 2-minute action to something you already do each day.
                Reminder: 08:30
                """.trim();
        }
        return """
            Habit: Morning top-three list
            Why: Choosing your top three priorities early helps the day feel more intentional.
            First step: Write your top 3 priorities each morning before checking social media or email.
            Reminder: 08:00
            """.trim();
    }

    private boolean containsAny(String value, String... keywords) {
        for (String keyword : keywords) {
            if (value.contains(keyword)) {
                return true;
            }
        }
        return false;
    }
}
