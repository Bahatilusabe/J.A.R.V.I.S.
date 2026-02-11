# Post-Quantum Cryptography (PQC) Implementation Guide

## Overview

This document describes J.A.R.V.I.S.'s Post-Quantum Cryptographic (PQC) system, which protects
against future threats from quantum computers. The system combines:

- **Kyber** (Key Encapsulation Mechanism) for key exchange
- **Dilithium** (Digital Signature Algorithm) for authentication
- Lattice-based cryptography resistant to quantum attacks
- NIST-approved algorithms (FIPS 203, FIPS 204)

## Architecture Components

The PQC system consists of the following integrated components:

1. **PQC Configuration & Key Management** (config.py)

   - Algorithm selection (Kyber512/768/1024, Dilithium2/3/5)
   - Key generation and rotation
   - Key backup and restoration
   - Audit trail tracking

1. **Kyber KEM** (kyber.py)

   - Keypair generation
   - Key encapsulation
   - Key decapsulation
   - Three security levels

1. **Dilithium DSA** (dilithium.py)

   - Keypair generation
   - Message signing
   - Signature verification
   - Three security levels

1. **PQC Handshake Protocol** (handshake.py)

   - ClientHello / ServerHello exchange
   - Kyber-based key exchange
   - Dilithium-based mutual authentication
   - Session key derivation
   - Server & Client implementations

1. **Additional Features**

   - Hybrid mode (Kyber + classical ECDH)
   - Attestation (attestation.py)
   - CANN optimization (cann_ops.py)
   - Hardware Security Module (HSM) support

## Security Levels

Each algorithm family offers three security levels:

| Level | Kyber | Dilithium | Quantum-Safe Bits | Use Case |
|-------|-------|-----------|-------------------|----------| | 1 | Kyber512 | Dilithium2 | ~128 |
Testing, non-critical systems | | 3 | Kyber768 | Dilithium3 | ~192 | Default for general use | | 5 |
Kyber1024 | Dilithium5 | ~256 | High-security critical systems |

**Default**: Kyber768 + Dilithium3 (~192-bit quantum-secure)

## Configuration

### Environment Variables

All PQC behavior is controlled via environment variables:

```bash
# Algorithm Selection
export PQC_KEM="Kyber768"                    # KEM algorithm
export PQC_SIG="Dilithium3"                  # Signature algorithm

# Key Management
export PQC_KEY_ROTATION_DAYS=180             # Automatic rotation interval
export PQC_KEY_VALIDITY_DAYS=365             # Key expiration
export PQC_KEY_BACKUP_DIR="/var/lib/jarvis/pqc_keys"

# Handshake
export PQC_HANDSHAKE_TIMEOUT=30              # Timeout in seconds
export PQC_SUPPORT_HYBRID=true               # Enable hybrid mode

# Attestation
export PQC_ATTESTATION_ENABLED=true
export PQC_ATTESTATION_CERT_VALIDITY_DAYS=365

# Hardware Security Module (HSM)
export PQC_USE_HSM=false                     # Use hardware module
export PQC_HSM_MODULE="/usr/lib/softhsm/libsofthsm2.so"
export PQC_HSM_SLOT=0
export PQC_HSM_PIN=1234

# CANN/Gradient Compression
export PQC_USE_CANN=true                     # Enable CANN optimization
export PQC_GRADIENT_COMPRESSION_RATIO=0.1    # Compression ratio

# Logging
export PQC_LOG_LEVEL=INFO
export PQC_AUDIT_LOG_ENABLED=true
```

### Programmatic Configuration

```python
from backend.core.pqcrypto.config import PQCConfig, get_pqc_config

# Get singleton instance (recommended)
config = get_pqc_config()

# Or create new instance
config = PQCConfig()

# Access configuration
print(config.kem_algorithm)  # "Kyber768"
print(config.key_rotation_days)  # 180
```

## Usage Examples

### Key Management

```python
from backend.core.pqcrypto.config import get_key_manager

# Get singleton key manager
km = get_key_manager()

# Generate initial keypairs
kem_pub, kem_priv = km.generate_kem_keypair()
sig_pub, sig_priv = km.generate_sig_keypair()

# Rotate keys (scheduled or on-demand)
new_kem_pub, new_kem_priv = km.rotate_kem_key(
    reason="scheduled rotation",
    performed_by="system"
)

# Backup keys (SENSITIVE - protect this file!)
backup_path = km.backup_keys()

# View rotation history
audit_log = km.get_rotation_audit_log()
for entry in audit_log:
    print(f"{entry.timestamp}: {entry.reason}")

# Export public keys for distribution
public_keys = km.export_public_keys()
```

### Kyber KEM (Key Exchange)

```python
from backend.core.pqcrypto.kyber import KyberKEM

# Create KEM with security level
kem = KyberKEM("Kyber768")  # or Kyber512, Kyber1024

# Alice generates keypair
alice_pub, alice_priv = kem.generate_keypair()

# Bob encapsulates a secret to Alice's public key
ciphertext, shared_secret = kem.encapsulate(alice_pub)

# Alice decapsulates to recover the same secret
shared_secret_recovered = kem.decapsulate(ciphertext, alice_priv)

assert shared_secret == shared_secret_recovered
```

### Dilithium Signatures (Authentication)

```python
from backend.core.pqcrypto.dilithium import DilithiumSigner

# Create signer with security level
signer = DilithiumSigner("Dilithium3")

# Generate keypair
pub_key, priv_key = signer.generate_keypair()

# Sign a message
message = b"Hello, World!"
signature = signer.sign(message, priv_key)

# Verify signature
is_valid = signer.verify(signature, message, pub_key)
assert is_valid
```

### PQC Handshake Protocol

#### Server Side

```python
from backend.core.pqcrypto.handshake import PQCHandshakeServer, ClientHello

# Initialize handshake server
server = PQCHandshakeServer(timeout_seconds=30)

# Receive ClientHello from client
client_hello_json = receive_from_client()
client_hello = ClientHello.from_json(client_hello_json)

# Process and respond
server_hello, state = server.process_client_hello(client_hello)
send_to_client(server_hello.to_json())

# Receive ClientKeyExchange
from backend.core.pqcrypto.handshake import ClientKeyExchange
client_key_exchange_json = receive_from_client()
client_key_exchange = json.loads(client_key_exchange_json)
client_key_exchange = ClientKeyExchange(**client_key_exchange)

# Process key exchange
session, state = server.process_client_key_exchange(client_key_exchange)

# Send ServerFinished with signature
server_finished = server.get_server_finished()
send_to_client(json.dumps({
    "verify_data": base64.b64encode(server_finished.verify_data).decode(),
    "signature": base64.b64encode(server_finished.signature).decode()
}))
```

#### Client Side

```python
from backend.core.pqcrypto.handshake import PQCHandshakeClient
import json

# Initialize handshake client
client = PQCHandshakeClient(timeout_seconds=30)

# Send ClientHello
client_hello = client.generate_client_hello()
send_to_server(client_hello.to_json())

# Receive ServerHello
server_hello_json = receive_from_server()
session, state = client.process_server_hello(server_hello_json)

# Send ClientKeyExchange
client_key_exchange = client.generate_client_key_exchange()
send_to_server(json.dumps({
    "client_ephemeral_public_key": base64.b64encode(
        client_key_exchange.client_ephemeral_public_key
    ).decode(),
    "encapsulated_secret": base64.b64encode(
        client_key_exchange.encapsulated_secret
    ).decode(),
    "client_certificate": base64.b64encode(
        client_key_exchange.client_certificate
    ).decode(),
}))

# Receive ServerFinished
server_finished_json = receive_from_server()
valid = client.verify_server_finished(server_finished_json)
assert valid
```

### Hybrid Mode (Kyber + Classical ECDH)

```python
from backend.core.pqcrypto.kyber import HybridKyberClassical

# Use both Kyber (quantum-safe) and ECDH (classical)
hybrid = HybridKyberClassical("Kyber768")

# Generate keypairs for both
kyber_pub, classical_pub, kyber_priv, classical_priv = hybrid.generate_keypair()

# Encapsulate with both algorithms
kyber_ct, classical_ct, combined_secret = hybrid.encapsulate(kyber_pub, classical_pub)

# shared_secret is combination of both Kyber and ECDH secrets
```

## FastAPI Integration Example

Register PQC routes in `backend/api/server.py`:

```python
from backend.api.routes import pqc_routes

app.include_router(pqc_routes.router, prefix="/api/pqc")
```

Then implement routes to handle:

- `/api/pqc/handshake/hello` - ClientHello endpoint
- `/api/pqc/handshake/key-exchange` - ClientKeyExchange endpoint
- `/api/pqc/session/verify` - Verify session is established

## Security Considerations

### Key Storage

- Private keys must be stored securely (encrypted on disk)
- Backups should be encrypted and stored separately
- Consider using Hardware Security Modules (HSMs) for production
- Set `PQC_USE_HSM=true` and configure HSM details

### Key Rotation

- Automatic rotation scheduled every 180 days (configurable)
- Manual rotation available for immediate needs
- All rotations are logged with timestamps and reasons
- Old key IDs are tracked for decryption of old ciphertexts

### Handshake Security

- Default timeout: 30 seconds (prevent resource exhaustion)
- Protocol version negotiation
- Cipher suite selection
- Mutual authentication via Dilithium signatures

### Hybrid Mode Advantage

- Combines Kyber (quantum-safe) + ECDH (classical)
- Even if Kyber is broken, ECDH protects the secret
- Even if ECDH is broken, Kyber protects the secret
- Recommended for critical systems during transition period

## Testing

### Unit Tests

```bash
# Run all PQC tests
make test -- backend/tests/unit/test_pqc_*.py

# Run specific test
pytest backend/tests/unit/test_pqc_config.py::TestPQCKeyManager -v

# Run with coverage
pytest backend/tests/unit/test_pqc_*.py --cov=backend.core.pqcrypto
```

### Integration Tests

```bash
# Test full handshake flow
pytest backend/tests/integration/test_pqc_handshake.py -v
```

## Key Sizes

| Algorithm | Public Key | Private Key | Ciphertext |
|-----------|-----------|-----------|------------| | Kyber512 | 800 bytes | 1,632 bytes | 768 bytes
| | Kyber768 | 1,184 bytes | 2,400 bytes | 1,088 bytes | | Kyber1024 | 1,568 bytes | 3,168 bytes |
1,568 bytes |

| Algorithm | Public Key | Private Key | Signature |
|-----------|-----------|-----------|-----------| | Dilithium2 | 1,312 bytes | 2,544 bytes | 2,420
bytes | | Dilithium3 | 1,952 bytes | 4,016 bytes | 3,293 bytes | | Dilithium5 | 2,592 bytes | 4,880
bytes | 4,595 bytes |

## Operation Timing (approximate)

- Kyber keypair generation: ~1ms
- Kyber encapsulation: ~0.5ms
- Kyber decapsulation: ~0.5ms
- Dilithium keypair generation: ~5ms
- Dilithium signing: ~2ms
- Dilithium verification: ~3ms

## Troubleshooting

### "liboqs not available"

The system falls back to an emulator for testing. For production, install liboqs:

```bash
# macOS
brew install liboqs

# Ubuntu/Debian
sudo apt-get install liboqs-dev

# Or use Python package
pip install liboqs-python
```

### Handshake Timing Issues

Increase timeout if network is slow:

```bash
export PQC_HANDSHAKE_TIMEOUT=60
```

### Key Manager Usage

Always use the singleton getter:

```python
from backend.core.pqcrypto.config import get_key_manager

# DO THIS
km = get_key_manager()  # Lazy singleton

# NOT THIS
from backend.core.pqcrypto.config import PQCKeyManager
km = PQCKeyManager()  # Creates new instance each time
```

## Monitoring and Audit

### Audit Log Format

```json
{
  "key_id": "kem-abc123...",
  "old_key_id": "kem-def456...",
  "new_key_id": "kem-ghi789...",
  "algorithm": "Kyber768",
  "timestamp": "2024-01-15T10:30:00.000000",
  "reason": "scheduled rotation",
  "performed_by": "system",
  "status": "completed"
}
```

### Log Levels

Set `PQC_LOG_LEVEL` to control verbosity:

- `DEBUG` - Detailed KEM/signature operations
- `INFO` - Key generation, rotation, session establishment
- `WARNING` - Key rotations, handshake failures
- `ERROR` - Critical failures (decryption errors, timeout)

## References

- [NIST FIPS 203 - Kyber](https://csrc.nist.gov/publications/fips/fips-203)
- [NIST FIPS 204 - Dilithium](https://csrc.nist.gov/publications/fips/fips-204)
- [liboqs Documentation](https://github.com/open-quantum-safe/liboqs)
- [NIST PQC Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography/)
