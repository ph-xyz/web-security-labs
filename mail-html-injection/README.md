# Mail HTML Injection Lab

A local lab I used to understand HTML injection in email notifications.

**Requirements:** Docker Desktop with Docker Compose.

**Run:**
```bash
docker compose up
```

App: `http://localhost:3000` · Inbox: `http://localhost:8025`.

**Credentials:** `attacker@taskflow.local:attacker123` and `victim@taskflow.local:victim123`.

**Objective:** determine whether comment content is handled differently by the web UI and email template.

**Skills practiced:**
- HTML injection testing
- Transactional email flow analysis
- Context-specific output handling

> Intentionally vulnerable. Use only locally or in authorized environments.

[Hint](HINT.md) · [Solution](SOLUTION.md)
