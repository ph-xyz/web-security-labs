from copy import deepcopy
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string, abort

app = Flask(__name__)
app.secret_key = "local-lab-secret-key-change-me"

INITIAL_USERS = {
    "demo@local.test": {
        "password": "password123",
        "account": {
            "id": 1042,
            "email": "demo@local.test",
            "created_at": "2026-01-18T10:34:12Z",
            "profile": {
                "display_name": "Carlos Silva",
                "timezone": "America/Sao_Paulo",
                "locale": "pt-BR",
                "avatar_url": ""
            },
            "billing": {
                "plan": "free",
                "trial_credits": 25,
                "payment_verified": False,
                "invoice_export_enabled": False
            },
            "workspace": {
                "id": "ws_alpha_01",
                "name": "Alpha Workspace",
                "role": "member",
                "seat_limit": 3
            },
            "entitlements": {
                "ai_assistant": False,
                "advanced_export": False,
                "admin_console": False,
                "audit_log": False
            },
            "security": {
                "mfa_enabled": False,
                "login_alerts": True
            }
        }
    },
    "admin@local.test": {
        "password": "not-the-user-password",
        "account": {
            "id": 1,
            "email": "admin@local.test",
            "created_at": "2025-10-03T08:00:00Z",
            "profile": {
                "display_name": "Admin User",
                "timezone": "UTC",
                "locale": "en-US",
                "avatar_url": ""
            },
            "billing": {
                "plan": "enterprise",
                "trial_credits": 9999,
                "payment_verified": True,
                "invoice_export_enabled": True
            },
            "workspace": {
                "id": "ws_alpha_01",
                "name": "Alpha Workspace",
                "role": "owner",
                "seat_limit": 250
            },
            "entitlements": {
                "ai_assistant": True,
                "advanced_export": True,
                "admin_console": True,
                "audit_log": True
            },
            "security": {
                "mfa_enabled": True,
                "login_alerts": True
            }
        }
    }
}

db = deepcopy(INITIAL_USERS)

LOGIN_HTML = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Workspace Lab</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 820px; margin: 42px auto; color: #202124; }
    .card { border: 1px solid #dadce0; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    input { width: 100%; padding: 10px; margin: 8px 0 14px; border: 1px solid #dadce0; border-radius: 6px; }
    button { padding: 10px 16px; border: 0; border-radius: 6px; cursor: pointer; }
    code { background: #f1f3f4; padding: 2px 5px; border-radius: 4px; }
    .muted { color: #5f6368; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Workspace Lab</h1>
    <p class="muted">Local SaaS workspace simulator.</p>
    <form method="post">
      <label>Email</label>
      <input name="email" value="demo@local.test">
      <label>Password</label>
      <input name="password" type="password" value="password123">
      <button type="submit">Entrar</button>
    </form>
  </div>
</body>
</html>
"""

APP_HTML = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Workspace Settings</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f8fafd; color: #202124; }
    header { background: white; border-bottom: 1px solid #dadce0; padding: 16px 28px; display: flex; justify-content: space-between; align-items: center; }
    main { max-width: 980px; margin: 28px auto; padding: 0 18px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .card { background: white; border: 1px solid #dadce0; border-radius: 12px; padding: 22px; box-shadow: 0 1px 2px rgba(0,0,0,.05); }
    input, select { width: 100%; padding: 9px; margin: 6px 0 14px; border: 1px solid #dadce0; border-radius: 6px; }
    button { padding: 9px 14px; border: 0; border-radius: 6px; cursor: pointer; }
    pre { background: #f1f3f4; padding: 12px; border-radius: 8px; overflow: auto; }
    a { color: #174ea6; text-decoration: none; margin-right: 12px; }
    .muted { color: #5f6368; }
    .pill { display: inline-block; padding: 3px 8px; border-radius: 999px; background: #eef3fe; }
  </style>
</head>
<body>
<header>
  <strong>Workspace Lab</strong>
  <nav>
    <a href="/app">Settings</a>
    <a href="/billing">Billing</a>
    <a href="/admin">Admin</a>
    <a href="/audit">Audit</a>
    <a href="/logout">Sair</a>
  </nav>
</header>

<main>
  <h1>Account settings</h1>
  <p class="muted">Gerencie sua conta e workspace.</p>

  <div class="grid">
    <section class="card">
      <h2>Editar perfil</h2>
      <label>Display name</label>
      <input id="display_name">
      <label>Timezone</label>
      <select id="timezone">
        <option>America/Sao_Paulo</option>
        <option>UTC</option>
        <option>America/New_York</option>
        <option>Europe/London</option>
      </select>
      <label>Locale</label>
      <select id="locale">
        <option>pt-BR</option>
        <option>en-US</option>
        <option>es-ES</option>
      </select>
      <button onclick="saveProfile()">Salvar</button>
      <p id="saveResult" class="muted"></p>
    </section>

    <section class="card">
      <h2>Workspace</h2>
      <p>Role: <span id="role" class="pill"></span></p>
      <p>Plan: <span id="plan" class="pill"></span></p>
      <p>Trial credits: <span id="credits" class="pill"></span></p>
      <p class="muted">Algumas áreas ficam bloqueadas dependendo do plano e permissões.</p>
    </section>
  </div>

  <section class="card" style="margin-top:18px;">
    <h2>Current account API response</h2>
    <pre id="account"></pre>
  </section>
</main>

<script>
async function loadMe() {
  const res = await fetch('/api/v1/me');
  const data = await res.json();

  document.getElementById('display_name').value = data.profile.display_name;
  document.getElementById('timezone').value = data.profile.timezone;
  document.getElementById('locale').value = data.profile.locale;
  document.getElementById('role').textContent = data.workspace.role;
  document.getElementById('plan').textContent = data.billing.plan;
  document.getElementById('credits').textContent = data.billing.trial_credits;
  document.getElementById('account').textContent = JSON.stringify(data, null, 2);
}

async function saveProfile() {
  const body = {
    profile: {
      display_name: document.getElementById('display_name').value,
      timezone: document.getElementById('timezone').value,
      locale: document.getElementById('locale').value
    }
  };

  const res = await fetch('/api/v1/account/profile', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });

  const data = await res.json();
  document.getElementById('saveResult').textContent = data.message || data.error;
  await loadMe();
}

loadMe();
</script>
</body>
</html>
"""

BLOCKED_HTML = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Blocked</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 760px; margin: 42px auto; }
    .card { border: 1px solid #dadce0; border-radius: 12px; padding: 24px; }
    a { color: #174ea6; }
  </style>
</head>
<body>
  <div class="card">
    <h1>403 Forbidden</h1>
    <p>{{ reason }}</p>
    <p><a href="/app">Voltar</a></p>
  </div>
</body>
</html>
"""

def current_record():
    email = session.get("email")
    if not email or email not in db:
        return None
    return db[email]

def current_account():
    record = current_record()
    if not record:
        return None
    return record["account"]

def require_login():
    if not current_record():
        return redirect(url_for("login"))
    return None

def deep_merge(target, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        elif key in target:
            target[key] = value

@app.route("/")
def index():
    if current_record():
        return redirect(url_for("app_page"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template_string(LOGIN_HTML)

    email = request.form.get("email", "")
    password = request.form.get("password", "")
    record = db.get(email)

    if not record or record["password"] != password:
        return render_template_string(LOGIN_HTML + "<p>Login inválido.</p>"), 401

    session["email"] = email
    return redirect(url_for("app_page"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/app")
def app_page():
    gate = require_login()
    if gate:
        return gate
    return render_template_string(APP_HTML)

@app.route("/billing")
def billing():
    gate = require_login()
    if gate:
        return gate

    account = current_account()
    if account["billing"]["plan"] not in ["pro", "enterprise"]:
        return render_template_string(BLOCKED_HTML, reason="Billing export requires a paid workspace."), 403

    if not account["entitlements"]["advanced_export"]:
        return render_template_string(BLOCKED_HTML, reason="Advanced export entitlement is not enabled."), 403

    return """
    <h1>Billing Export</h1>
    <p>Enterprise invoice export unlocked.</p>
    <p><strong>FLAG{workspace_billing_export_mass_assignment}</strong></p>
    <p><a href="/app">Voltar</a></p>
    """

@app.route("/admin")
def admin():
    gate = require_login()
    if gate:
        return gate

    account = current_account()
    if account["workspace"]["role"] not in ["admin", "owner"]:
        return render_template_string(BLOCKED_HTML, reason="Admin console requires workspace admin or owner role."), 403

    if not account["entitlements"]["admin_console"]:
        return render_template_string(BLOCKED_HTML, reason="Admin console entitlement is disabled."), 403

    return """
    <h1>Admin Console</h1>
    <p>Workspace administration unlocked.</p>
    <p><strong>FLAG{workspace_admin_console_mass_assignment}</strong></p>
    <p><a href="/app">Voltar</a></p>
    """

@app.route("/audit")
def audit():
    gate = require_login()
    if gate:
        return gate

    account = current_account()
    if account["workspace"]["role"] != "owner":
        return render_template_string(BLOCKED_HTML, reason="Audit logs require workspace owner role."), 403

    if not account["entitlements"]["audit_log"]:
        return render_template_string(BLOCKED_HTML, reason="Audit log entitlement is disabled."), 403

    return """
    <h1>Audit Log</h1>
    <p>Security audit log unlocked.</p>
    <p><strong>FLAG{workspace_audit_log_mass_assignment}</strong></p>
    <p><a href="/app">Voltar</a></p>
    """

@app.route("/api/v1/me")
def api_me():
    gate = require_login()
    if gate:
        return jsonify({"error": "unauthenticated"}), 401
    return jsonify(current_account()), 200

@app.route("/api/v1/account/profile", methods=["PATCH"])
def update_profile():
    gate = require_login()
    if gate:
        return jsonify({"error": "unauthenticated"}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON object required"}), 400

    account = current_account()

    # Vulnerable by design for this local lab:
    # The UI only sends account.profile fields, but the API recursively merges
    # any known key already present in the account object.
    deep_merge(account, payload)

    return jsonify({
        "message": "Account updated",
        "account": account
    }), 200

@app.route("/reset", methods=["GET", "POST"])
def reset():
    db.clear()
    db.update(deepcopy(INITIAL_USERS))
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)