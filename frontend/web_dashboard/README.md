# Frontend (web_dashboard)

This is the Vite + React frontend for the JARVIS admin console and dashboard.

Quick start

1. Change into the frontend folder:

       cd frontend/web_dashboard

2. Install dependencies:

       npm install

3. Start the dev server:

       npm run dev

Default dev server
- Vite dev server runs on port 5173 by default. Open `http://localhost:5173` in your browser.
- Frontend expects the backend API at `http://127.0.0.1:8000` by default. You can change this in the client code or via a proxy setup.

Common issues
- `vite: command not found` — run `npm install` in `frontend/web_dashboard` (it will create `node_modules/.bin/vite`).
- Docker-based scripts in `package.json` (`docker:build`, `docker:run`) require Docker CLI installed locally.

Wiring to backend
- The frontend uses an `APIClient` (axios) configured to target `http://127.0.0.1:8000` by default. The dashboard UI already calls endpoints such as `/api/self_healing/trigger`, `/api/forensics/export`, and others. Ensure the backend is running on port 8000 when testing end-to-end.
