const DB_NAME = 'todo-pwa';
const DB_VERSION = 1;
const TASK_STORE = 'tasks';
const QUEUE_STORE = 'syncQueue';
const SERVER_STATE_KEY = 'todo-pwa-server';

const statusEl = document.getElementById('connection-status');
const form = document.getElementById('task-form');
const taskInput = document.getElementById('task-title');
const listEl = document.getElementById('task-list');
const emptyStateEl = document.getElementById('empty-state');
const queueIndicator = document.getElementById('queue-indicator');
const conflictPanel = document.getElementById('conflict-panel');
const conflictLog = document.getElementById('conflict-log');

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(TASK_STORE)) {
        const taskStore = db.createObjectStore(TASK_STORE, { keyPath: 'id' });
        taskStore.createIndex('status', 'status');
        taskStore.createIndex('updatedAt', 'updatedAt');
      }
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function withStore(storeName, mode, fn) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, mode);
    const store = tx.objectStore(storeName);
    const request = fn(store, tx);
    tx.oncomplete = () =>
      resolve(request && typeof request === 'object' && 'result' in request ? request.result : request);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

async function getAll(storeName) {
  return withStore(storeName, 'readonly', (store) => store.getAll());
}

async function getTask(id) {
  return withStore(TASK_STORE, 'readonly', (store) => store.get(id));
}

async function saveTask(task) {
  return withStore(TASK_STORE, 'readwrite', (store) => store.put(task));
}

async function deleteTaskFromDB(id) {
  return withStore(TASK_STORE, 'readwrite', (store) => store.delete(id));
}

async function enqueue(action, payload) {
  const entry = {
    id: crypto.randomUUID(),
    action,
    taskId: payload.id,
    payload,
    baseUpdatedAt: payload.updatedAt,
    queuedAt: Date.now(),
  };
  await withStore(QUEUE_STORE, 'readwrite', (store) => store.put(entry));
  updateQueueIndicator();
  requestBackgroundSync();
  return entry;
}

async function dequeue(id) {
  return withStore(QUEUE_STORE, 'readwrite', (store) => store.delete(id));
}

async function getQueue() {
  return getAll(QUEUE_STORE);
}

function loadServerTasks() {
  try {
    const stored = localStorage.getItem(SERVER_STATE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (err) {
    console.warn('Falling back to empty server state', err);
    return [];
  }
}

function persistServerTasks(tasks) {
  localStorage.setItem(SERVER_STATE_KEY, JSON.stringify(tasks));
}

function formatDate(ts) {
  return new Intl.DateTimeFormat([], { dateStyle: 'medium', timeStyle: 'short' }).format(ts);
}

async function requestBackgroundSync() {
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    try {
      const reg = await navigator.serviceWorker.ready;
      await reg.sync.register('sync-tasks');
      console.log('Background sync registered');
    } catch (err) {
      console.warn('Background sync registration failed', err);
    }
  }
}

async function addTask(title) {
  const now = Date.now();
  const task = {
    id: crypto.randomUUID(),
    title: title.trim(),
    status: 'pending',
    createdAt: now,
    updatedAt: now,
    lastSyncedAt: null,
    syncState: navigator.onLine ? 'synced' : 'pending',
  };
  await saveTask(task);
  await enqueue('create', task);
  renderTasks();
  processQueue();
}

async function updateTask(id, updates) {
  const existing = await getTask(id);
  if (!existing) return;
  const updated = {
    ...existing,
    ...updates,
    updatedAt: Date.now(),
    syncState: navigator.onLine ? 'synced' : 'pending',
  };
  await saveTask(updated);
  await enqueue('update', updated);
  renderTasks();
  processQueue();
}

async function deleteTask(id) {
  const existing = await getTask(id);
  if (!existing) return;
  await deleteTaskFromDB(id);
  await enqueue('delete', existing);
  renderTasks();
  processQueue();
}

function setStatus(isOnline) {
  statusEl.textContent = isOnline ? 'Online - syncing changes' : 'Offline - changes will sync later';
  statusEl.classList.toggle('online', isOnline);
  statusEl.classList.toggle('offline', !isOnline);
}

function renderConflict(message) {
  conflictPanel.hidden = false;
  const li = document.createElement('li');
  li.textContent = message;
  conflictLog.prepend(li);
}

async function syncFromServer() {
  const serverTasks = loadServerTasks();
  const localTasks = await getAll(TASK_STORE);
  const serverIds = new Set(serverTasks.map((task) => task.id));

  for (const task of serverTasks) {
    const normalized = {
      ...task,
      lastSyncedAt: task.lastSyncedAt ?? task.updatedAt,
      syncState: 'synced',
    };
    await saveTask(normalized);
  }

  for (const task of localTasks) {
    if (!serverIds.has(task.id)) {
      await deleteTaskFromDB(task.id);
    }
  }

  await renderTasks();
}

async function renderTasks() {
  const tasks = await getAll(TASK_STORE);
  tasks.sort((a, b) => b.updatedAt - a.updatedAt);
  listEl.innerHTML = '';
  if (!tasks.length) {
    emptyStateEl.hidden = false;
    return;
  }
  emptyStateEl.hidden = true;
  tasks.forEach((task) => {
    const li = document.createElement('li');
    li.className = 'task';
    const info = document.createElement('div');
    info.className = 'task-info';
    const title = document.createElement('div');
    title.className = 'task-title';
    title.textContent = task.title;
    info.append(title);
    const meta = document.createElement('div');
    meta.className = 'task-meta';
    meta.textContent = `Updated ${formatDate(task.updatedAt)}`;
    if (task.lastSyncedAt) {
      const synced = document.createElement('span');
      synced.textContent = `Synced ${formatDate(task.lastSyncedAt)}`;
      meta.append(' · ', synced);
    }
    info.append(meta);

    const actions = document.createElement('div');
    actions.className = 'task-actions';

    const statusPill = document.createElement('span');
    statusPill.className = `status-pill ${task.syncState === 'pending' ? 'syncing' : task.status === 'completed' ? 'completed' : 'pending'}`;
    statusPill.textContent = task.syncState === 'pending' ? 'Pending sync' : task.status === 'completed' ? 'Completed' : 'Open';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'btn-ghost';
    toggleBtn.textContent = task.status === 'completed' ? 'Mark open' : 'Complete';
    toggleBtn.addEventListener('click', () => updateTask(task.id, { status: task.status === 'completed' ? 'pending' : 'completed' }));

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-ghost btn-danger';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', () => deleteTask(task.id));

    actions.append(statusPill, toggleBtn, deleteBtn);

    li.append(info, actions);
    listEl.append(li);
  });
}

async function updateQueueIndicator() {
  const queue = await getQueue();
  queueIndicator.hidden = queue.length === 0;
  if (!queueIndicator.hidden) {
    queueIndicator.textContent = `${queue.length} item${queue.length === 1 ? '' : 's'} pending sync`;
  }
}

async function processQueue() {
  if (!navigator.onLine) return;
  const queue = await getQueue();
  if (!queue.length) return;
  let serverTasks = loadServerTasks();

  for (const entry of queue) {
    try {
      const serverIndex = serverTasks.findIndex((task) => task.id === entry.taskId);
      const serverTask = serverIndex >= 0 ? serverTasks[serverIndex] : null;
      const hasServerConflict =
        entry.action !== 'delete' && serverTask && serverTask.updatedAt > entry.baseUpdatedAt;

      if (hasServerConflict) {
        await dequeue(entry.id);
        renderConflict(
          `Task "${serverTask.title}" kept the server copy because it was updated elsewhere.`
        );
        continue;
      }

      if (entry.action === 'delete') {
        if (serverIndex >= 0) {
          serverTasks.splice(serverIndex, 1);
        }
        await dequeue(entry.id);
        continue;
      }

      const syncedTask = {
        ...entry.payload,
        lastSyncedAt: Date.now(),
        syncState: 'synced',
      };

      if (serverIndex >= 0) {
        serverTasks[serverIndex] = syncedTask;
      } else {
        serverTasks.push(syncedTask);
      }
      await dequeue(entry.id);
    } catch (err) {
      console.warn('Failed processing queue entry; will retry later', err);
    }
  }

  persistServerTasks(serverTasks);
  await syncFromServer();
  updateQueueIndicator();
}

async function bootstrap() {
  await openDB();
  setStatus(navigator.onLine);
  await syncFromServer();
  await updateQueueIndicator();
  processQueue();

  window.addEventListener('online', () => {
    setStatus(true);
    processQueue();
  });
  window.addEventListener('offline', () => setStatus(false));

  if ('serviceWorker' in navigator) {
    try {
      const reg = await navigator.serviceWorker.register('sw.js');
      console.log('Service worker registered', reg);
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data === 'sync-tasks') {
          processQueue();
        }
      });
      if ('SyncManager' in window) {
        reg.addEventListener('updatefound', () => console.log('SW update found'));
      }
    } catch (err) {
      console.error('SW registration failed', err);
    }
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const title = taskInput.value.trim();
  if (!title) return;
  addTask(title);
  form.reset();
  taskInput.focus();
});

bootstrap();
