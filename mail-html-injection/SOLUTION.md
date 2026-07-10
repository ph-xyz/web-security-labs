# Solution

1. Log in as `attacker@taskflow.local`.
2. Open the available task and post `@victim <b>test</b>` as a comment.
3. Open Mailpit at `http://localhost:8025`.
4. The website displays the tag as text, while the email renders it as HTML.

To verify the fix, set `SAFE_MODE: "true"` in `docker-compose.yml`, restart the containers and repeat the test. The email should display the tag as text.
