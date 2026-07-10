# Session Puzzling Lab

A local lab I used to practice session puzzling across different account flows.

**Requirements:** Python 3, Burp Suite and a browser.

**Run:**
```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5001`.

**Credentials:** `wiener:peter`; target user: `carlos`.

**Objective:** access the target user's private vault without knowing the target password.

**Skills practiced:**
- Multi-step workflow analysis
- Session-state testing
- State confusion across application flows

> Intentionally vulnerable. Use only locally or in authorized environments.

[Hint](HINT.md) · [Solution](SOLUTION.md)
