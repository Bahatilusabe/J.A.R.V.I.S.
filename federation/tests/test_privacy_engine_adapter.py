import importlib
import sys


def test_privacy_engine_opacus_integration():
    """Mock a minimal opacus-like API and ensure PrivacyEngine fallback doesn't break.

    We create a fake opacus module with a PrivacyEngine class so that
    `privacy_engine` import path finds it; the real `PrivacyEngine` in our
    module is a wrapper and should still work when opacus is available.
    """
    class FakeOpacusPE:
        def __init__(self, *args, **kwargs):
            pass

        def attach(self, module):
            return module

    fake_mod = type(sys)("opacus")
    setattr(fake_mod, "PrivacyEngine", FakeOpacusPE)
    sys.modules["opacus"] = fake_mod

    # import the privacy_engine module and run a small flow
    m = importlib.import_module("federation.privacy_engine")
    PE = m.PrivacyEngine
    pe = PE(seed=0)
    weights = {"a": [1.0, 2.0]}
    out = pe.apply_dp_to_weights(weights, noise_std=0.001)
    assert "a" in out
    assert len(out["a"]) == 2
