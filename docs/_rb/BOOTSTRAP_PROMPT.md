# MISSION: RB Bootstrap for {{PROJECT_NAME}}

## Context

We just copied the universal RB framework into this repo. Now adapt it to THIS project on first start.

## Goals

1. **Source of Truth**: Make `docs/_rb` the only normative source of truth.
2. **Facts**: Fill `docs/_rb/02_SYSTEM_FACTS.md` with the real tech stack, commands, and paths found in this repo.
3. **Gate**: Implement/adjust `rb check` so it runs:
   - `scripts/pre_commit_police.py`
   - one baseline smoke test (fast <30s) that exists in this repo
4. **Strategy**: Update `docs/_rb/06_TEST_MATRIX.md` with baseline + trigger tests.
5. **Security**: Adapt `scripts/pre_commit_police.py` to this project:
   - scan correct file extensions for this stack
   - block `.env` and secrets (hardened patterns)
   - enforce migration rule for this repo (schema change => migration in same commit)
6. **Safety**: Adapt `scripts/packer.py` include/exclude lists to this repo (never include secrets/db dumps).
7. **Memory**: Verify access to the central Error-DB at `E:\_____1111____Projekte-Programmierung\Antigravity\03_ERROR_DB.md` and ensure the project uses it for learning.

## Work rules

- Small diffs, max 5 files per patch.
- Always show diff and run `rb check` after changes.
- **Final output**: Diff summary + exact commands run + outputs + evidence that police blocks a fake secret and migration rule triggers.
