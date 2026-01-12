import "./style.css";
import Sortable from "sortablejs";

// State
let todos = JSON.parse(localStorage.getItem("todos")) || [];
let filter = "all";

// DOM Elements
const app = document.getElementById("app");

// Render App
function render() {
  app.innerHTML = `
        <div class="container">
            <header class="header">
                <h1>📝 Todo App</h1>
                <p class="subtitle">Organize your tasks efficiently</p>
            </header>

            <div class="add-todo">
                <input type="text" id="todoInput" placeholder="What needs to be done?" />
                <select id="prioritySelect">
                    <option value="low">Low Priority</option>
                    <option value="medium" selected>Medium Priority</option>
                    <option value="high">High Priority</option>
                </select>
                <input type="date" id="dueDateInput" />
                <button id="addBtn">Add Todo</button>
            </div>

            <div class="filters">
                <button class="filter-btn ${filter === "all" ? "active" : ""}" data-filter="all">
                    All (${todos.length})
                </button>
                <button class="filter-btn ${filter === "active" ? "active" : ""}" data-filter="active">
                    Active (${todos.filter((t) => !t.completed).length})
                </button>
                <button class="filter-btn ${filter === "completed" ? "active" : ""}" data-filter="completed">
                    Completed (${todos.filter((t) => t.completed).length})
                </button>
            </div>

            <ul class="todo-list" id="todoList">
                ${getFilteredTodos().map(renderTodo).join("")}
            </ul>

            ${
              todos.length > 0
                ? `
                <div class="footer">
                    <span>${todos.filter((t) => !t.completed).length} items left</span>
                    <button id="clearCompleted">Clear Completed</button>
                </div>
            `
                : ""
            }
        </div>
    `;

  attachEventListeners();
  initSortable();
}

// Render individual todo
function renderTodo(todo) {
  const priorityClass = `priority-${todo.priority}`;
  const completedClass = todo.completed ? "completed" : "";
  const overdueClass =
    todo.dueDate && new Date(todo.dueDate) < new Date() && !todo.completed
      ? "overdue"
      : "";

  return `
        <li class="todo-item ${completedClass} ${priorityClass} ${overdueClass}" data-id="${todo.id}">
            <div class="todo-content">
                <input type="checkbox" ${todo.completed ? "checked" : ""} onchange="toggleTodo('${todo.id}')" />
                <div class="todo-details">
                    <span class="todo-text">${todo.text}</span>
                    ${todo.dueDate ? `<span class="due-date">📅 ${formatDate(todo.dueDate)}</span>` : ""}
                </div>
            </div>
            <div class="todo-actions">
                <button class="btn-icon" onclick="editTodo('${todo.id}')" title="Edit">✏️</button>
                <button class="btn-icon" onclick="deleteTodo('${todo.id}')" title="Delete">🗑️</button>
                <span class="drag-handle">⋮⋮</span>
            </div>
        </li>
    `;
}

// Attach event listeners
function attachEventListeners() {
  const addBtn = document.getElementById("addBtn");
  const todoInput = document.getElementById("todoInput");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const clearBtn = document.getElementById("clearCompleted");

  addBtn?.addEventListener("click", addTodo);
  todoInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") addTodo();
  });
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => setFilter(btn.dataset.filter));
  });
  clearBtn?.addEventListener("click", clearCompleted);
}

// Initialize drag and drop
function initSortable() {
  const list = document.getElementById("todoList");
  if (list) {
    new Sortable(list, {
      handle: ".drag-handle",
      animation: 150,
      onEnd: (evt) => {
        const item = todos.splice(evt.oldIndex, 1)[0];
        todos.splice(evt.newIndex, 0, item);
        saveTodos();
      },
    });
  }
}

// Add todo
function addTodo() {
  const input = document.getElementById("todoInput");
  const prioritySelect = document.getElementById("prioritySelect");
  const dueDateInput = document.getElementById("dueDateInput");

  const text = input.value.trim();
  if (!text) return;

  const todo = {
    id: Date.now().toString(),
    text,
    completed: false,
    priority: prioritySelect.value,
    dueDate: dueDateInput.value || null,
    createdAt: new Date().toISOString(),
  };

  todos.unshift(todo);
  saveTodos();

  input.value = "";
  dueDateInput.value = "";
  render();
}

// Toggle todo
window.toggleTodo = (id) => {
  const todo = todos.find((t) => t.id === id);
  if (todo) {
    todo.completed = !todo.completed;
    saveTodos();
    render();
  }
};

// Edit todo
window.editTodo = (id) => {
  const todo = todos.find((t) => t.id === id);
  if (!todo) return;

  const newText = prompt("Edit todo:", todo.text);
  if (newText && newText.trim()) {
    todo.text = newText.trim();
    saveTodos();
    render();
  }
};

// Delete todo
window.deleteTodo = (id) => {
  if (confirm("Delete this todo?")) {
    todos = todos.filter((t) => t.id !== id);
    saveTodos();
    render();
  }
};

// Set filter
function setFilter(newFilter) {
  filter = newFilter;
  render();
}

// Clear completed
function clearCompleted() {
  todos = todos.filter((t) => !t.completed);
  saveTodos();
  render();
}

// Get filtered todos
function getFilteredTodos() {
  if (filter === "active") return todos.filter((t) => !t.completed);
  if (filter === "completed") return todos.filter((t) => t.completed);
  return todos;
}

// Save to localStorage
function saveTodos() {
  localStorage.setItem("todos", JSON.stringify(todos));
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  if (date.toDateString() === today.toDateString()) return "Today";
  if (date.toDateString() === tomorrow.toDateString()) return "Tomorrow";
  return date.toLocaleDateString();
}

// Initial render
render();
