# PQC API Reference

## Core Classes and Functions

### PQCConfig

Configuration manager for PQC system.

```python
from backend.core.pqcrypto.config import PQCConfig, get_pqc_config

config = get_pqc_config()  # Singleton getter
```

#### Properties

- `kem_algorithm: str` - Selected KEM algorithm (Kyber512/768/1024)
- `sig_algorithm: str` - Selected signature algorithm (Dilithium2/3/5)
- `key_rotation_days: int` - Key rotation interval (default: 180)
- `key_validity_days: int` - Key expiration interval (default: 365)
- `use_hsm: bool` - Use Hardware Security Module
- `handshake_timeout_seconds: int` - Handshake timeout (default: 30)
- `attestation_enabled: bool` - Enable attestation
- `use_cann: bool` - Enable CANN optimization

#### Methods

- `to_dict() -> Dict` - Export configuration as dictionary

### PQCKeyManager

Key generation, rotation, and management.

```python
from backend.core.pqcrypto.config import get_key_manager

km = get_key_manager()  # Singleton getter
```

#### Methods

- `generate_kem_keypair() -> Tuple[bytes, bytes]` - Generate Kyber keypair
- `generate_sig_keypair() -> Tuple[bytes, bytes]` - Generate Dilithium keypair
- `rotate_kem_key(reason: str, performed_by: str) -> Tuple[bytes, bytes]` - Rotate Kyber key
- `rotate_sig_key(reason: str, performed_by: str) -> Tuple[bytes, bytes]` - Rotate Dilithium key
- `backup_keys(backup_path: Optional[str]) -> str` - Backup keys to file
- `restore_keys(backup_path: str)` - Restore keys from backup
- `get_rotation_audit_log() -> List[PQCKeyRotationAudit]` - Get audit trail
- `export_public_keys() -> Dict[str, str]` - Export public keys for distribution

### KyberKEM

Key Encapsulation Mechanism using Kyber.

```python
from backend.core.pqcrypto.kyber import KyberKEM

kem = KyberKEM("Kyber768")  # or Kyber512, Kyber1024
```

#### Methods

- `generate_keypair() -> KeyPair` - Generate (public, private) keypair
- `encapsulate(public_key: bytes) -> Tuple[bytes, bytes]` - Encapsulate to public key
  - Returns: (ciphertext, shared_secret)
- `decapsulate(ciphertext: bytes, private_key: bytes) -> bytes` - Decapsulate ciphertext
  - Returns: shared_secret
- `get_security_level_bits() -> int` - Get quantum-safe bits (128, 192, or 256)

#### Static Methods

- `get_public_key_size(algorithm: str) -> int` - Get public key size in bytes
- `get_private_key_size(algorithm: str) -> int` - Get private key size in bytes
- `get_ciphertext_size(algorithm: str) -> int` - Get ciphertext size in bytes

### DilithiumSigner

Digital Signature Algorithm using Dilithium.

```python
from backend.core.pqcrypto.dilithium import DilithiumSigner

signer = DilithiumSigner("Dilithium3")  # or Dilithium2, Dilithium5
```

#### Methods

- `generate_keypair() -> SignKeyPair` - Generate (public, private) keypair
- `sign(message: bytes, private_key: bytes) -> bytes` - Sign a message
  - Returns: signature
- `verify(signature: bytes, message: bytes, public_key: bytes) -> bool` - Verify signature
  - Returns: True if valid, False otherwise
- `get_security_level_bits() -> int` - Get quantum-safe bits (128, 192, or 256)

#### Static Methods

- `get_public_key_size(algorithm: str) -> int` - Get public key size in bytes
- `get_private_key_size(algorithm: str) -> int` - Get private key size in bytes
- `get_signature_size(algorithm: str) -> int` - Get signature size in bytes

### PQCHandshakeServer

Server-side handshake implementation.

```python
from backend.core.pqcrypto.handshake import PQCHandshakeServer, ClientHello

server = PQCHandshakeServer(timeout_seconds=30)
```

#### Methods

- `process_client_hello(client_hello: ClientHello) -> Tuple[ServerHello, HandshakeState]`
  - Process ClientHello and respond with ServerHello
- `process_client_key_exchange(client_key_exchange: ClientKeyExchange) -> Tuple[PQCSession, HandshakeState]`
  - Process ClientKeyExchange and establish session
- `get_server_finished() -> HandshakeFinished`
  - Generate ServerFinished message with signature

#### Properties

- `state: HandshakeState` - Current handshake state (IDLE, CLIENT_HELLO, SERVER_HELLO, etc.)
- `session: Optional[PQCSession]` - Established session (after key exchange)

### PQCHandshakeClient

Client-side handshake implementation.

```python
from backend.core.pqcrypto.handshake import PQCHandshakeClient

client = PQCHandshakeClient(timeout_seconds=30)
```

#### Methods

- `generate_client_hello() -> ClientHello` - Generate ClientHello message
- `process_server_hello(server_hello_json: str) -> Tuple[Optional[PQCSession], HandshakeState]`
  - Process ServerHello and establish session
- `generate_client_key_exchange() -> ClientKeyExchange` - Generate ClientKeyExchange
- `verify_server_finished(server_finished_json: str) -> bool` - Verify ServerFinished signature

#### Properties

- `state: HandshakeState` - Current handshake state
- `session: Optional[PQCSession]` - Established session (after ServerHello processing)

### PQCSession

Established secure session with derived keys.

```python
@dataclass
class PQCSession:
    session_id: str
    shared_secret: bytes
    client_random: bytes
    server_random: bytes
    cipher_suite: str
    kem_algorithm: str
    sig_algorithm: str
    
    # Derived keys
    client_write_key: bytes
    server_write_key: bytes
    client_write_iv: bytes
    server_write_iv: bytes
    client_verify_data: bytes
    server_verify_data: bytes
    
    # Metadata
    created_at: str
    expires_at: Optional[str]
    peer_identity: Optional[str]
```

#### Methods

- `is_expired() -> bool` - Check if session has expired

## Data Classes

### ClientHello

Initial client message in handshake.

```python
@dataclass
class ClientHello:
    protocol_version: str = "PQC/1.0"
    client_random: bytes = field(default_factory=lambda: os.urandom(32))
    cipher_suites: List[str] = [...]
    supported_groups: List[str] = ["Kyber768", "Kyber1024"]
    sig_algorithms: List[str] = ["Dilithium3", "Dilithium5"]
    psk_modes: List[str] = ["psk_ke", "psk_dhe_ke"]
    extensions: Dict = {}
    timestamp: str = field(default_factory=...)
```

#### Methods

- `to_json() -> str` - Serialize to JSON
- `from_json(cls, data: str) -> ClientHello` - Deserialize from JSON (classmethod)

### ServerHello

Server's response to ClientHello.

```python
@dataclass
class ServerHello:
    protocol_version: str = "PQC/1.0"
    server_random: bytes
    selected_cipher_suite: str
    selected_group: str
    selected_sig_algorithm: str
    server_ephemeral_public_key: bytes
    server_certificate: bytes
    extensions: Dict = {}
    timestamp: str
```

#### Methods

- `to_json() -> str` - Serialize to JSON
- `from_json(cls, data: str) -> ServerHello` - Deserialize from JSON (classmethod)

### ClientKeyExchange

Client's key exchange contribution.

```python
@dataclass
class ClientKeyExchange:
    client_ephemeral_public_key: bytes
    encapsulated_secret: bytes
    client_certificate: bytes
```

### HandshakeFinished

Handshake completion with signature.

```python
@dataclass
class HandshakeFinished:
    verify_data: bytes
    signature: bytes
```

## Enumerations

### HandshakeState

```python
class HandshakeState(Enum):
    IDLE = "idle"
    CLIENT_HELLO = "client_hello"
    SERVER_HELLO = "server_hello"
    CLIENT_FINISHED = "client_finished"
    SERVER_FINISHED = "server_finished"
    ESTABLISHED = "established"
    FAILED = "failed"
```

### CipherSuite

```python
class CipherSuite(Enum):
    KYBER768_DILITHIUM3 = "Kyber768-Dilithium3"
    KYBER1024_DILITHIUM5 = "Kyber1024-Dilithium5"
    KYBER512_DILITHIUM2 = "Kyber512-Dilithium2"
```

### KeyEncapsulationMechanism

```python
class KeyEncapsulationMechanism(Enum):
    KYBER512 = "Kyber512"
    KYBER768 = "Kyber768"
    KYBER1024 = "Kyber1024"
```

### DigitalSignatureAlgorithm

```python
class DigitalSignatureAlgorithm(Enum):
    DILITHIUM2 = "Dilithium2"
    DILITHIUM3 = "Dilithium3"
    DILITHIUM5 = "Dilithium5"
```

## Error Handling

### Common Exceptions

- `ValueError` - Invalid algorithm or parameter
- `RuntimeError` - Key generation or cryptographic operation failure
- `HTTPException` (FastAPI) - HTTP errors in API routes

### Example Error Handling

```python
from backend.core.pqcrypto.kyber import KyberKEM

try:
    kem = KyberKEM("InvalidAlgorithm")
except ValueError as e:
    print(f"Invalid algorithm: {e}")

try:
    shared_secret = kem.decapsulate(bad_ciphertext, private_key)
except ValueError as e:
    print(f"Decapsulation failed: {e}")
```

## Environment Variables Reference

| Variable | Default | Description | |----------|---------|-------------| | PQC_KEM | Kyber768 | Key
encapsulation algorithm | | PQC_SIG | Dilithium3 | Signature algorithm | | PQC_KEY_ROTATION_DAYS |
180 | Key rotation interval (days) | | PQC_KEY_VALIDITY_DAYS | 365 | Key validity (days) | |
PQC_KEY_BACKUP_DIR | /var/lib/jarvis/pqc_keys | Backup directory | | PQC_HANDSHAKE_TIMEOUT | 30 |
Handshake timeout (seconds) | | PQC_SUPPORT_HYBRID | true | Enable hybrid mode | |
PQC_ATTESTATION_ENABLED | true | Enable attestation | | PQC_ATTESTATION_CERT_VALIDITY_DAYS | 365 |
Attestation cert validity | | PQC_USE_HSM | false | Use Hardware Security Module | | PQC_HSM_MODULE
| (empty) | HSM module path | | PQC_HSM_SLOT | 0 | HSM slot number | | PQC_HSM_PIN | (empty) | HSM
PIN | | PQC_USE_CANN | true | Enable CANN optimization | | PQC_GRADIENT_COMPRESSION_RATIO | 0.1 |
Gradient compression ratio | | PQC_LOG_LEVEL | INFO | Logging level | | PQC_AUDIT_LOG_ENABLED | true
| Enable audit logging |

## Example: Complete Handshake

```python
import json
import base64
from backend.core.pqcrypto.handshake import (
    PQCHandshakeServer,
    PQCHandshakeClient,
    ClientHello,
    ClientKeyExchange,
)

# === CLIENT SIDE ===
client = PQCHandshakeClient()
client_hello = client.generate_client_hello()
client_hello_json = client_hello.to_json()

# === SERVER SIDE ===
server = PQCHandshakeServer()
client_hello_recv = ClientHello.from_json(client_hello_json)
server_hello, state = server.process_client_hello(client_hello_recv)
server_hello_json = server_hello.to_json()

# === CLIENT PROCESSES SERVER HELLO ===
session, state = client.process_server_hello(server_hello_json)

# === CLIENT SENDS KEY EXCHANGE ===
client_key_exchange = client.generate_client_key_exchange()
client_key_exchange_dict = {
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

# === SERVER PROCESSES KEY EXCHANGE ===
client_key_exchange_recv = ClientKeyExchange(
    client_ephemeral_public_key=base64.b64decode(
        client_key_exchange_dict["client_ephemeral_public_key"]
    ),
    encapsulated_secret=base64.b64decode(
        client_key_exchange_dict["encapsulated_secret"]
    ),
    client_certificate=base64.b64decode(
        client_key_exchange_dict["client_certificate"]
    ),
)
server_session, state = server.process_client_key_exchange(client_key_exchange_recv)

# === SERVER SENDS FINISHED ===
server_finished = server.get_server_finished()
server_finished_json = json.dumps({
    "verify_data": base64.b64encode(server_finished.verify_data).decode(),
    "signature": base64.b64encode(server_finished.signature).decode(),
})

# === CLIENT VERIFIES FINISHED ===
valid = client.verify_server_finished(server_finished_json)
assert valid

# === BOTH HAVE SAME SESSION ===
assert client.session.shared_secret == server_session.shared_secret
assert client.session.client_write_key == server_session.client_write_key
assert client.session.server_write_key == server_session.server_write_key
print("✓ Handshake complete")
```
