"""Small example showing encryption, addition, and decryption using the
HomomorphicLayer emulated and Pyfhel backends.

Run as a script or inspect the code. The Pyfhel example only runs if
Pyfhel is installed in the environment.
"""
from backend.core.blockchain_xdr.homomorphic_layer import HomomorphicLayer

VECTOR_A = [0.1, 1.5, -2.0, 3.1415]
VECTOR_B = [0.9, -0.5, 2.0, 0.8585]


def demo_emulated():
    print("--- Emulated backend demo ---")
    hl = HomomorphicLayer(backend="emulated")
    a = hl.encrypt_vector(VECTOR_A)
    b = hl.encrypt_vector(VECTOR_B)
    s = hl.add(a, b)
    out = hl.decrypt_vector(s)
    print("A:", VECTOR_A)
    print("B:", VECTOR_B)
    print("Sum:", out)


def demo_pyfhel():
    print("--- Pyfhel (SEAL) backend demo ---")
    try:
        hl = HomomorphicLayer(backend="pyfhel")
    except Exception as e:
        print("Pyfhel not available in this environment:", e)
        return

    a = hl.encrypt_vector(VECTOR_A)
    b = hl.encrypt_vector(VECTOR_B)
    s = hl.add(a, b)
    out = hl.decrypt_vector(s)
    print("A:", VECTOR_A)
    print("B:", VECTOR_B)
    print("Sum:", out)

    # demonstrate export/import of keys
    keys = hl.export_keys()
    print("Exported keys sizes:", {k: len(v) for k, v in keys.items()})

    # Import keys into a new instance and decrypt a ciphertext
    hl2 = HomomorphicLayer.from_keys(keys)
    s2 = hl2.add(a, b)
    out2 = hl2.decrypt_vector(s2)
    print("Decrypted with imported keys:", out2)


if __name__ == "__main__":
    demo_emulated()
    print()
    demo_pyfhel()
