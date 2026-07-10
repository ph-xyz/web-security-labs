from flask import Flask, request, session, redirect, render_template_string, abort
from datetime import datetime
import random
import string

app = Flask(__name__)
app.secret_key = "dev-hard-v2-secret-do-not-use-in-prod"

# =========================
# Fake database
# =========================

USERS = {
    "wiener": {
        "password": "peter",
        "email": "wiener@bugcloud.local",
        "plan": "free",
        "vault": "Wiener's boring note: buy milk.",
    },
    "carlos": {
        "password": "not-the-path",
        "email": "carlos@bugcloud.local",
        "plan": "enterprise",
        "vault": "FLAG{session_puzzling_cross_flow_identity_confusion}",
    },
    "administrator": {
        "password": "adminpass",
        "email": "admin@bugcloud.local",
        "plan": "admin",
        "vault": "Admin vault. No flag here.",
    },
}

INBOX = {
    "wiener": [],
    "carlos": [],
    "administrator": [],
}

CASES = {}

def gen_code():
    return "".join(random.choice(string.digits) for _ in range(6))

def nav():
    return """
    <hr>
    <p>
      <a href="/">Home</a> |
      <a href="/login">Login</a> |
      <a href="/logout">Logout</a> |
      <a href="/recovery/start">Account recovery</a> |
      <a href="/account">Account</a> |
      <a href="/security">Security</a> |
      <a href="/vault">Vault</a> |
      <a href="/mailbox">Mailbox</a>
    </p>
    """

def page(body):
    return render_template_string(body + nav())

# =========================
# Public pages
# =========================

@app.route("/")
def home():
    return page("""
    <h1>BugCloud</h1>
    <p>Secure cloud workspace for teams.</p>
    <p><b>Known creds:</b> wiener:peter</p>
    <p><b>Goal:</b> get Carlos' vault flag without Carlos' password.</p>

    <h3>Public flows</h3>
    <ul>
      <li><a href="/recovery/start">Account recovery</a></li>
      <li><a href="/login">Login</a></li>
    </ul>

    <h3>Private flows</h3>
    <ul>
      <li><a href="/security">Security center</a></li>
      <li><a href="/vault">Private vault</a></li>
      <li><a href="/mailbox">Mailbox</a></li>
    </ul>
    """)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return page("""
        <h1>Login</h1>
        <form method="POST">
          <input name="username" placeholder="username">
          <input name="password" placeholder="password" type="password">
          <button>Login</button>
        </form>
        """)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return page("<h1>Invalid credentials</h1>"), 401

    # Intentional bug:
    # A secure app would clear pre-authentication state here.
    # This app keeps recovery/session context alive across login.
    session["auth_user"] = username
    session["logged_in"] = True

    return redirect("/account")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# Pre-auth flow: recovery
# =========================

@app.route("/recovery/start", methods=["GET", "POST"])
def recovery_start():
    if request.method == "GET":
        return page("""
        <h1>Account recovery</h1>
        <p>Start recovery for an account. This does not log you in.</p>

        <form method="POST">
          <input name="username" placeholder="username">
          <button>Start recovery</button>
        </form>
        """)

    username = request.form.get("username", "")

    # Generic outward response, but it stores a server-side session context.
    if username in USERS:
        case_id = "CASE-" + str(random.randint(10000, 99999))
        CASES[case_id] = {
            "subject": username,
            "created": datetime.utcnow().isoformat() + "Z",
            "status": "started",
        }

        # Intentional bug source:
        # "subject" means "account currently being recovered" in this flow.
        session["subject"] = username
        session["case_id"] = case_id
        session["recovery_started"] = True

    return redirect("/recovery/checklist")

@app.route("/recovery/checklist")
def recovery_checklist():
    return page("""
    <h1>Recovery checklist</h1>
    <p>If the account exists, a recovery case was started.</p>
    <p>For security, finish identity verification from the Security Center after login.</p>
    <p><a href="/login">Login to continue</a></p>
    """)

# =========================
# Private normal account
# =========================

@app.route("/account")
def account():
    if not session.get("logged_in"):
        return redirect("/login")

    username = session.get("auth_user")
    user = USERS.get(username)
    if not user:
        abort(403)

    return page(f"""
    <h1>Account</h1>
    <p>Logged in as: <b>{username}</b></p>
    <p>Email: {user["email"]}</p>
    <p>Plan: {user["plan"]}</p>
    <p>This page correctly uses <code>auth_user</code>.</p>
    """)

@app.route("/mailbox")
def mailbox():
    if not session.get("logged_in"):
        return redirect("/login")

    username = session.get("auth_user")
    messages = INBOX.get(username, [])

    items = ""
    if not messages:
        items = "<li>No messages.</li>"
    else:
        for m in reversed(messages):
            items += f"<li><b>{m['subject']}</b><br><pre>{m['body']}</pre></li>"

    return page(f"""
    <h1>Mailbox for {username}</h1>
    <ul>{items}</ul>
    """)

# =========================
# Security center / identity verification
# =========================

@app.route("/security", methods=["GET"])
def security():
    if not session.get("logged_in"):
        return redirect("/login")

    auth_user = session.get("auth_user")
    subject = session.get("subject", auth_user)

    return page(f"""
    <h1>Security Center</h1>
    <p>Authenticated user: <b>{auth_user}</b></p>
    <p>Active security subject: <b>{subject}</b></p>

    <h3>Step 1: Send verification code</h3>
    <form method="POST" action="/security/send-code">
      <button>Send code to my mailbox</button>
    </form>

    <h3>Step 2: Verify code</h3>
    <form method="POST" action="/security/verify-code">
      <input name="code" placeholder="6-digit code">
      <button>Verify</button>
    </form>

    <p>After successful verification, try the <a href="/vault">vault</a>.</p>
    """)

@app.route("/security/send-code", methods=["POST"])
def send_code():
    if not session.get("logged_in"):
        return redirect("/login")

    auth_user = session.get("auth_user")
    code = gen_code()

    # Correct part:
    # Code is sent to the currently authenticated user's mailbox.
    session["mfa_code_for_auth_user"] = code

    INBOX[auth_user].append({
        "subject": "BugCloud verification code",
        "body": f"Your verification code is: {code}",
    })

    return redirect("/mailbox")

@app.route("/security/verify-code", methods=["POST"])
def verify_code():
    if not session.get("logged_in"):
        return redirect("/login")

    code = request.form.get("code", "")
    expected = session.get("mfa_code_for_auth_user")

    if not expected or code != expected:
        return page("<h1>Invalid code</h1>"), 401

    auth_user = session.get("auth_user")

    # Intentional bug:
    # The MFA code belongs to auth_user, but the app unlocks the active "subject".
    # If "subject" came from recovery/start before login, this unlocks the wrong account.
    subject = session.get("subject", auth_user)

    session["verified_subject"] = subject
    session["security_verified"] = True

    return redirect("/vault")

# =========================
# Final target
# =========================

@app.route("/vault")
def vault():
    if not session.get("logged_in"):
        return redirect("/login")

    if not session.get("security_verified"):
        return page("""
        <h1>Vault locked</h1>
        <p>Verify your identity in the Security Center first.</p>
        <p><a href="/security">Go to Security Center</a></p>
        """), 403

    owner = session.get("verified_subject")
    if not owner or owner not in USERS:
        abort(403)

    vault_text = USERS[owner]["vault"]

    return page(f"""
    <h1>Private Vault</h1>
    <p>Vault owner: <b>{owner}</b></p>
    <pre>{vault_text}</pre>
    """)

# =========================
# Debug-ish endpoint intentionally not useful
# =========================

@app.route("/debug/session")
def debug_session():
    return page("""
    <h1>Debug disabled</h1>
    <p>Nice try. Map the flow instead.</p>
    """), 403

if __name__ == "__main__":
    print("[+] Session Puzzling Hard v2 running")
    print("[+] Known creds: wiener:peter")
    print("[+] Goal: get Carlos' vault flag without Carlos' password")
    print("[+] URL: http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)