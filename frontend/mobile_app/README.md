# J.A.R.V.I.S. — Mobile App

Core mobile principles

- Minimalist, holographic-inspired UI with high information density and clear depth cues.
- One-hand navigation: primary actions reachable with thumb; large tap targets on the bottom/center.
- Real-time updates via WebSockets for alerts, feeds, and live SOC state.
- Lightweight 3D/2D infographics for attack paths and asset topology (use small WebGL or canvas widgets).
- All critical events delivered as immediate alerts (push & in-app) with action shortcuts.
- On-device secure enclave for PQC key storage (platform TEE/KeyStore / Secure Enclave / StrongBox).
- Biometric unlock (FaceID/TouchID) + Zero-Trust Biometric Login with PQC handshake for device-to-node pairing.

Primary screens / features

- Home Dashboard (Live SOC State) — live KPIs, active incidents, quick actions.
- Full-screen Threat Feed (Real-Time Alerts) — infinite scroll, filtering, acknowledgements.
- Asset Status Monitor — per-asset telemetry and health.
- Attack Path Predictor (mini PASM) — small visualization with predicted next-step risk.
- Incident Detail View + Actions — contain/block/patch/deceive buttons and quick runbooks.
- AI Explainability (Mobile CED Panel) — short text+visual rationale for why an alert was flagged.
- Quick Actions bar — single-tap actions for common responses.
- Voice Command Interface (mini VocalSOC) — local STT + server intent fallback.
- Self-Healing Monitor — show automated remediation state and allow manual overrides.
- Federated XDR Node Status — show node sync status and last heartbeat.
- Forensics Viewer — fetch and view timeline/log artifacts, offer export.
- Settings & Security Controls — biometric settings, key management, device pairing.

Security & architecture notes

- Store PQC private keys in the platform TEE / Secure Enclave when available. If not available, require explicit hardware policy and warn user.
- Implement a PQC-based pairing handshake between device and federation node. Use device attestation (TPM/TEE) to bind keys.
- Biometric unlock performs local auth only; the actual login exchange is a PQC handshake — biometric unlock releases the local key from the enclave.
- All sensitive operations must require explicit user confirmation (high-friction flow) and show clear consequences.
- Use secure WebSocket (wss://) with mutual TLS when possible; fallback to token + PQC signature of messages.

Developer quick-start (assumes Flutter project)

1. Install Flutter SDK and Android SDK. Follow the Flutter install guide: [https://flutter.dev/docs/get-started/install](https://flutter.dev/docs/get-started/install)
1. From the `frontend/mobile_app` directory, run:

```bash
# macOS / zsh
cd frontend/mobile_app
flutter pub get
flutter run   # launches on connected device or emulator
```

1. To run on Android emulator:

```bash
open -a Simulator   # iOS simulator (macOS only)
flutter emulators --launch <emulator-id>
flutter run
```

1. Hot reload: press `r` in the flutter run terminal.

Backend integration notes

- Provide a small health/status endpoint returning JSON for the dashboard. Example: `GET /api/v1/mobile/status`.
- Provide a WebSocket endpoint for real-time alerts (wss://) and a lightweight binary format (JSON lines acceptable).
- Implement a short REST pairing flow for device registration/pqc handshake: `POST /api/v1/device/register`.

Next recommended tasks

1. Confirm the mobile project type (if this repo uses Flutter, confirm `lib/main.dart` and `pubspec.yaml`).
2. Add a minimal health-check screen that calls `GET /api/v1/mobile/status` (scaffold `lib/main.dart`).
3. Add WebSocket client service and a simple Threat Feed UI to render live alerts.
4. Create a short security integration checklist for PQC/TEE on iOS and Android.
