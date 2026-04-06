package com.habitflow.controller;

import com.habitflow.entity.Habit;
import com.habitflow.service.HabitService;
import com.habitflow.service.HuggingFaceService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/habits")
public class HabitController {

    private final HabitService habitService;
    private final HuggingFaceService huggingFaceService;

    public HabitController(HabitService habitService, HuggingFaceService huggingFaceService) {
        this.habitService = habitService;
        this.huggingFaceService = huggingFaceService;
    }

    @PostMapping
    public ResponseEntity<Habit> create(@RequestParam Long userId, @RequestBody Habit habit) {
        return ResponseEntity.ok(habitService.createHabit(userId, habit));
    }

    @GetMapping
    public ResponseEntity<List<Habit>> list(@RequestParam Long userId) {
        return ResponseEntity.ok(habitService.getHabits(userId));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Habit> update(@PathVariable Long id, @RequestBody Habit habit) {
        return ResponseEntity.ok(habitService.updateHabit(id, habit));
    }

    @PostMapping("/suggest")
    public ResponseEntity<Map<String, String>> suggest(@RequestBody Map<String, String> body) {
        HuggingFaceService.AiResult result = huggingFaceService.suggestHabit(body.getOrDefault("input", ""));
        return ResponseEntity.ok(Map.of(
            "suggestion", result.content(),
            "source", result.fallbackUsed() ? "fallback" : "ai",
            "reason", result.fallbackReason()
        ));
    }
}
