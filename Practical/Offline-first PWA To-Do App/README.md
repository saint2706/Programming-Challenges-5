# Offline-first PWA To-Do App

A Progressive Web Application (PWA) demonstrating offline-first architecture with IndexedDB storage and Background Sync capabilities.

## Features

- **Offline Support**: Full functionality even without an internet connection
- **IndexedDB Storage**: Client-side data persistence using IndexedDB
- **Background Sync**: Queues changes when offline and syncs when connectivity returns
- **Service Worker**: Caches app shell for instant loading
- **Conflict Resolution**: Handles sync conflicts with last-write-wins strategy

## Files

| File | Description |
|------|-------------|
| `index.html` | Main HTML structure with semantic markup |
| `app.js` | Core application logic, IndexedDB operations, and sync queue management |
| `sw.js` | Service worker for caching and background sync |
| `styles.css` | Responsive styling with mobile-first approach |
| `manifest.json` | PWA manifest for installability |
| `icons/` | App icons for various display sizes |

## How It Works

### Data Flow

1. **Adding Tasks**: Creates task in IndexedDB, queues sync operation
2. **Offline Mode**: All operations stored locally, sync queue builds up
3. **Back Online**: Background sync processes queue, resolves conflicts

### Storage Architecture

- **IndexedDB Stores**:
  - `tasks`: Primary task storage with indexes on status and updatedAt
  - `syncQueue`: Pending operations waiting for network

- **LocalStorage**: Simulated server state for demo purposes

## Running the App

Serve the directory with any static file server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js (npx)
npx serve .

# Using PHP
php -S localhost:8000
```

Then open `http://localhost:8000` in your browser.

## Browser Requirements

- Modern browser with IndexedDB support
- Service Worker support (Chrome, Firefox, Safari, Edge)
- Background Sync API (Chrome, Edge - graceful fallback for others)

## Implementation Notes

- Uses `crypto.randomUUID()` for unique task IDs
- Conflict detection compares `updatedAt` timestamps
- Service worker uses cache-first strategy for app shell
- Responsive design works on mobile and desktop
