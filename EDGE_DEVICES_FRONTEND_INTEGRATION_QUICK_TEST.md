# Edge Devices - Frontend Integration Quick Test Guide

**Status**: ✅ Frontend Integrated with Backend  
**Date**: December 16, 2025  

---

## 🚀 QUICK START (2 Minutes)

### Terminal 1: Start Backend
```bash
cd /Users/mac/Desktop/J.A.R.V.I.S.
make run-backend
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Start Frontend
```bash
cd /Users/mac/Desktop/J.A.R.V.I.S./frontend/web_dashboard
npm run dev
```

**Expected Output**:
```
  ➜  Local:   http://localhost:5173/
```

### Browser: Test the Page
1. Open: **http://localhost:5173**
2. Navigate to: **Edge Device Management**
3. Open DevTools: **F12 → Network Tab**

---

## ✅ 5-MINUTE VERIFICATION

### ✓ Test 1: Devices Load
- [ ] See 4 device cards on page load
- [ ] Grid/List/Security tabs visible
- [ ] Stats show: 4 Total, 3 Secure, 100% Binding

**Network Check**: Look for `GET /api/edge-devices` call

---

### ✓ Test 2: Select Device
- [ ] Click on "Atlas-500-East" card
- [ ] Right panel appears with device details
- [ ] Chart shows 20 data points (history)

**Network Check**: Look for `GET /api/edge-devices/edge-001` call

---

### ✓ Test 3: Remote Command
- [ ] In right panel, find action buttons
- [ ] Click "Status" or "Reboot" button
- [ ] Button shows loading state
- [ ] Device list refreshes

**Network Check**: Look for `POST /api/edge-devices/edge-001/command` call

---

### ✓ Test 4: List View
- [ ] Click "List View" tab
- [ ] See table with all 4 devices
- [ ] Status colors correct (green=online, yellow=degraded)

---

### ✓ Test 5: Security View
- [ ] Click "Security" tab
- [ ] See security metrics dashboard
- [ ] Stats match grid view

---

## 🔍 WHAT TO LOOK FOR IN NETWORK TAB

### Working API Calls (Expected)

✅ `GET /api/edge-devices` - Returns 4 devices + metrics  
✅ `GET /api/edge-devices/edge-001` - Returns device + 20-entry history  
✅ `POST /api/edge-devices/edge-001/command` - Returns command result  

### Console (Should be Clean)

✅ No red errors  
✅ No 404s for API endpoints  
✅ Green messages from API calls  

### If Something is Wrong

❌ **Devices not loading?**
- Check backend is running on port 8000
- Check Network tab for 404 errors
- Console should show fallback to demo data

❌ **Commands not executing?**
- Check POST request goes to correct endpoint
- Check request body has `{"command": "..."}`
- Check Content-Type header is set

❌ **History not showing?**
- Check GET request includes device ID
- Verify response has `history` array with 20 entries

---

## 📊 EXPECTED DATA

### When Backend is Working

**Grid View**:
```
Edge-001: Atlas-500-East (Online)    CPU: 45%  MEM: 62%  TEMP: 52°C
Edge-002: Kunpeng-920-Central (Online) CPU: 38%  MEM: 54%  TEMP: 48°C  
Edge-003: Atlas-300i-West (Online)    CPU: 72%  MEM: 78%  TEMP: 68°C
Edge-004: HiSilicon-Echo-South (Degraded) CPU: 89% MEM: 92% TEMP: 76°C
```

**Metrics**:
```
Total Devices: 4
Secure Devices: 3
Device Binding: 100%
Encryption: 4
```

### When API is Down (Fallback)

Same data appears automatically from demo data. Page still works!

---

## 🐛 DEBUGGING CHECKLIST

- [ ] Backend running? `ps aux | grep uvicorn`
- [ ] Frontend running? Check terminal shows `Local: http://localhost:5173`
- [ ] Correct URL? `http://127.0.0.1:8000` (not `localhost:8000`)
- [ ] Network tab open? (F12 → Network)
- [ ] No CORS errors? Check console
- [ ] API responses valid JSON? Check Network → Response tab
- [ ] Status codes 200? (Not 404, 500, etc.)

---

## 📋 THREE HANDLERS UPDATED

### 1️⃣ loadEdgeDevices()
**What**: Fetches all edge devices  
**When**: Page load + every 5 seconds  
**API**: `GET /api/edge-devices`  
**Fallback**: Demo data (4 devices)  

### 2️⃣ handleSelectDevice()
**What**: Fetches device history  
**When**: Click device card  
**API**: `GET /api/edge-devices/{id}`  
**Fallback**: Generated demo history (20 entries)  

### 3️⃣ handleRemoteCommand()
**What**: Executes remote command  
**When**: Click Status/Reboot button  
**API**: `POST /api/edge-devices/{id}/command`  
**Fallback**: Mock execution (1 second delay)  

---

## ✨ SUCCESS INDICATORS

✅ **Page loads** without errors  
✅ **4 devices appear** on first load  
✅ **Metrics display** correctly  
✅ **Click device** → history loads  
✅ **Click button** → command executes  
✅ **Network tab** shows API calls  
✅ **Console** shows no red errors  
✅ **All 3 views work** (Grid, List, Security)  
✅ **Filters work** (platform, status, TEE)  
✅ **Auto-refresh** every 5 seconds  

---

## 🎯 QUICK CURL TESTS

### Test Backend Directly

```bash
# Test 1: Get all devices
curl http://127.0.0.1:8000/api/edge-devices

# Test 2: Get specific device
curl http://127.0.0.1:8000/api/edge-devices/edge-001

# Test 3: Execute command
curl -X POST http://127.0.0.1:8000/api/edge-devices/edge-001/command \
  -H "Content-Type: application/json" \
  -d '{"command":"status"}'
```

**All should return 200 + JSON**

---

## ⏱️ TESTING TIMELINE

| Task | Time |
|------|------|
| Start servers | 1 min |
| Test page load | 1 min |
| Test all views | 2 min |
| Test device select | 1 min |
| Test commands | 2 min |
| Verify network calls | 1 min |
| Check fallback | 2 min |
| **Total** | **10 min** |

---

## 📞 SUPPORT

**For Full Testing Guide**: See `EDGE_DEVICES_FRONTEND_INTEGRATION_COMPLETE.md`

**For API Specs**: See `EDGE_DEVICES_PAGE_100_PERCENT_INTEGRATION_COMPLETE.md`

**For Backend Details**: See `EDGE_DEVICES_BACKEND_INTEGRATION_COMPLETE.md`

---

## ✅ SIGN-OFF

**Frontend**: ✅ Integrated  
**Backend**: ✅ Running  
**Testing**: ✅ Ready  
**Status**: ✅ GO!  

**Start testing now!** 🚀
