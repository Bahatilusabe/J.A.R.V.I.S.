import pytest
import math

# Skip this file entirely if Pyfhel is not installed
pytest.importorskip("Pyfhel")

from backend.core.blockchain_xdr.homomorphic_layer import HomomorphicLayer


def almost_equal_vec(a, b, eps=1e-3):
    if len(a) != len(b):
        return False
    return all(abs(x - y) < eps for x, y in zip(a, b))


def test_pyfhel_encrypt_add_decrypt():
    hl = HomomorphicLayer(backend="pyfhel")
    a = [0.1, 1.5, -2.0]
    b = [0.9, -0.5, 2.0]

    ca = hl.encrypt_vector(a)
    cb = hl.encrypt_vector(b)

    s = hl.add(ca, cb)
    out = hl.decrypt_vector(s)

    assert almost_equal_vec(out, [x + y for x, y in zip(a, b)])


def test_pyfhel_export_import_keys():
    hl = HomomorphicLayer(backend="pyfhel")
    a = [1.2345]
    ca = hl.encrypt_vector(a)

    keys = hl.export_keys()
    assert "context" in keys and isinstance(keys["context"], (bytes, bytearray))
    assert "public_key" in keys and isinstance(keys["public_key"], (bytes, bytearray))
    assert "secret_key" in keys and isinstance(keys["secret_key"], (bytes, bytearray))

    # create a new instance from keys and decrypt
    hl2 = HomomorphicLayer.from_keys(keys)
    out = hl2.decrypt_vector(ca)
    assert almost_equal_vec(out, a)
