package com.habitflow.controller;

import com.habitflow.service.HuggingFaceService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/ai")
public class AIController {

    private final HuggingFaceService huggingFaceService;

    public AIController(HuggingFaceService huggingFaceService) {
        this.huggingFaceService = huggingFaceService;
    }

    @PostMapping("/recommend")
    public ResponseEntity<Map<String, String>> recommend(@RequestBody Map<String, String> body) {
        HuggingFaceService.AiResult result = huggingFaceService.coach(body.getOrDefault("input", ""));
        return ResponseEntity.ok(Map.of(
            "suggestion", result.content(),
            "source", result.fallbackUsed() ? "fallback" : "ai",
            "reason", result.fallbackReason()
        ));
    }
}
