package com.habitflow.service;

import com.habitflow.entity.Task;
import com.habitflow.entity.User;
import com.habitflow.repository.TaskRepository;
import com.habitflow.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TaskService {
    @Autowired private TaskRepository taskRepository;
    @Autowired private UserRepository userRepository;

    public Task createTask(Long userId, Task task) {
        User user = userRepository.findById(userId).orElseThrow();
        task.setUser(user);
        return taskRepository.save(task);
    }

    public List<Task> getTasks(Long userId) {
        return taskRepository.findByUserId(userId);
    }

    public Task updateTask(Long id, Task update) {
        Task task = taskRepository.findById(id).orElseThrow();
        task.setTitle(update.getTitle());
        task.setCompleted(update.isCompleted());
        return taskRepository.save(task);
    }

    public void deleteTask(Long id) {
        taskRepository.deleteById(id);
    }
}
