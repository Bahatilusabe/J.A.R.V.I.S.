# Web Dashboard Setup Guide

## Project Overview

This is a **production-ready** React + TypeScript web dashboard for J.A.R.V.I.S. built with:

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + PostCSS
- **State Management**: Redux Toolkit + React Query
- **Real-time Communication**: WebSocket + SSE fallback
- **Visualization**: Three.js, D3.js, Cytoscape.js
- **Authentication**: PQC-backed tokens (hybrid TLS + PQC)
- **Deployment**: Docker + Huawei CCE

---

## Prerequisites

- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0
- **Docker**: (optional, for containerized deployment)
- **Backend API**: Running on `http://127.0.0.1:5000`

---

## Installation

### 1. Install Dependencies

```bash
cd frontend/web_dashboard
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env.local` and update as needed:

```bash
cp .env.example .env.local
```

### 3. (Optional) Install Backend Requirements

If developing against the Python backend:

```bash
cd backend
pip install -r requirements.txt
```

---

## Development

### Start Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

### Key Directories

```
src/
├── components/          # Reusable React components
├── pages/              # Page components (PASM, Self-healing, etc.)
├── hooks/              # Custom React hooks
├── services/           # API and WebSocket services
├── store/              # Redux store and slices
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
├── styles/             # Global CSS and Tailwind
└── assets/             # Images, fonts, etc.
```

### Available Scripts

```bash
# Development server (HMR enabled)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Run TypeScript type checking
npm run type-check

# Run ESLint
npm run lint

# Format code with Prettier
npm run format

# Build Docker image
npm run docker:build

# Run Docker container
npm run docker:run
```

---

## Configuration Files

### `vite.config.ts`
- Build configuration
- Development server proxy settings
- Code splitting strategy
- Environment variable definitions

### `tsconfig.json`
- TypeScript compiler options
- Path aliases (@components, @services, etc.)
- Strict type checking enabled

### `tailwind.config.ts`
- Custom color palette (neon cyan, dark navy, etc.)
- Font family and sizing
- Custom animations and effects
- Utility class safelist

### `postcss.config.js`
- Tailwind CSS processing
- Autoprefixer for browser compatibility

### `.env.local` / `.env.example`
- API endpoints
- WebSocket configuration
- Feature flags
- Authentication settings

---

## API Integration

### Available Services

#### `auth.service.ts`
- User login/logout
- Token refresh
- PQC authentication
- User profile management

```typescript
import authService from '@/services/auth.service'

// Login
const token = await authService.login(username, password)

// Get current user
const user = await authService.getProfile()

// Refresh token
const newToken = await authService.refreshToken()
```

#### `websocket.service.ts`
- Real-time event subscriptions
- Message publishing
- Automatic reconnection
- Connection status monitoring

```typescript
import websocketService from '@/services/websocket.service'

// Connect
await websocketService.connect()

// Subscribe to events
websocketService.on('pasm:prediction', (data) => {
  console.log('New PASM prediction:', data)
})

// Publish events
websocketService.send('request:predict', { nodeId: '123' })

// Check connection status
const status = websocketService.getStatus()
```

---

## State Management

### Redux Store Structure

```typescript
store/
├── index.ts              # Store configuration
├── auth/
│   ├── authSlice.ts     # Auth state and reducers
│   └── authAPI.ts       # Auth API calls
├── pasm/
│   ├── pasmSlice.ts     # PASM state and reducers
│   └── pasmAPI.ts       # PASM API calls
└── ui/
    ├── uiSlice.ts       # UI state (notifications, modals, etc.)
    └── uiAPI.ts         # UI API calls
```

### Using Redux

```typescript
import { useDispatch, useSelector } from 'react-redux'
import { loginUser } from '@/store/auth/authAPI'

function LoginComponent() {
  const dispatch = useDispatch()
  const { isLoading, error } = useSelector((state) => state.auth)

  const handleLogin = async (username: string, password: string) => {
    await dispatch(loginUser({ username, password }))
  }

  return (
    // JSX
  )
}
```

---

## Real-time Features

### WebSocket Events

**Incoming Events** (from server):
- `pasm:prediction` - New PASM attack prediction
- `metric:update` - System metric update
- `alert:triggered` - Security alert
- `healing:status` - Self-healing status update

**Outgoing Events** (from client):
- `request:predict` - Request PASM prediction
- `request:remediate` - Request healing action
- `request:report` - Request CED report

### Server-Sent Events (SSE) Fallback

If WebSocket is unavailable:

```typescript
const eventSource = new EventSource('/api/telemetry/stream')
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // Handle telemetry data
}
```

---

## Authentication Flow

### PQC-Backed Authentication

1. **Login Request**
   ```
   POST /auth/login
   {
     "username": "user",
     "password": "pass"
   }
   ```

2. **Response with PQC Token**
   ```json
   {
     "accessToken": "pqc_eyJ...",
     "refreshToken": "refresh_...",
     "expiresIn": 3600,
     "tokenType": "PQC",
     "pqcEnabled": true
   }
   ```

3. **Token Storage**
   - Stored in localStorage for simplicity
   - In production, consider using secure HttpOnly cookies
   - Tokens are attached to all API requests via Authorization header

4. **Token Refresh**
   - Tokens expire after 1 hour
   - Automatic refresh on 401 responses
   - Tokens are hybrid TLS + post-quantum cryptography

### PQC Verification

```typescript
import authService from '@/services/auth.service'

const isVerified = await authService.verifyPQC(challenge, response)
```

---

## Building for Production

### Build Process

```bash
npm run build
```

This will:
1. Run TypeScript type checking
2. Optimize and minify code
3. Generate source maps (if VITE_SOURCEMAP=true)
4. Create vendor bundles (React, D3, Three.js, etc.)
5. Output optimized files to `dist/`

### Build Output

```
dist/
├── index.html          # Entry point
├── assets/
│   ├── js/            # JavaScript bundles (code-split)
│   ├── css/           # Optimized CSS
│   └── images/        # Optimized images
└── vendor/            # Separate vendor chunks
```

---

## Docker Deployment

### Build Docker Image

```bash
npm run docker:build
```

### Run Container

```bash
npm run docker:run
```

Or with docker-compose:

```bash
docker-compose up
```

### Environment Variables for Docker

Set these in `docker-compose.yml` or `.env` file:

```
VITE_API_BASE_URL=http://backend:5000
VITE_WEBSOCKET_URL=ws://backend:5000
NODE_ENV=production
```

---

## Huawei Cloud Deployment (CCE)

### Preparation

1. **Tag Docker Image**
   ```bash
   docker tag jarvis-dashboard:latest <huawei-registry>/jarvis-dashboard:latest
   ```

2. **Push to Huawei Registry**
   ```bash
   docker push <huawei-registry>/jarvis-dashboard:latest
   ```

3. **Create Kubernetes Deployment**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: jarvis-dashboard
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: dashboard
           image: <huawei-registry>/jarvis-dashboard:latest
           ports:
           - containerPort: 5173
           env:
           - name: VITE_API_BASE_URL
             value: "http://backend-service:5000"
           - name: VITE_WEBSOCKET_URL
             value: "ws://backend-service:5000"
   ```

### CDN Configuration

Assets can be served from Huawei CDN by setting:

```
VITE_CDN_URL=https://cdn.example.com/jarvis-assets
VITE_HUAWEI_CDN_BUCKET=jarvis-assets
```

---

## Performance Optimization

### Code Splitting

Vite automatically splits code into:
- **react-vendor**: React, React DOM, Router
- **ui-vendor**: D3, Three.js, Cytoscape
- **state**: Redux, React Query
- **realtime**: Socket.io, EventSource

### Image Optimization

Images are automatically optimized with:
- JPEG quality: 80%
- WebP format support
- Responsive image generation

### Compression

Two compression formats are generated:
- **Brotli**: Best compression (default for modern browsers)
- **GZIP**: Fallback for older browsers

---

## Type Safety

### TypeScript Configuration

- **Strict Mode**: Enabled for maximum type safety
- **No Implicit Any**: Prevents accidental `any` types
- **Path Aliases**: Clean import statements

### Type Definitions

All API responses are typed:

```typescript
interface ApiResponse<T> {
  success: boolean
  data: T
  error?: string
  message?: string
}

interface PasmPrediction {
  nodeId: string
  riskScore: number
  uncertainty: number
  paths: AttackPath[]
  recommendations: string[]
  timestamp: string
}
```

---

## Testing

### Component Testing

```typescript
import { render, screen } from '@testing-library/react'
import Dashboard from '@/pages/Dashboard'

describe('Dashboard', () => {
  it('renders dashboard', () => {
    render(<Dashboard />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })
})
```

### Service Testing

```typescript
import authService from '@/services/auth.service'

describe('AuthService', () => {
  it('logs in user', async () => {
    const token = await authService.login('user', 'pass')
    expect(token.accessToken).toBeDefined()
  })
})
```

---

## Troubleshooting

### WebSocket Connection Issues

1. Check backend is running: `http://127.0.0.1:5000`
2. Verify WebSocket URL in `.env.local`
3. Check CORS and WebSocket CORS headers on backend
4. Review browser console for connection errors

### Type Errors

```bash
# Run type checking
npm run type-check

# This helps identify missing types or incorrect imports
```

### Build Issues

```bash
# Clear cache and reinstall
rm -rf node_modules dist
npm install
npm run build
```

### Hot Module Replacement (HMR) Not Working

1. Ensure Vite dev server is running on correct port
2. Check firewall settings
3. Try accessing `http://localhost:5173` instead of `127.0.0.1:5173`

---

## Additional Resources

- [Vite Documentation](https://vitejs.dev)
- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org)
- [React Query Documentation](https://tanstack.com/query)
- [Three.js Documentation](https://threejs.org)
- [D3.js Documentation](https://d3js.org)

---

## Support & Contribution

For issues or feature requests, please open an issue on the project repository.

---

**Last Updated**: December 6, 2025  
**Status**: ✅ Production Ready
