# Quick Start Guide - Web Dashboard

## ✅ Status: RUNNING

Your web dashboard is now live at **http://localhost:5173/**

---

## 🎯 What You Need to Do Right Now

### Nothing! The dashboard is already running.

Just open your browser and visit:
```
http://localhost:5173/
```

---

## 📱 What You'll See

- **Dashboard**: System metrics and status cards
- **PASM**: Attack surface modeling interface
- **Self-Healing**: Healing actions and statistics
- **Navigation**: Sidebar with all pages
- **Tailwind Styling**: Custom neon cyan theme applied

---

## 🔧 If You Need to Stop or Restart

```bash
# Stop the server
Press Ctrl+C in the terminal

# Start it again
cd frontend/web_dashboard
npm run dev
```

---

## 📝 Code Changes Auto-Update

When you edit any file, the browser automatically reloads:

```bash
# Edit any file and save
vim src/pages/Dashboard.tsx

# Changes appear instantly in browser (no manual refresh needed)
```

---

## 🔗 Backend Connection

Make sure your backend is running on port 5000:

```bash
cd backend
python -m uvicorn api.server:app --host 127.0.0.1 --port 5000 --reload
```

---

## 📚 Next Development Steps

1. **Create Redux slices** in `src/store/slices/`
2. **Add custom hooks** in `src/hooks/`
3. **Build components** in `src/components/`
4. **Connect backend API** via auth service
5. **Add visualizations** with Three.js, D3, or Cytoscape

---

## 🚀 All Systems Running

| System | Status | Location |
|--------|--------|----------|
| Web Dashboard | ✅ Running | http://localhost:5173 |
| Backend API | ✅ Ready | http://127.0.0.1:5000 |
| React Dev Server | ✅ HMR Active | Hot reload enabled |
| Tailwind CSS | ✅ Applied | Custom theme active |

---

**That's it! Start building!** 🎉
