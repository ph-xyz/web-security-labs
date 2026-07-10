# Authorization Testing Lab

A local lab I used to practice authorization testing across users and roles.

**Requirements:** Python 3, Burp Suite and the Autorize extension.

**Run:**
```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5001`.

**Credentials:** `alice:alicepass`, `bob:bobpass`, `carlos:carlospass`, `root:rootpass`.

**Objective:** identify authorization failures by comparing requests across users and roles.

**Skills practiced:**
- Horizontal and vertical authorization testing
- Cookie and bearer-token comparison
- BOLA and BFLA validation

> Intentionally vulnerable. Use only locally or in authorized environments.

[Hint](HINT.md) · [Solution](SOLUTION.md)
