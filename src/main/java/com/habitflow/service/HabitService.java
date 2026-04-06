package com.habitflow.service;

import com.habitflow.entity.Habit;
import com.habitflow.entity.User;
import com.habitflow.repository.HabitRepository;
import com.habitflow.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class HabitService {
    @Autowired private HabitRepository habitRepository;
    @Autowired private UserRepository userRepository;

    public Habit createHabit(Long userId, Habit habit) {
        User user = userRepository.findById(userId).orElseThrow();
        habit.setUser(user);
        habit.setStreak(0);
        return habitRepository.save(habit);
    }

    public List<Habit> getHabits(Long userId) {
        return habitRepository.findByUserId(userId);
    }

    public Habit updateHabit(Long habitId, Habit update) {
        Habit habit = habitRepository.findById(habitId).orElseThrow();
        habit.setName(update.getName());
        habit.setFrequency(update.getFrequency());
        habit.setEmoji(update.getEmoji());
        if (update.getStreak() != null) {
            habit.setStreak(update.getStreak());
        }
        return habitRepository.save(habit);
    }
}
