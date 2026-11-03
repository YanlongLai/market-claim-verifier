V4 preparation validation. Full offline verification is pending; exact logs will be retained here.

First targeted invocation: `demo/.venv/bin/python -m pytest -q demo/tests/test_v4.py` — **6 passed in 1.17 s**; `node --test demo/tests/motion-v4.test.mjs` — **3 passed**. These are the tool-reported results; no historical shell log is reconstructed.

First explicit checks: `realworld.py --check`, `motion_v4.py --check`, `scale_v4.py --check` all passed. A final retained invocation covers the completed source.
