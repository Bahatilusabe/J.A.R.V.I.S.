# PQC Quick Start Guide

Get up and running with Post-Quantum Cryptography in J.A.R.V.I.S.

## 1. Installation

### Prerequisites

```bash
# Install Python dependencies
pip install cryptography

# Optional: Install liboqs for production
# macOS
brew install liboqs

# Ubuntu/Debian
sudo apt-get install liboqs-dev

# Or Python package
pip install liboqs-python
```

## 2. Basic Usage

### Configure Environment

```bash
# Set algorithm defaults
export PQC_KEM="Kyber768"
export PQC_SIG="Dilithium3"
export PQC_KEY_ROTATION_DAYS=180
```

### Key Management

```python
from backend.core.pqcrypto.config import get_key_manager

# Get the singleton key manager
km = get_key_manager()

# Generate keypairs
kem_pub, kem_priv = km.generate_kem_keypair()
sig_pub, sig_priv = km.generate_sig_keypair()

# Backup keys
backup_path = km.backup_keys()
print(f"Keys backed up to: {backup_path}")

# Export public keys for distribution
public_keys = km.export_public_keys()
print(f"Kyber public key ID: {public_keys['kem_key_id']}")
```

### Key Exchange (Kyber)

```python
from backend.core.pqcrypto.kyber import KyberKEM

kem = KyberKEM("Kyber768")

# Alice generates keypair
alice_pub, alice_priv = kem.generate_keypair()

# Bob encapsulates
ciphertext, shared_secret = kem.encapsulate(alice_pub)

# Alice decapsulates
recovered_secret = kem.decapsulate(ciphertext, alice_priv)

assert shared_secret == recovered_secret
print("✓ Shared secret established!")
```

### Digital Signatures (Dilithium)

```python
from backend.core.pqcrypto.dilithium import DilithiumSigner

signer = DilithiumSigner("Dilithium3")

# Generate keypair
pub, priv = signer.generate_keypair()

# Sign a message
message = b"Important message"
signature = signer.sign(message, priv)

# Verify signature
valid = signer.verify(signature, message, pub)
assert valid
print("✓ Signature verified!")
```

### Complete Handshake

```python
from backend.core.pqcrypto.handshake import (
    PQCHandshakeServer,
    PQCHandshakeClient,
    ClientHello,
    ClientKeyExchange,
)
import json
import base64

# ============ CLIENT ============
client = PQCHandshakeClient()
client_hello = client.generate_client_hello()
client_hello_json = client_hello.to_json()

# ============ SERVER ============
server = PQCHandshakeServer()
client_hello_recv = ClientHello.from_json(client_hello_json)
server_hello, _ = server.process_client_hello(client_hello_recv)
server_hello_json = server_hello.to_json()

# ============ CLIENT ============
client_session, _ = client.process_server_hello(server_hello_json)
client_key_exchange = client.generate_client_key_exchange()

# Convert to JSON for transmission
client_key_dict = {
    "client_ephemeral_public_key": base64.b64encode(
        client_key_exchange.client_ephemeral_public_key
    ).decode(),
    "encapsulated_secret": base64.b64encode(
        client_key_exchange.encapsulated_secret
    ).decode(),
    "client_certificate": base64.b64encode(
        client_key_exchange.client_certificate
    ).decode(),
}

# ============ SERVER ============
client_key_recv = ClientKeyExchange(
    client_ephemeral_public_key=base64.b64decode(
        client_key_dict["client_ephemeral_public_key"]
    ),
    encapsulated_secret=base64.b64decode(
        client_key_dict["encapsulated_secret"]
    ),
    client_certificate=base64.b64decode(
        client_key_dict["client_certificate"]
    ),
)
server_session, _ = server.process_client_key_exchange(client_key_recv)
server_finished = server.get_server_finished()

server_finished_json = json.dumps({
    "verify_data": base64.b64encode(server_finished.verify_data).decode(),
    "signature": base64.b64encode(server_finished.signature).decode(),
})

# ============ CLIENT ============
valid = client.verify_server_finished(server_finished_json)
assert valid

# ============ BOTH SIDES ============
assert client_session.session_id == server_session.session_id
assert client_session.shared_secret == server_session.shared_secret
assert client_session.client_write_key == server_session.client_write_key
print("✓ Handshake complete! Session established.")
print(f"  Session ID: {client_session.session_id}")
print(f"  Client write key: {client_session.client_write_key.hex()}")
print(f"  Server write key: {client_session.server_write_key.hex()}")
```

## 3. Configuration Reference

### Environment Variables

```bash
# KEM Algorithm (default: Kyber768)
export PQC_KEM="Kyber768"  # or Kyber512, Kyber1024

# Signature Algorithm (default: Dilithium3)
export PQC_SIG="Dilithium3"  # or Dilithium2, Dilithium5

# Key Management
export PQC_KEY_ROTATION_DAYS=180
export PQC_KEY_VALIDITY_DAYS=365
export PQC_KEY_BACKUP_DIR="/var/lib/jarvis/pqc_keys"

# Handshake
export PQC_HANDSHAKE_TIMEOUT=30

# Hybrid Mode (optional)
export PQC_SUPPORT_HYBRID=true

# Logging
export PQC_LOG_LEVEL=INFO
export PQC_AUDIT_LOG_ENABLED=true
```

## 4. Security Levels

| Use Case | KEM | Signature | Quantum-Safe | |----------|-----|-----------|--------------| |
Testing/Dev | Kyber512 | Dilithium2 | ~128 bits | | **General Use** | **Kyber768** | **Dilithium3**
| **~192 bits** | | Critical Systems | Kyber1024 | Dilithium5 | ~256 bits |

## 5. Common Tasks

### Rotate Keys

```python
from backend.core.pqcrypto.config import get_key_manager

km = get_key_manager()
km.generate_kem_keypair()  # Generate initial keys

# Later: rotate keys
new_pub, new_priv = km.rotate_kem_key(
    reason="scheduled rotation",
    performed_by="admin"
)

# Check audit trail
for entry in km.get_rotation_audit_log():
    print(f"{entry.timestamp}: {entry.reason}")
```

### Backup and Restore

```python
from backend.core.pqcrypto.config import get_key_manager

km = get_key_manager()
km.generate_kem_keypair()
km.generate_sig_keypair()

# Backup
backup_path = km.backup_keys()
print(f"Backed up to: {backup_path}")

# Later: restore
km2 = get_key_manager()
km2.restore_keys(backup_path)
assert km2.current_kem_key == km.current_kem_key
```

### Export Public Keys

```python
from backend.core.pqcrypto.config import get_key_manager
import json

km = get_key_manager()
km.generate_kem_keypair()
km.generate_sig_keypair()

public_keys = km.export_public_keys()
# Save for distribution
with open("public_keys.json", "w") as f:
    json.dump(public_keys, f, indent=2)
```

### Use Hybrid Mode

```python
from backend.core.pqcrypto.kyber import HybridKyberClassical

hybrid = HybridKyberClassical("Kyber768")

# Get keys for both Kyber and classical ECDH
kyber_pub, classical_pub, kyber_priv, classical_priv = hybrid.generate_keypair()

# Encapsulate with both (combines Kyber + ECDH)
kyber_ct, classical_ct, combined_secret = hybrid.encapsulate(
    kyber_pub, classical_pub
)

# Secret is protected by BOTH quantum-safe AND classical algorithms
# Even if one is broken, the other protects the secret
```

## 6. Testing

### Run Unit Tests

```bash
# Run all PQC tests
python3 -m pytest backend/tests/unit/test_pqc_config.py -v

# Run specific test class
python3 -m pytest backend/tests/unit/test_pqc_config.py::TestPQCKeyManager -v

# Run with coverage
python3 -m pytest backend/tests/unit/test_pqc_config.py --cov=backend.core.pqcrypto -v
```

### Manual Test

```python
# Test basic operations
from backend.core.pqcrypto.config import get_key_manager
from backend.core.pqcrypto.kyber import KyberKEM
from backend.core.pqcrypto.dilithium import DilithiumSigner

print("Testing Kyber...")
kem = KyberKEM("Kyber768")
pub, priv = kem.generate_keypair()
ct, ss = kem.encapsulate(pub)
ss2 = kem.decapsulate(ct, priv)
assert ss == ss2
print("✓ Kyber works")

print("Testing Dilithium...")
signer = DilithiumSigner("Dilithium3")
pub, priv = signer.generate_keypair()
sig = signer.sign(b"test", priv)
assert signer.verify(sig, b"test", pub)
print("✓ Dilithium works")

print("Testing Key Manager...")
km = get_key_manager()
km.generate_kem_keypair()
km.generate_sig_keypair()
print("✓ Key manager works")

print("\n✓ All tests passed!")
```

## 7. Troubleshooting

### "liboqs not available"

The system falls back to an emulator for testing. For production:

```bash
# macOS
brew install liboqs

# Ubuntu
sudo apt-get install liboqs-dev

# Python
pip install liboqs-python
```

### Handshake Timeout

If handshake times out:

```bash
# Increase timeout (default 30s)
export PQC_HANDSHAKE_TIMEOUT=60
```

### Wrong Algorithm Selected

Check environment variables:

```python
from backend.core.pqcrypto.config import get_pqc_config

config = get_pqc_config()
print(f"KEM: {config.kem_algorithm}")
print(f"SIG: {config.sig_algorithm}")
```

## 8. Next Steps

1. **Basic Operations**: Start with key generation and signatures
1. **Key Exchange**: Try the Kyber encapsulation examples
1. **Handshake**: Implement the full handshake protocol
1. **Integration**: Add to FastAPI routes
1. **Production**: Enable HSM, configure backups, set up monitoring

## 9. Documentation

- **Full Guide**: `docs/PQC_GUIDE.md`
- **API Reference**: `docs/PQC_API_REFERENCE.md`
- **Delivery Summary**: `PQC_DELIVERY_SUMMARY.md`
- **Implementation Checklist**: `PQC_IMPLEMENTATION_CHECKLIST.md`

## 10. Support

For issues or questions:

1. Check the documentation files
1. Review test examples in `backend/tests/unit/test_pqc_config.py`
1. Enable debug logging: `export PQC_LOG_LEVEL=DEBUG`
1. Check audit logs: `km.get_rotation_audit_log()`

## Quick Commands

```bash
# Set up environment
export PQC_KEM="Kyber768"
export PQC_SIG="Dilithium3"
export PQC_KEY_ROTATION_DAYS=180

# Run tests
python3 -m pytest backend/tests/unit/test_pqc_config.py -v

# Check configuration
python3 -c "from backend.core.pqcrypto.config import get_pqc_config; print(get_pqc_config().to_dict())"

# Generate and export keys
python3 << 'EOF'
from backend.core.pqcrypto.config import get_key_manager
import json

km = get_key_manager()
km.generate_kem_keypair()
km.generate_sig_keypair()
keys = km.export_public_keys()
print(json.dumps(keys, indent=2))
EOF
```

______________________________________________________________________

**Ready to go!** Start with the examples above and refer to the documentation for more details.
