package com.habitflow.service;

import com.habitflow.entity.Note;
import com.habitflow.entity.User;
import com.habitflow.repository.NoteRepository;
import com.habitflow.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class NoteService {
    @Autowired private NoteRepository noteRepository;
    @Autowired private UserRepository userRepository;

    public Note createNote(Long userId, Note note) {
        User user = userRepository.findById(userId).orElseThrow();
        note.setUser(user);
        return noteRepository.save(note);
    }

    public List<Note> getNotes(Long userId) {
        return noteRepository.findByUserId(userId);
    }

    public Note updateNote(Long id, Note update) {
        Note note = noteRepository.findById(id).orElseThrow();
        note.setContent(update.getContent());
        return noteRepository.save(note);
    }

    public void deleteNote(Long id) {
        noteRepository.deleteById(id);
    }
}
