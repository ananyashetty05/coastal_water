package com.habitflow.controller;

import com.habitflow.entity.Note;
import com.habitflow.service.NoteService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/notes")
@RequiredArgsConstructor
public class NoteController {

    private final NoteService noteService;

    @PostMapping
    public ResponseEntity<Note> create(@RequestParam Long userId, @RequestBody Note note) {
        return ResponseEntity.ok(noteService.createNote(userId, note));
    }

    @GetMapping
    public ResponseEntity<List<Note>> list(@RequestParam Long userId) {
        return ResponseEntity.ok(noteService.getNotes(userId));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Note> update(@PathVariable Long id, @RequestBody Note note) {
        return ResponseEntity.ok(noteService.updateNote(id, note));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        noteService.deleteNote(id);
        return ResponseEntity.noContent().build();
    }
}
