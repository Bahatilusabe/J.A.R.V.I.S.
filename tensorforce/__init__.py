"""Minimal local stub of the `tensorforce` package used for tests and CI.

This stub exists so the repository's TensorForce wrapper can be exercised in
environments where the real `tensorforce` package (and its heavy deps like
TensorFlow/h5py) cannot be installed. It intentionally implements a tiny
compatible surface: `Agent.create(...)` returning an object with `act`,
`observe`, and `close` methods.

This is a test shim only and should not be used as a replacement for the
real library in production. If you later install the real `tensorforce`
package in your environment, Python's normal import resolution will prefer the
installed package over this local stub if the stub is removed.
"""

__version__ = "0.0-stub"

class _Agent:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def act(self, observation, deterministic: bool = False):
        # Very small deterministic policy: sum of observation mod num_actions
        try:
            # If actions spec was provided in kwargs, use it
            num_actions = self._kwargs.get("actions", {}).get("num_actions", 2)
        except Exception:
            num_actions = 2
        # Compute a simple deterministic action from observation
        try:
            s = 0
            if hasattr(observation, "__iter__"):
                for x in observation:
                    s += float(x)
            else:
                s = float(observation)
            return int(abs(int(s)) % max(1, int(num_actions)))
        except Exception:
            return 0

    def observe(self, reward=None, terminal=False):
        return

    def close(self):
        return


def Agent():
    """Compatibility function for `from tensorforce import Agent` usage.

    Returns a module-like factory with a `create` method so code that calls
    `Agent.create(...)` works against this stub.
    """

    class _Factory:
        @staticmethod
        def create(agent="ppo", states=None, actions=None, network=None, **kwargs):
            # Return a tiny agent implementing the minimal API used in the repo
            return _Agent(actions=actions or {})

    return _Factory()


# Backwards compatibility: allow `from tensorforce import Agent` to return
# the factory object directly.
Agent = Agent()
