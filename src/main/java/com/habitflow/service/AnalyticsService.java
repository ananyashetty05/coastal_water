package com.habitflow.service;

import com.habitflow.entity.Habit;
import com.habitflow.entity.Task;
import com.habitflow.repository.HabitLogRepository;
import com.habitflow.repository.HabitRepository;
import com.habitflow.repository.TaskRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AnalyticsService {
    @Autowired private HabitRepository habitRepository;
    @Autowired private HabitLogRepository habitLogRepository;
    @Autowired private TaskRepository taskRepository;

    public Map<String, Object> getOverview(Long userId) {
        List<Habit> habits = habitRepository.findByUserId(userId);
        List<Task> tasks = taskRepository.findByUserId(userId);

        int totalHabits = habits.size();
        int completedTasks = (int) tasks.stream().filter(Task::isCompleted).count();

        Map<String, Object> result = new HashMap<>();
        result.put("totalHabits", totalHabits);
        result.put("totalTasks", tasks.size());
        result.put("completedTasks", completedTasks);
        result.put("activeStreaks", habits.stream().mapToInt(Habit::getStreak).sum());

        LocalDate today = LocalDate.now();
        long doneToday = habitLogRepository.findAll().stream()
                .filter(log -> log.getDate().equals(today) && log.isDone())
                .count();
        result.put("habitsDoneToday", doneToday);

        return result;
    }
}
