# 06_TEST_MATRIX

## Baseline (immer)

- `rb check` muss laufen und grün sein.

## Trigger‑Tests (wenn betroffen)

| Änderung                 | Trigger                       | Command                 |
| ------------------------ | ----------------------------- | ----------------------- |
| DB schema/migrations     | Migration‑Test + DB roundtrip | `pytest Jarvis_Development/tests/test_memory_interface.py` |
| Routing/External service | Golden/E2E                    | `python Jarvis_Development/src/heartbeat.py --once` |
| Frontend UI              | UI smoke                      | `n/a (Monaco Backend only)` |
| Auth/RBAC                | Permission tests              | `pytest Jarvis_Development/tests/ -v` |

## Mindestnachweis

- Jede Änderung muss entweder:
  - durch Tests abgedeckt sein, oder
  - einen reproduzierbaren manuellen Testschritt + Screenshot/Log liefern.
