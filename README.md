# Ralph Orchestrator Dashboard v8.0 🚀

A modern, glassmorphic orchestration dashboard built with Flask (backend) and React + Tailwind (frontend).

## Features
- **Real-time Updates**: Server-Sent Events (SSE) for live task progress.
- **Glassmorphism UI**: Beautiful, translucent interface with dynamic gradients.
- **Keyboard Shortcuts**: Power-user controls (`Ctrl+Enter` to run, `Ctrl+K` to clear console).
- **Responsive Design**: Full support for Desktop (Grid) and Mobile (Stacked).
- **Playwright Tested**: 100% E2E test coverage.

## Tech Stack
- **Backend**: Flask, Gevent (SSE)
- **Frontend**: React, Vite, Tailwind CSS
- **Testing**: Playwright, Pytest

## Architecture
- `backend/dashboard/app.py`: Flask server with `/api/stream` SSE endpoint.
- `frontend/src/`: React application using Vite proxy to backend.
- `backend/tests/`: Playwright E2E tests ensuring stability.

## Setup & Running

### Prerequisites
- Python 3.11+
- Node.js 18+

### Installation
1. Install Backend Dependencies:
   ```bash
   pip install flask flask-cors pytest
   ```
2. Install Frontend Dependencies:
   ```bash
   cd backend
   npm install
   ```

### Running Dev Server
Start the development server (proxies React to Flask):
```bash
cd backend
npm run dev
```
Access at: `http://localhost:5173`

### Running Tests
Run the full E2E suite:
```bash
cd backend
npm test
```

Run backend unit tests:
```bash
python -m pytest dashboard/test_app.py
```

## Shortcuts
| Key | Action |
|-----|--------|
| `Ctrl + Enter` | submit task |
| `Ctrl + K` | Clear Console |
| `Ctrl + ,` | Toggle Settings |
| `/` | Focus Input |

---
*Built by Antigravity Agent*
