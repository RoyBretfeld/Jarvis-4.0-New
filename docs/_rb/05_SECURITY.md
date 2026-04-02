# 05_SECURITY

## Secrets

- Verboten im Repo: API‑Keys, Tokens, Passwörter, private keys.
- Verboten in Logs: Authorization Header, DB URLs, SMTP Passwörter.

## Auth/RBAC

- Rollen: {{ROLES}}
- Jede Datenabfrage ist mandanten‑sicher (scope by owner/tenant).

## Uploads

- Allowed MIME: {{ALLOWED_MIME}}
- Max size: {{MAX_UPLOAD_SIZE}}
- EXIF strip + Thumbnails (wenn Bilder)

## Injections

- SQL: prepared statements/ORM
- XSS: output escaping
- CSRF: token/cookie policy

## Audit/DSGVO (falls relevant)

- Wer hat was gesehen/gelöscht/geladen?
- Export/Löschung möglich.
