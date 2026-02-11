# Self-Healing Monitor Enhancement Guide

## Overview

I've created **two enhanced versions** of your self-healing monitor:

1. **React Web Version** (`frontend/web_dashboard/pages/self-healing-monitor.tsx`)
2. **Flutter Mobile Version** (`frontend/mobile_app/lib/screens/self_healing_monitor_enhanced.dart`)

Both versions include significant improvements over the original implementation.

---

## ✨ Key Improvements

### React Web Version

**State Management:**

- ✅ Separate queries for metrics and actions with independent polling
- ✅ Manual refresh capability
- ✅ Auto-refresh toggle with configurable intervals
- ✅ Improved error handling with retry logic
- ✅ Stale time optimization (2s) for UI responsiveness

**UI/UX Enhancements:**

- ✅ Tab-based navigation (Overview, Agents, Timeline, Analytics)
- ✅ Status cards with visual progress indicators
- ✅ Color-coded agent status indicators
- ✅ Expandable action items in timeline
- ✅ Responsive grid layouts
- ✅ Better error state handling
- ✅ Loading states with skeletons

**Data Presentation:**

- ✅ 4-card dashboard overview (System Health, RL Confidence, Success Rate, Recovery Rate)
- ✅ Latest action card with impact details
- ✅ Agent selector with individual metrics
- ✅ Performance analytics tab
- ✅ Action timeline with expandable details
- ✅ Recovery action execution panel

**Features:**

- ✅ Real-time metrics polling (3s interval)
- ✅ Manual refresh with toast notifications
- ✅ Action execution with detailed feedback
- ✅ Automatic error recovery with exponential backoff
- ✅ Improved query invalidation

### Flutter Mobile Version

**Architecture:**

- ✅ Riverpod state management (async providers)
- ✅ ConsumerStatefulWidget for optimal performance
- ✅ Separation of concerns with focused builders
- ✅ Memoized data providers with realistic mock data

**UI Components:**

- ✅ Status cards with color-coded metrics
- ✅ Agent selector with selection indicators
- ✅ Timeline view with expandable details
- ✅ Analytics dashboard with performance charts
- ✅ Recovery action buttons
- ✅ Modern glass morphism effects

**State Management:**

- ✅ Selected agent provider
- ✅ Auto-refresh toggle
- ✅ Active tab tracking
- ✅ Expandable action tracking
- ✅ Async data loading with proper error handling

**Mobile Optimizations:**

- ✅ Responsive layouts
- ✅ Touch-friendly button sizes
- ✅ Scrollable content with SafeArea
- ✅ Proper spacing and padding
- ✅ Loading indicators
- ✅ Haptic feedback ready

---

## 📊 React Web - Feature Breakdown

**Overview Tab Layout:**

- Dashboard (4 Key Metrics): System Health (94%), RL Confidence (88%), Success Rate (95%), Recovery Rate (92%)
- Latest Recovery Action: Action Type, Target System, Confidence Score, Impact Details
- Agent Selector: List of Active Agents, Confidence Metrics, Accuracy Ratings
- Recovery Actions Panel: Isolation, Remediation, Policy Update, Rollback
- Recent Actions Timeline: (5 most recent) Expandable details per action

**Agents Tab Layout:**

- Selected Agent Details: Accuracy, Confidence, Actions Taken, Success Rate, Learning Progress

**Timeline Tab Layout:**

- Action Timeline (scrollable): Action Type, Target System, Confidence, Result Status, Timestamp

**Analytics Tab Layout:**

- Performance Analysis: Agent Performance Charts, Action Outcomes Stats

---

## 📱 Flutter Mobile - Feature Breakdown

**Overview Tab Layout:**

- Status Cards (4 metrics): System Health, RL Confidence, Success Rate, Recovery Rate
- Latest Action Card: Action details, Confidence score, Status badge
- Agent Selector: Agent list, Individual metrics, Selection indicator
- Recovery Actions Grid: Isolate Threat, Remediate System, Update Policy, Rollback Changes

**Agents Tab Layout:**

- Selected Agent Details: Agent name, Accuracy, Confidence, Actions taken, Success rate, Learning progress bar

**Timeline Tab Layout:**

- Action Timeline (scrollable): Action indicator (green for latest), Action details, Confidence badge, Result status, Expandable impact details

**Analytics Tab Layout:**

- Agent Performance Analysis: Performance bars for each agent

## 🔄 Integration Instructions

### Web Dashboard

**1. Replace in your project:**

```bash
cp frontend/web_dashboard/pages/self-healing-monitor.tsx \
   /path/to/your/web-dashboard/pages/
```

**2. Ensure dependencies are installed:**

```bash
npm install @tanstack/react-query lucide-react
```

**3. Verify API endpoints:**

```typescript
// The component expects these endpoints:
GET  /api/self-healing/metrics
GET  /api/self-healing/actions
POST /api/self-healing/execute
```

**4. Update your routing:**

```typescript
import SelfHealingMonitorPage from '@/pages/self-healing-monitor';

// In your router
{
  path: '/self-healing',
  element: <SelfHealingMonitorPage />
}
```

### Mobile Application

Step 1: Create the file

```bash
touch frontend/mobile_app/lib/screens/self_healing_monitor_enhanced.dart
```

Step 2: Copy the content from the provided file

Step 3: Add to your routing in main.dart

```dart
import 'screens/self_healing_monitor_enhanced.dart';

// In your routes map:
'/self-healing-enhanced': (c) => const SelfHealingMonitorScreen(),
```

**4. Ensure dependencies:**

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.4.0
  intl: ^0.19.0  # For date formatting
```

**5. Update navigation to include the new screen:**

```dart
// In your MobileShell or navigation
ElevatedButton(
  onPressed: () => Navigator.pushNamed(context, '/self-healing-enhanced'),
  child: const Text('Self-Healing Monitor'),
)
```

## 📋 API Requirements

### Metrics Endpoint

**GET `/api/self-healing/metrics`**

Response:

```json
{
  "agents": {
    "recovery_coordinator": {
      "accuracy": 0.94,
      "confidence": 0.88,
      "actions_taken": 42,
      "success_rate": 0.96,
      "learning_progress": 0.87,
      "status": "active",
      "performance_score": 0.91,
      "error_count": 2
    },
    "threat_analyzer": { },
    "policy_engine": { }
  },
  "overall_confidence": 0.88,
  "overall_success_rate": 0.95,
  "system_health": 94,
  "recovery_rate": 0.92,
  "avg_response_time": 1.8,
  "total_actions_today": 115
}
```

### Actions Endpoint

**GET `/api/self-healing/actions`**

Response:

```json
{
  "recent_actions": [
    {
      "id": "action_001",
      "type": "isolation",
      "target": "workstation-42",
      "confidence": 0.92,
      "result": "success",
      "timestamp": "2025-12-05T10:35:00Z",
      "impact": "Isolated compromised endpoint..."
    }
  ],
  "total_actions_today": 115,
  "success_rate": 0.95,
  "failed_actions": 5
}
```

### Execute Endpoint

**POST `/api/self-healing/execute`**

Request:

```json
{
  "type": "isolation|remediation|policy_update|rollback",
  "target": "system_identifier",
  "impact": "Description of impact",
  "confidence": 0.92
}
```

Response:

```json
{
  "id": "action_001",
  "type": "isolation",
  "target": "workstation-42",
  "confidence": 0.92,
  "result": "success",
  "timestamp": "2025-12-05T10:35:00Z"
}
```

---

## 🚀 Configuration Options

**React Web - Polling Interval:**

```typescript
const POLLING_INTERVAL = 3000; // 3 seconds
const STALE_TIME = 2000;       // 2 seconds
```

**React Web - Customize action types:**

```typescript
const actionConfig = {
  isolation: {
    target: "workstation-42",
    impact: "..."
  }
};
```

**Flutter Mobile - Mock data can be replaced with real API calls:**

```dart
final agentMetricsProvider = FutureProvider<Map<String, AgentMetrics>>((ref) async {
  // Replace with actual HTTP client call
  // final response = await httpClient.get('/api/self-healing/metrics');
  // return parseMetrics(response);
  
  await Future.delayed(const Duration(milliseconds: 500));
  return { };
});
```

---

## 🎨 Customization Guide

### React Web Styling

To move inline styles to CSS (if linting requires):

```css
/* styles/self-healing-monitor.css */

.progress-bar {
  width: var(--progress);
  background: linear-gradient(to right, rgba(0, 255, 255, 0.8), rgba(0, 150, 255, 0.8));
  transition: width 0.5s ease;
}

.status-card {
  border-color: rgba(0, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 255, 255, 0.1);
}
```

### Flutter Mobile Theming

Modify colors:

```dart
// Change all Color.cyan to Colors.blue
Color.cyan[300]       → Colors.blue[300]
Colors.cyan.withOpacity(0.3) → Colors.blue.withOpacity(0.3)
```

Add haptic feedback:

```dart
import 'package:flutter/services.dart';

GestureDetector(
  onTap: () {
    HapticFeedback.lightImpact();
    // action...
  },
)
```

---

## 🧪 Testing

### React Web Mock API

```typescript
// Mock for testing
const mockMetrics: MetricsData = {
  agents: { },
  overall_confidence: 0.88,
  system_health: 94
};

// Use in tests
jest.mock('@/lib/queryClient', () => ({
  apiRequest: jest.fn().mockResolvedValue(mockMetrics)
}));
```

### Flutter Mobile Test Data

```dart
// Already includes realistic mock data
// Replace FutureProvider for testing:

final agentMetricsProviderTest = 
  FutureProvider<Map<String, AgentMetrics>>((ref) async {
    return testAgentsData;
  });
```

---

## 🐛 Troubleshooting

### React Web Auto-refresh not working

Check if isAutoRefreshing is enabled:

```typescript
const autoRefresh = ref.watch(autoRefreshProvider);
// Should toggle with button
```

### React Web API errors not showing

Check error state:

```typescript
if (metricsError || actionsError) {
  // Error UI displays
}
```

### Flutter Mobile Data not updating

Manually invalidate:

```dart
ref.invalidate(agentMetricsProvider);
ref.invalidate(systemMetricsProvider);
ref.invalidate(recentActionsProvider);
```

### Flutter Mobile UI not responsive

Ensure using ConsumerWidget/ConsumerStatefulWidget:

```dart
// Check Riverpod watch/read usage
// Avoid unnecessary rebuilds
```

---

## 📈 Metrics Explained

| Metric | Range | Meaning |
|--------|-------|---------|
| System Health | 0-100% | Overall system operational status |
| RL Confidence | 0-100% | Agent decision confidence |
| Success Rate | 0-100% | % of successful recovery actions |
| Recovery Rate | 0-100% | % of incidents fully recovered |
| Accuracy | 0-100% | Agent prediction accuracy |
| Learning Progress | 0-100% | Training completion percentage |

---

## 🔗 Related Documentation

- **Backend Integration:** `docs/SELF_HEALING_RL_GUIDE.md`
- **RL Service:** `backend/core/self_healing/rl_service.py`
- **API Routes:** `backend/api/routes/self_healing.py`

---

## ✅ Checklist

### Before Deployment

- [ ] API endpoints are implemented and responding
- [ ] Mock data can be replaced with real API calls
- [ ] Error states display properly
- [ ] Auto-refresh toggle works
- [ ] Manual refresh button works
- [ ] Action execution returns proper feedback
- [ ] All color indicators work correctly
- [ ] Mobile is responsive
- [ ] Loading states display properly
- [ ] Timestamps format correctly

### Post-Deployment

- [ ] Monitor API response times
- [ ] Check error logs for API failures
- [ ] Validate metric calculations
- [ ] Test action execution
- [ ] Gather user feedback
- [ ] Optimize polling interval if needed

---

## 📞 Support

For issues or questions:

1. Check the API endpoints are working: `curl http://localhost:8000/api/self-healing/metrics`
2. Verify React/Flutter dependencies are installed
3. Check browser/app console for errors
4. Review the troubleshooting section above

---

**Last Updated:** December 5, 2025  
**Version:** 2.0 (Enhanced)  
**Status:** Ready for Integration ✅
