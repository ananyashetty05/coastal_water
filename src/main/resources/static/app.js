const USER_ID = 1;

const state = {
  analytics: null,
  habits: [],
  tasks: [],
  notes: [],
};

const els = {
  todayLabel: document.getElementById("todayLabel"),
  focusScore: document.getElementById("focusScore"),
  focusMessage: document.getElementById("focusMessage"),
  statHabits: document.getElementById("statHabits"),
  statHabitsMeta: document.getElementById("statHabitsMeta"),
  statTasks: document.getElementById("statTasks"),
  statTasksMeta: document.getElementById("statTasksMeta"),
  statStreaks: document.getElementById("statStreaks"),
  statStreaksMeta: document.getElementById("statStreaksMeta"),
  statNotes: document.getElementById("statNotes"),
  statNotesMeta: document.getElementById("statNotesMeta"),
  heroStreak: document.getElementById("heroStreak"),
  dashboardContent: document.getElementById("dashboardContent"),
  completionPercent: document.getElementById("completionPercent"),
  completionSummary: document.getElementById("completionSummary"),
  habitList: document.getElementById("habitList"),
  taskList: document.getElementById("taskList"),
  noteList: document.getElementById("noteList"),
  aiOutput: document.getElementById("ai-output"),
  suggestionBanner: document.getElementById("suggestionBanner"),
  habitForm: document.getElementById("habitForm"),
  taskForm: document.getElementById("taskForm"),
  noteForm: document.getElementById("noteForm"),
  askAiBtn: document.getElementById("askAiBtn"),
  suggestHabitBtn: document.getElementById("suggestHabitBtn"),
  aiInput: document.getElementById("ai-input"),
  habitInput: document.getElementById("habitInput"),
  habitFrequency: document.getElementById("habitFrequency"),
  taskInput: document.getElementById("taskInput"),
  noteInput: document.getElementById("noteInput"),
};

function setTodayLabel() {
  const now = new Date();
  els.todayLabel.textContent = now.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function pickHabitEmoji(name) {
  const value = (name || "").toLowerCase();
  if (value.includes("read") || value.includes("book") || value.includes("study")) return "📚";
  if (value.includes("run") || value.includes("walk") || value.includes("gym") || value.includes("workout")) return "🏃";
  if (value.includes("code") || value.includes("project") || value.includes("build")) return "💻";
  if (value.includes("write") || value.includes("journal") || value.includes("note")) return "✍️";
  if (value.includes("water") || value.includes("drink")) return "💧";
  if (value.includes("sleep")) return "😴";
  if (value.includes("meditate") || value.includes("breathe")) return "🧘";
  if (value.includes("eat") || value.includes("meal")) return "🥗";
  return "✨";
}

function renderAnalytics() {
  const data = state.analytics || {};
  const totalHabits = Number(data.totalHabits || state.habits.length || 0);
  const totalTasks = Number(data.totalTasks || state.tasks.length || 0);
  const completedTasks = Number(
    data.completedTasks || state.tasks.filter((task) => task.completed).length || 0
  );
  const activeStreaks = Number(data.activeStreaks || 0);
  const habitsDoneToday = Number(data.habitsDoneToday || 0);
  const totalNotes = state.notes.length;
  const completionPercent = totalTasks
    ? Math.round((completedTasks / totalTasks) * 100)
    : 0;
  const focusScore = Math.min(
    100,
    Math.round(completionPercent * 0.6 + activeStreaks * 12 + totalHabits * 4)
  );

  els.statHabits.textContent = String(totalHabits);
  els.statHabitsMeta.textContent =
    totalHabits > 0 ? `${habitsDoneToday} logged today` : "Create your first habit";
  els.statTasks.textContent = String(totalTasks);
  els.statTasksMeta.textContent = `${completedTasks} completed`;
  els.statStreaks.textContent = String(activeStreaks);
  els.statStreaksMeta.textContent =
    activeStreaks > 0 ? "Consistency is building" : "Start a streak today";
  els.statNotes.textContent = String(totalNotes);
  els.statNotesMeta.textContent =
    totalNotes > 0 ? "Your ideas are captured" : "Write one useful note";
  els.heroStreak.textContent = String(activeStreaks);

  els.focusScore.textContent = String(focusScore);
  els.focusMessage.textContent =
    focusScore >= 75
      ? "Strong momentum. Protect the streak."
      : focusScore >= 40
        ? "You're in motion. Finish a few more high-value actions."
        : "Fresh start. One completed action will shift the day.";

  els.completionPercent.textContent = `${completionPercent}%`;
  els.completionSummary.textContent =
    totalTasks > 0
      ? `${completedTasks} of ${totalTasks} tasks completed`
      : "No tasks created yet.";
  document.documentElement.style.setProperty("--completion", String(completionPercent));

  els.dashboardContent.innerHTML = [
    {
      label: "Habit Footprint",
      value: `${totalHabits} active habits`,
      meta: `${habitsDoneToday} completed today, with ${activeStreaks} active streaks.`,
    },
    {
      label: "Execution Rate",
      value: `${completionPercent}% task completion`,
      meta: `${completedTasks} tasks done out of ${totalTasks || 0}.`,
    },
    {
      label: "Reflection Volume",
      value: `${totalNotes} notes captured`,
      meta: totalNotes
        ? "Keep writing short reflections to spot patterns."
        : "Use notes to save insights before they disappear.",
    },
  ]
    .map(
      (item) => `
        <div class="metric-item">
          <strong>${item.label}</strong>
          <p>${item.value}</p>
          <p class="metric-meta">${item.meta}</p>
        </div>
      `
    )
    .join("");
}

function renderHabits() {
  if (!state.habits.length) {
    els.habitList.innerHTML =
      '<div class="empty-state"><p class="empty-copy">No habits yet. Add one to begin your daily system.</p></div>';
    return;
  }

  els.habitList.innerHTML = state.habits
    .map((habit) => {
      const streak = Number(habit.streak || 0);
      const progress = Math.min(100, streak * 20);
      return `
        <article class="habit-card">
          <div class="habit-top">
            <div class="habit-emoji">${escapeHtml(habit.emoji || "✨")}</div>
            <div class="habit-copy">
              <h4>${escapeHtml(habit.name)}</h4>
              <p>${escapeHtml(habit.frequency || "daily")} cadence</p>
            </div>
            <span class="habit-streak-badge">🔥 ${streak}</span>
          </div>
          <div class="habit-progress">
            <div class="habit-progress-bar">
              <div class="habit-progress-fill" style="width: ${progress}%"></div>
            </div>
            <span class="habit-progress-label">${progress}% toward your next rhythm milestone</span>
          </div>
          <div class="habit-meta-row">
            <span class="meta-pill">Streak ${streak}</span>
            <span class="meta-pill">${escapeHtml((habit.frequency || "daily").toUpperCase())}</span>
          </div>
          <div class="habit-actions">
            <button class="secondary-button" type="button" data-habit-boost="${habit.id}">Mark Progress</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderTasks() {
  if (!state.tasks.length) {
    els.taskList.innerHTML =
      '<div class="empty-state"><p class="empty-copy">No tasks queued. Add a task to make the day concrete.</p></div>';
    return;
  }

  els.taskList.innerHTML = state.tasks
    .map(
      (task) => `
        <article class="task-item ${task.completed ? "complete" : ""}">
          <div class="task-copy">
            <strong>${escapeHtml(task.title)}</strong>
            <p>${task.completed ? "Completed and off your mind." : "Still in your execution queue."}</p>
          </div>
          <div class="task-actions">
            <button class="checkbox-button" type="button" data-task-toggle="${task.id}">
              ${task.completed ? "Completed" : "Mark Done"}
            </button>
            <button class="delete-button" type="button" data-task-delete="${task.id}">Delete</button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderNotes() {
  if (!state.notes.length) {
    els.noteList.innerHTML =
      '<div class="empty-state"><p class="empty-copy">No notes yet. Capture ideas, blockers, and wins here.</p></div>';
    return;
  }

  els.noteList.innerHTML = state.notes
    .map(
      (note, index) => `
        <article class="note-card">
          <small>Note ${index + 1}</small>
          <p>${escapeHtml(note.content)}</p>
        </article>
      `
    )
    .join("");
}

async function refreshAnalytics() {
  try {
    state.analytics = await api(`/api/analytics/overview?userId=${USER_ID}`);
  } catch (error) {
    state.analytics = null;
  }
}

async function loadHabits() {
  try {
    state.habits = await api(`/api/habits?userId=${USER_ID}`);
  } catch (error) {
    state.habits = [];
  }
}

async function loadTasks() {
  try {
    state.tasks = await api(`/api/tasks?userId=${USER_ID}`);
  } catch (error) {
    state.tasks = [];
  }
}

async function loadNotes() {
  try {
    state.notes = await api(`/api/notes?userId=${USER_ID}`);
  } catch (error) {
    state.notes = [];
  }
}

async function reloadAll() {
  await Promise.all([refreshAnalytics(), loadHabits(), loadTasks(), loadNotes()]);
  renderAnalytics();
  renderHabits();
  renderTasks();
  renderNotes();
}

async function addHabit(event) {
  event.preventDefault();
  const name = els.habitInput.value.trim();
  if (!name) {
    showBanner("suggestionBanner", "Add a habit name first.");
    return;
  }

  try {
    await api(`/api/habits?userId=${USER_ID}`, {
      method: "POST",
      body: JSON.stringify({
        name,
        frequency: els.habitFrequency.value,
        emoji: pickHabitEmoji(name),
        streak: 0,
      }),
    });

    els.habitForm.reset();
    showBanner("suggestionBanner", "Habit added successfully.");
    await reloadAll();
  } catch (error) {
    showBanner("suggestionBanner", `Could not add habit: ${error.message}`);
  }
}

async function boostHabit(id) {
  const habit = state.habits.find((item) => item.id === id);
  if (!habit) {
    return;
  }

  await api(`/api/habits/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      name: habit.name,
      frequency: habit.frequency,
      emoji: habit.emoji,
      streak: Number(habit.streak || 0) + 1,
    }),
  });

  await reloadAll();
}

async function addTask(event) {
  event.preventDefault();
  const title = els.taskInput.value.trim();
  if (!title) {
    return;
  }

  try {
    await api(`/api/tasks?userId=${USER_ID}`, {
      method: "POST",
      body: JSON.stringify({ title, completed: false }),
    });

    els.taskForm.reset();
    await reloadAll();
  } catch (error) {
    els.taskList.innerHTML = `<div class="empty-state"><p class="empty-copy">Could not add task: ${escapeHtml(error.message)}</p></div>`;
  }
}

async function toggleTask(id) {
  const task = state.tasks.find((item) => item.id === id);
  if (!task) {
    return;
  }

  await api(`/api/tasks/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      title: task.title,
      completed: !task.completed,
    }),
  });

  await reloadAll();
}

async function deleteTask(id) {
  await api(`/api/tasks/${id}`, { method: "DELETE" });
  await reloadAll();
}

async function addNote(event) {
  event.preventDefault();
  const content = els.noteInput.value.trim();
  if (!content) {
    return;
  }

  try {
    await api(`/api/notes?userId=${USER_ID}`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });

    els.noteForm.reset();
    await reloadAll();
  } catch (error) {
    els.noteList.innerHTML = `<div class="empty-state"><p class="empty-copy">Could not save note: ${escapeHtml(error.message)}</p></div>`;
  }
}

async function askAI() {
  const input = els.aiInput.value.trim();
  if (!input) {
    els.aiOutput.textContent = "Write a prompt first so the coach has context.";
    return;
  }

  els.aiOutput.textContent = "Thinking through your next best move...";
  try {
    const data = await api("/api/ai/recommend", {
      method: "POST",
      body: JSON.stringify({ input }),
    });
    const suffix =
      data.source === "fallback"
        ? `\n\nUsing fallback guidance. ${data.reason || "The AI provider did not return a usable response."}`
        : "";
    els.aiOutput.textContent = `${data.suggestion || JSON.stringify(data, null, 2)}${suffix}`;
  } catch (error) {
    els.aiOutput.textContent = `AI request failed: ${error.message}`;
  }
}

async function suggestHabit() {
  showBanner("suggestionBanner", "Generating a habit idea...");
  try {
    const data = await api("/api/habits/suggest", {
      method: "POST",
      body: JSON.stringify({ input: "Suggest a healthy habit for a beginner." }),
    });
    const prefix = data.source === "fallback" ? "Fallback suggestion" : "AI Suggestion";
    const reason = data.source === "fallback" && data.reason ? ` (${data.reason})` : "";
    showBanner("suggestionBanner", `${prefix}: ${data.suggestion}${reason}`);
  } catch (error) {
    showBanner("suggestionBanner", `Suggestion failed: ${error.message}`);
  }
}

function showBanner(id, message) {
  const el = document.getElementById(id);
  el.textContent = message;
  el.classList.remove("hidden");
}

function hideBanner(id) {
  document.getElementById(id).classList.add("hidden");
}

function handleDynamicClicks(event) {
  const habitBoostId = event.target.getAttribute("data-habit-boost");
  const taskToggleId = event.target.getAttribute("data-task-toggle");
  const taskDeleteId = event.target.getAttribute("data-task-delete");

  if (habitBoostId) {
    boostHabit(Number(habitBoostId));
  }

  if (taskToggleId) {
    toggleTask(Number(taskToggleId));
  }

  if (taskDeleteId) {
    deleteTask(Number(taskDeleteId));
  }
}

function bindEvents() {
  els.habitForm.addEventListener("submit", addHabit);
  els.taskForm.addEventListener("submit", addTask);
  els.noteForm.addEventListener("submit", addNote);
  els.askAiBtn.addEventListener("click", askAI);
  els.suggestHabitBtn.addEventListener("click", suggestHabit);
  document.body.addEventListener("click", handleDynamicClicks);

  document.querySelectorAll(".prompt-chip").forEach((button) => {
    button.addEventListener("click", () => {
      els.aiInput.value = button.dataset.prompt || "";
      askAI();
    });
  });
}

async function init() {
  setTodayLabel();
  bindEvents();
  await reloadAll();
}

init();
