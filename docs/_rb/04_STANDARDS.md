# 04_STANDARDS

## Code‑Regeln

- Kleine PRs, kleine Diffs.
- Keine "nur mal schnell alles formatieren" Aktionen.
- Naming: {{NAMING_RULES}}

## Architektur‑Regeln

- Trenne: domain / service / persistence / transport (wo sinnvoll)
- Keine Business‑Logik in Templates/UI‑Views.

## Logging

- Keine Secrets.
- Logs müssen debug‑fähig sein: request_id, user_id (wenn erlaubt), timings.
