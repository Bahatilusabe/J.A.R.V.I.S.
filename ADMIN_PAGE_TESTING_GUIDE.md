# Admin Page Security Testing Guide

**Date**: December 18, 2025  
**Version**: 1.0  
**Purpose**: Validate role-based access control and UI/UX enhancements

---

## 🚀 Quick Start

### Prerequisites

```bash
# Backend running
make run-backend

# Frontend running in separate terminal
cd frontend/web_dashboard && npm run dev
```

### Test Users Available

| Username | Password | Role | Status |
|----------|----------|------|--------|
| `admin` | `admin123` | admin | active |
| `analyst01` | `analyst123` | analyst | active |
| `operator01` | `operator123` | operator | active |

---

## ✅ Test Suite

### 1️⃣ Test: Non-Authenticated User Access

**Objective**: Verify unauthenticated users cannot access admin page

**Steps**:
```
1. Clear browser storage: DevTools → Application → Storage → Clear Site Data
2. Open http://localhost:5173/admin (without login)
3. Observe redirect
4. Check browser console
```

**Expected Results**:
- ✅ Redirected to `/login` page immediately
- ✅ No admin page flash
- ✅ URL shows `/login`
- ✅ Return state preserved in URL
- ✅ No console errors

**Evidence**:
```
Browser console should show NO errors
URL should be: http://localhost:5173/login?from=%2Fadmin
```

---

### 2️⃣ Test: Non-Admin User Access

**Objective**: Verify non-admin authenticated users cannot access admin page

**Steps**:
```
1. Login as analyst01 / analyst123
2. Open http://localhost:5173/admin (direct URL)
3. Observe redirect behavior
4. Check where you land
```

**Expected Results**:
- ✅ Redirected to `/dashboard` page
- ✅ No admin page flash or loading
- ✅ URL shows `/dashboard`
- ✅ "Admin Console" not visible
- ✅ Status bar shows analyst role (not admin)

**Evidence**:
```
URL should be: http://localhost:5173/dashboard
No admin tabs (Features, Keys, Settings, etc.) visible
```

---

### 3️⃣ Test: Admin User Access

**Objective**: Verify admin users can access admin page

**Steps**:
```
1. Login as admin / admin123
2. Navigate to Admin Console (via menu or direct URL)
3. Observe page loads
4. Check all UI elements
```

**Expected Results**:
- ✅ Admin page loads without redirect
- ✅ Sticky navigation bar visible
- ✅ Breadcrumb shows "Dashboard / Admin Console"
- ✅ Admin badge visible (top right: "👤 ADMIN")
- ✅ Quick stats panel displays (4 cards)
- ✅ All tabs accessible (Features, Keys, Settings, Users, Health, Logs)
- ✅ Tab icons visible and correct

**Evidence**:
```
URL: http://localhost:5173/admin
Header shows: "Admin Console" with Shield icon
Admin badge visible in top right
Quick stats: Total Users, Features, System Status, Audit Logs
All tabs clickable
```

**Screenshot Checklist**:
- [ ] Breadcrumb navigation visible
- [ ] Admin badge displayed ("👤 ADMIN")
- [ ] Quick stats cards (4 visible)
- [ ] Tab navigation with icons
- [ ] Users tab content visible

---

### 4️⃣ Test: Quick Stats Dashboard

**Objective**: Verify quick stats display correct data

**Steps**:
```
1. Login as admin
2. Navigate to Admin Console
3. Check quick stats section (below header, above tabs)
4. Verify each metric
```

**Expected Results**:
- ✅ **Total Users** card shows user count
- ✅ **Active Users** card shows active count
- ✅ **Features** card shows enabled/total count
- ✅ **System Status** shows health indicator
- ✅ All cards styled with dark theme
- ✅ Cards responsive on mobile

**Verification**:
```
Total Users: Should match count in Users tab
Active Users: Count of users with status='active'
Features: Count of enabled features
System Status: Shows green (healthy) indicator
```

---

### 5️⃣ Test: Tab Navigation

**Objective**: Verify tab switching works correctly

**Steps**:
```
1. On Admin Console
2. Click each tab: Features, Keys, Settings, Users, Health, Logs
3. Observe content changes
4. Check icons load correctly
```

**Expected Results**:
- ✅ All tabs clickable
- ✅ Icons visible for each tab
- ✅ Content updates when switching tabs
- ✅ Tab highlights when active (blue underline)
- ✅ Smooth transition between tabs
- ✅ Tab icons display correctly (mobile: icon only, desktop: icon + text)

**Icon Verification**:
```
Features → ToggleRight icon
Keys → Lock icon
Settings → Settings/Gear icon
Users → Users/People icon
Health → Server icon
Logs → FileText/Document icon
```

---

### 6️⃣ Test: Users Tab - Statistics Display

**Objective**: Verify user statistics section

**Steps**:
```
1. Click "Users" tab
2. Observe stats section at top
3. Check three stat cards
```

**Expected Results**:
- ✅ **Total Users** card (dark-700 background)
  - Shows total count (e.g., "3")
  - Text uppercase: "TOTAL USERS"
- ✅ **Admins** card (red-400 text)
  - Shows admin count
  - Text uppercase: "ADMINS"
- ✅ **Active** card (green-400 text)
  - Shows active user count
  - Text uppercase: "ACTIVE"

**Values to Check**:
```
If 3 users exist with:
- 1 admin (admin)
- 2 analysts (analyst01, analyst02)
- All active

Results should show:
Total Users: 3
Admins: 1
Active: 3
```

---

### 7️⃣ Test: User List - Role Badges

**Objective**: Verify admin users show distinct badge

**Steps**:
```
1. In Users tab
2. Scroll down to user list
3. Find admin user
4. Check badges
```

**Expected Results**:
- ✅ Admin user (admin) shows:
  - Red badge with text: "ADMIN" + Shield icon
  - Blue "admin" role badge
  - Status badge (● ACTIVE or ○ INACTIVE)
- ✅ Non-admin users show:
  - NO red ADMIN badge
  - Blue role badge (analyst/operator)
  - Status badge
- ✅ All badges styled correctly with borders

**Badge Verification**:
```
ADMIN badge:
- Background: red-900/40
- Text: red-400
- Border: red-800/50
- Icon: Shield (lucide-react)
- Text: "ADMIN"

Role badge (analyst):
- Background: blue-900/30
- Text: blue-400
- Border: blue-800/30

Status badge (active):
- Background: green-900/40
- Text: green-400
- Border: green-800/50
- Symbol: ● (bullet)
```

---

### 8️⃣ Test: User List - Status Indicators

**Objective**: Verify active/inactive status display

**Steps**:
```
1. In Users tab, view user list
2. Check status badges for each user
3. Verify visual differences
```

**Expected Results**:
- ✅ Active users show:
  - Green badge: "● ACTIVE"
  - Green-400 text color
  - Green-900/40 background
- ✅ Inactive users show:
  - Gray badge: "○ INACTIVE"
  - Gray-400 text color
  - Gray-900/40 background
- ✅ Visual distinction clear at a glance

**Verification**:
```
Change a user's status to test (if button available)
Active: ● ACTIVE (green)
Inactive: ○ INACTIVE (gray)
```

---

### 9️⃣ Test: Create User Flow

**Objective**: Verify user creation works with password display

**Steps**:
```
1. In Users tab
2. Click "Add User" button
3. Fill form:
   - Username: testuser01
   - Email: test01@jarvis.local
   - Role: analyst
4. Click "Create User"
5. Observe password modal
```

**Expected Results**:
- ✅ Form visible with input fields
- ✅ Form has gradient background (blue-900/20)
- ✅ Fields have proper styling
- ✅ Create button functional
- ✅ Password modal appears after creation
- ✅ Password shown in modal
- ✅ Copy button works
- ✅ User appears in list with correct badges
- ✅ Temporary password visible only once

**Form Fields**:
```
- Username: textinput
- Email: textinput
- Role: select dropdown (admin/analyst/operator)
- Create User: submit button
```

---

### 🔟 Test: User Deletion

**Objective**: Verify delete button behavior

**Steps**:
```
1. In Users tab, user list
2. Hover over a user card
3. Check for delete button
4. Click delete button
```

**Expected Results**:
- ✅ Delete button appears on hover (not visible by default)
- ✅ Delete button positioned consistently
- ✅ Delete button styled as red/danger button
- ✅ Confirmation modal appears on click
- ✅ Cancel/Confirm options available
- ✅ User removed from list after confirmation
- ✅ Admin user cannot be deleted

**Verification**:
```
Hover over user card → Delete button appears
Click Delete → Confirmation modal
Select "Confirm" → User removed
Try to delete admin → Error message or prevented
```

---

## 🔐 Backend Authentication Tests

### Test 11: Authorization Header Validation

**Objective**: Verify POST /users requires authorization header

**Steps**:
```bash
# Test 1: Request WITHOUT auth header
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test2",
    "email": "test2@example.com",
    "role": "analyst"
  }'

# Test 2: Request WITH auth header
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "username": "test3",
    "email": "test3@example.com",
    "role": "analyst"
  }'
```

**Expected Results**:
- ✅ **Without header**: Returns 401 "Missing authorization header"
- ✅ **With header**: Processes request (logs audit event)
- ✅ Backend logs show audit entries

**Console Output**:
```
# Test 1 result:
{"detail":"Missing authorization header","status_code":401}

# Test 2 result:
Request logged in backend console
```

---

### Test 12: Audit Logging

**Objective**: Verify admin actions are logged

**Steps**:
```
1. Open backend logs/console
2. Create user as admin
3. Check logs for audit entry
4. Try creating user as non-admin
5. Check logs for denied entry
```

**Expected Results**:
- ✅ Backend logs show user creation attempts
- ✅ Request source logged (client IP)
- ✅ Audit trail available for security review
- ✅ Failed attempts also logged

**Log Entry Pattern**:
```
INFO: User creation request from: 127.0.0.1:12345
INFO: New user created: testuser01 (analyst)
```

---

## 📱 Responsive Design Tests

### Test 13: Mobile View (< 640px)

**Objective**: Verify admin page responsive on mobile

**Steps**:
```
1. Open DevTools (F12)
2. Toggle Device Toolbar (mobile view)
3. Set width: 375px (iPhone SE)
4. Navigate to Admin Console as admin
5. Check layout and navigation
```

**Expected Results**:
- ✅ Tab labels hidden (icons only visible)
- ✅ Stats grid stacks vertically (1 column)
- ✅ User cards responsive
- ✅ Buttons clickable without side-scrolling
- ✅ No horizontal overflow
- ✅ Admin badge still visible
- ✅ Breadcrumb text abbreviated if needed

---

### Test 14: Tablet View (640px - 1024px)

**Objective**: Verify admin page responsive on tablet

**Steps**:
```
1. Set viewport width: 768px (iPad)
2. Check layout
3. Verify tab labels visible
4. Check stats grid columns
```

**Expected Results**:
- ✅ Tab labels visible with icons ("Features", "Keys", etc.)
- ✅ Stats grid shows 2 columns
- ✅ Layout optimized for medium screens
- ✅ All content accessible without scrolling

---

### Test 15: Desktop View (> 1024px)

**Objective**: Verify admin page optimal on desktop

**Steps**:
```
1. Set viewport width: 1920px (full desktop)
2. Check layout
3. Verify full width usage
4. Check max-width container
```

**Expected Results**:
- ✅ Stats grid shows 4 columns
- ✅ Content centered with max-width (7xl)
- ✅ All tabs visible with full labels
- ✅ User cards display at full width
- ✅ Optimal visual hierarchy

---

## 🎯 Integration Tests

### Test 16: Login → Admin Flow

**Objective**: Verify complete flow from login to admin dashboard

**Steps**:
```
1. Open http://localhost:5173 (home/login)
2. Login as admin / admin123
3. Click "Admin" link in navigation (or go to /admin)
4. Observe admin console
```

**Expected Results**:
- ✅ Login succeeds
- ✅ Redirected to dashboard
- ✅ Can navigate to admin console
- ✅ Admin console loads without delay
- ✅ All features accessible

---

### Test 17: Non-Admin → Redirect Flow

**Objective**: Verify non-admin redirect experience

**Steps**:
```
1. Login as analyst01 / analyst123
2. Try to navigate to admin (via URL or menu)
3. Observe redirect
4. Check landing page
```

**Expected Results**:
- ✅ Redirected to /dashboard
- ✅ Stays logged in (not logged out)
- ✅ Can still access analyst features
- ✅ Admin menu item not visible (if role-filtered)

---

### Test 18: Session Persistence

**Objective**: Verify admin session persists across page reloads

**Steps**:
```
1. Login as admin
2. Navigate to admin console
3. Press F5 (page reload)
4. Check if still on admin page
```

**Expected Results**:
- ✅ Admin console still visible
- ✅ Auth token persisted
- ✅ User data preserved
- ✅ No redirect to login

---

## 🐛 Error Scenario Tests

### Test 19: Token Expiration

**Objective**: Verify behavior with expired token

**Steps**:
```
1. Login as admin
2. Clear localStorage manually (DevTools)
3. Refresh page
4. Try to access admin console
```

**Expected Results**:
- ✅ Redirected to login
- ✅ Clear error message or silent redirect
- ✅ Can login again

---

### Test 20: Missing User Data

**Objective**: Verify graceful handling of missing user data

**Steps**:
```
1. Open DevTools → Application
2. Edit localStorage USER_KEY to remove role
3. Navigate to admin console
4. Check handling
```

**Expected Results**:
- ✅ Redirected to /dashboard
- ✅ No console errors
- ✅ Graceful fallback

---

## 📊 Test Results Matrix

| Test # | Description | Status | Notes |
|--------|-------------|--------|-------|
| 1 | Non-authenticated access | ⏳ | Redirect to login |
| 2 | Non-admin access | ⏳ | Redirect to dashboard |
| 3 | Admin access | ⏳ | Console loads |
| 4 | Quick stats display | ⏳ | Correct values |
| 5 | Tab navigation | ⏳ | All tabs work |
| 6 | User stats section | ⏳ | Correct counts |
| 7 | Role badges | ⏳ | Admin badge shows |
| 8 | Status indicators | ⏳ | Active/Inactive |
| 9 | Create user flow | ⏳ | Password modal |
| 10 | User deletion | ⏳ | Delete on hover |
| 11 | Auth header validation | ⏳ | 401 without auth |
| 12 | Audit logging | ⏳ | Actions logged |
| 13 | Mobile responsive | ⏳ | Icons only |
| 14 | Tablet responsive | ⏳ | 2 columns |
| 15 | Desktop responsive | ⏳ | 4 columns |
| 16 | Login→Admin flow | ⏳ | Complete flow |
| 17 | Non-admin redirect | ⏳ | Redirect works |
| 18 | Session persistence | ⏳ | Survives reload |
| 19 | Token expiration | ⏳ | Redirect to login |
| 20 | Missing user data | ⏳ | Graceful handling |

---

## ✅ Sign-Off

**All tests completed**: [ ] Yes / [ ] No

**All tests passed**: [ ] Yes / [ ] No

**Issues found**: [ ] None / [ ] See below

**Notes**:
```
[Space for test notes and issues]
```

**Tested by**: ___________________  
**Date**: ___________________  
**Version**: 1.0

---

## 🔗 Resources

- Frontend: `frontend/web_dashboard/src/components/AdminRoute.tsx`
- Backend: `backend/api/routes/admin.py`
- Auth Service: `frontend/web_dashboard/src/services/auth.service.ts`
- Admin Page: `frontend/web_dashboard/src/pages/Admin.tsx`

---

**End of Testing Guide**
