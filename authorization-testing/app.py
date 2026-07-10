from flask import Flask, request, redirect, make_response, render_template_string, jsonify
import secrets, json

app = Flask(__name__)

USERS = {
    "alice": {"password":"alicepass","role":"member","orgs":["org-alpha"],"email":"alice@alpha.local","display":"Alice A."},
    "bob": {"password":"bobpass","role":"member","orgs":["org-beta"],"email":"bob@beta.local","display":"Bob B."},
    "carlos": {"password":"carlospass","role":"manager","orgs":["org-alpha"],"email":"carlos@alpha.local","display":"Carlos M."},
    "diana": {"password":"dianapass","role":"manager","orgs":["org-beta"],"email":"diana@beta.local","display":"Diana M."},
    "root": {"password":"rootpass","role":"global_admin","orgs":["org-alpha","org-beta"],"email":"root@platform.local","display":"Root Admin"},
}
PROJECTS = {
    "PROJ-A-100":{"org":"org-alpha","owner":"alice","name":"Alpha Checkout Refactor","secret":"alpha-checkout-db-readonly"},
    "PROJ-A-200":{"org":"org-alpha","owner":"carlos","name":"Alpha Refund Console","secret":"alpha-refund-service-key"},
    "PROJ-B-100":{"org":"org-beta","owner":"bob","name":"Beta Card Vault","secret":"beta-cardvault-limited-key"},
    "PROJ-B-900":{"org":"org-beta","owner":"diana","name":"Beta Fraud Rules","secret":"beta-fraud-rules-prod-key"},
}
DOCUMENTS = {
    "DOC-A-1":{"org":"org-alpha","owner":"alice","title":"Alpha onboarding notes","body":"Alice private onboarding notes."},
    "DOC-A-2":{"org":"org-alpha","owner":"carlos","title":"Manager escalation playbook","body":"Manager-only Alpha escalation playbook."},
    "DOC-B-1":{"org":"org-beta","owner":"bob","title":"Beta support checklist","body":"Bob private support checklist."},
    "DOC-B-2":{"org":"org-beta","owner":"diana","title":"Beta risk memo","body":"Diana private risk memo."},
}
INVOICES = {
    "INV-A-101":{"org":"org-alpha","owner":"alice","amount":120,"note":"Alpha testing credits"},
    "INV-A-900":{"org":"org-alpha","owner":"carlos","amount":4400,"note":"Alpha manager tooling"},
    "INV-B-101":{"org":"org-beta","owner":"bob","amount":80,"note":"Beta starter usage"},
    "INV-B-900":{"org":"org-beta","owner":"diana","amount":9900,"note":"Beta fraud platform"},
}
TICKETS = {
    "TCK-A-1":{"org":"org-alpha","owner":"alice","title":"Cannot export report"},
    "TCK-A-2":{"org":"org-alpha","owner":"carlos","title":"Approve Alpha refund batch"},
    "TCK-B-1":{"org":"org-beta","owner":"bob","title":"Card vault alert"},
    "TCK-B-2":{"org":"org-beta","owner":"diana","title":"Fraud rule exception"},
}
REPORTS = {
    "RPT-A-777":{"org":"org-alpha","title":"Alpha revenue export","content":"Revenue export for Alpha Retail."},
    "RPT-B-777":{"org":"org-beta","title":"Beta card risk export","content":"Risk export for Beta Finance."},
}
REFUNDS = {
    "REF-A-500":{"org":"org-alpha","owner":"alice","amount":30,"approved":False},
    "REF-B-500":{"org":"org-beta","owner":"bob","amount":70,"approved":False},
}
AUDIT_LOG = {
    "org-alpha":[{"time":"2026-06-22 10:12","actor":"carlos","action":"reviewed Alpha refunds"},{"time":"2026-06-22 11:44","actor":"alice","action":"opened Alpha report"}],
    "org-beta":[{"time":"2026-06-22 09:02","actor":"diana","action":"changed Beta fraud rule"},{"time":"2026-06-22 12:10","actor":"bob","action":"opened card vault"}],
}
SESSIONS, TOKENS, SUSPENDED = {}, {}, set()

def issue_session(username):
    sid, csrf, token = secrets.token_hex(18), secrets.token_hex(12), secrets.token_urlsafe(30)
    SESSIONS[sid] = {"username": username, "csrf": csrf}
    TOKENS[token] = username
    return sid, csrf, token

def session_auth():
    data = SESSIONS.get(request.cookies.get("session_id"))
    return (data["username"], data) if data else (None, None)

def bearer_auth():
    value = request.headers.get("Authorization","")
    if not value.startswith("Bearer "): return None
    return TOKENS.get(value.split(" ",1)[1].strip())

def auth_any():
    u = bearer_auth()
    if u: return u, "bearer"
    u, s = session_auth()
    if u: return u, "cookie"
    return None, None

def require_session():
    u, s = session_auth()
    if not u: return None, make_response(jsonify({"error":"Not authenticated"}), 401)
    return (u, s), None

def require_bearer():
    u = bearer_auth()
    if not u: return None, make_response(jsonify({"error":"Bearer token required"}), 401)
    return u, None

def role(u): return USERS[u]["role"]
def is_admin(u): return role(u) == "global_admin"
def is_manager_or_admin(u): return role(u) in ("manager","global_admin")
def user_in_org(u, org): return is_admin(u) or org in USERS[u]["orgs"]
def bound_csrf_ok(u, token): return any(d["username"] == u and d["csrf"] == token for d in SESSIONS.values())
def any_csrf_ok(token): return any(d["csrf"] == token for d in SESSIONS.values())

def list_links(items, kind):
    return "\n".join(f'<li><a href="/api/v1/{kind}/{i}">{i}</a> — {v.get("title") or v.get("name") or v.get("note")}</li>' for i,v in items.items())

def page(title, body):
    u, sess = session_auth()
    top = '<a href="/login">Login</a>'
    if u:
        token = next((t for t,x in TOKENS.items() if x == u), "")
        top = f'''<b>Logged in:</b> {u} | <b>role:</b> {USERS[u]["role"]} | <b>orgs:</b> {", ".join(USERS[u]["orgs"])}
        | <a href="/dashboard">Dashboard</a> | <a href="/api-console">API Console</a> | <a href="/graphql-console">GraphQL Console</a> | <a href="/logout">Logout</a>
        <div class="small">CSRF: <code>{sess["csrf"]}</code><br>Bearer token: <code>{token}</code></div>'''
    return render_template_string(f'''<!doctype html><html><head><title>{title}</title><style>
    body{{margin:0;font-family:Arial,sans-serif;background:#f3f4f6;color:#111827}} header{{background:#0f172a;color:white;padding:18px 28px}}
    nav{{background:white;border-bottom:1px solid #d1d5db;padding:14px 28px}} main{{padding:24px 28px;max-width:1100px}}
    a{{color:#2563eb;text-decoration:none}} .card{{background:white;border-radius:10px;padding:16px 18px;margin:14px 0;box-shadow:0 1px 4px #0002}}
    code{{background:#eef2ff;padding:2px 5px;border-radius:4px}} pre{{background:#111827;color:#e5e7eb;padding:12px;border-radius:8px;overflow:auto}}
    input,button{{padding:8px;margin:4px}} button{{cursor:pointer}} .small{{font-size:12px;color:#374151;margin-top:8px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
    </style></head><body><header><h1>OrbitOps Portal — Autorize Hard Lab</h1></header><nav>{top}</nav><main>{body}</main></body></html>''')

@app.route("/")
def index():
    return page("Home", '''<div class="card"><h2>Hard authorization lab</h2><p>Treine Autorize com cookies, Bearer, CSRF, GraphQL, endpoints seguros, falsos positivos e bugs reais.</p><p><a href="/login">Entrar</a></p></div>
    <div class="card"><h3>Contas</h3><pre>alice:alicepass   member org-alpha
bob:bobpass       member org-beta
carlos:carlospass manager org-alpha
diana:dianapass   manager org-beta
root:rootpass     global_admin</pre></div>''')

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return page("Login", '<div class="card"><h2>Login</h2><form method="post"><input name="username" placeholder="username"><input name="password" type="password" placeholder="password"><button>Login</button></form></div>')
    username, password = request.form.get("username",""), request.form.get("password","")
    if username not in USERS or USERS[username]["password"] != password: return make_response("Invalid login", 403)
    sid, csrf, token = issue_session(username)
    resp = redirect("/dashboard")
    resp.set_cookie("session_id", sid, httponly=True, samesite="Lax")
    resp.set_cookie("workspace_hint", USERS[username]["orgs"][0], samesite="Lax")
    resp.set_cookie("ui_theme", "dark" if username in ("bob","diana") else "light")
    return resp

@app.route("/logout")
def logout():
    sid = request.cookies.get("session_id")
    SESSIONS.pop(sid, None)
    resp = redirect("/")
    for c in ("session_id","workspace_hint","ui_theme"): resp.delete_cookie(c)
    return resp

@app.route("/dashboard")
def dashboard():
    auth, err = require_session()
    if err: return err
    u, sess = auth
    owned_docs = {k:v for k,v in DOCUMENTS.items() if v["owner"] == u}
    visible_projects = {k:v for k,v in PROJECTS.items() if user_in_org(u, v["org"])}
    owned_invoices = {k:v for k,v in INVOICES.items() if v["owner"] == u}
    visible_tickets = {k:v for k,v in TICKETS.items() if v["owner"] == u or is_manager_or_admin(u)}
    admin_area = ""
    if is_manager_or_admin(u):
        admin_area = f'''<div class="card"><h3>Manager/Admin links</h3><ul>
        <li><a href="/api/v1/admin/users">/api/v1/admin/users</a></li>
        <li><a href="/api/v1/orgs/org-alpha/audit-log">Alpha audit log</a></li>
        <li><a href="/api/v1/orgs/org-beta/audit-log">Beta audit log</a></li></ul>
        <h4>Suspend user</h4><form method="post" action="/api/v1/admin/users/bob/suspend"><input type="hidden" name="csrf" value="{sess["csrf"]}"><button>Suspend bob</button></form>
        <h4>Approve refund</h4><form method="post" action="/api/v1/refunds/REF-B-500/approve"><input type="hidden" name="csrf" value="{sess["csrf"]}"><button>Approve REF-B-500</button></form></div>'''
    return page("Dashboard", f'''<div class="grid"><div class="card"><h2>Current user</h2><p><a href="/api/v1/me">/api/v1/me</a></p><p><a href="/api/v1/preferences">/api/v1/preferences</a> <span class="small">safe current-user endpoint</span></p><p><a href="/api/v1/public/profiles/{u}">Public profile</a></p></div>
    <div class="card"><h2>Report export</h2><p>Use Repeater para testar <code>X-Org-ID</code>.</p><ul><li><a href="/api/v1/reports/RPT-A-777/export">RPT-A-777</a></li><li><a href="/api/v1/reports/RPT-B-777/export">RPT-B-777</a></li></ul></div></div>
    <div class="card"><h3>Projects visible</h3><ul>{list_links(visible_projects, "projects")}</ul></div>
    <div class="card"><h3>Your documents</h3><ul>{list_links(owned_docs, "documents")}</ul></div>
    <div class="card"><h3>Your invoices</h3><ul>{list_links(owned_invoices, "invoices")}</ul></div>
    <div class="card"><h3>Tickets visible</h3><ul>{list_links(visible_tickets, "tickets")}</ul></div>{admin_area}''')

@app.route("/api-console")
def api_console():
    auth, err = require_session()
    if err: return err
    u, sess = auth
    token = next((t for t,x in TOKENS.items() if x == u), "")
    return page("API Console", f'''<div class="card"><h2>Bearer-token API console</h2><p>Esses botões fazem requests com <code>Authorization: Bearer</code>. Cookie sozinho não autentica <code>/api/v2/*</code>.</p>
    <p><b>Token:</b> <code>{token}</code></p>
    <button onclick="callApi('/api/v2/me')">GET /api/v2/me</button>
    <button onclick="callApi('/api/v2/billing/invoices/INV-A-900')">GET INV-A-900</button>
    <button onclick="callApi('/api/v2/billing/invoices/INV-B-900')">GET INV-B-900</button>
    <button onclick="postApi('/api/v2/projects/PROJ-B-900/rotate-secret')">POST rotate PROJ-B-900</button>
    <button onclick="callApi('/api/v2/admin/feature-flags')">GET admin feature flags</button>
    <pre id="out">click a button</pre></div>
    <script>
    const token = {json.dumps(token)};
    async function callApi(path){{const r=await fetch(path,{{headers:{{'Authorization':'Bearer '+token,'Accept':'application/json'}}}});document.getElementById('out').textContent=r.status+"\\n"+await r.text();}}
    async function postApi(path){{const r=await fetch(path,{{method:'POST',headers:{{'Authorization':'Bearer '+token,'Accept':'application/json'}}}});document.getElementById('out').textContent=r.status+"\\n"+await r.text();}}
    </script>''')

@app.route("/graphql-console")
def graphql_console():
    auth, err = require_session()
    if err: return err
    u, sess = auth
    token = next((t for t,x in TOKENS.items() if x == u), "")
    return page("GraphQL Console", f'''<div class="card"><h2>GraphQL-like console</h2><button onclick="gql('GetCurrentUser',{{}})">GetCurrentUser</button><button onclick="gql('GetTicket',{{id:'TCK-B-2'}})">GetTicket TCK-B-2</button><button onclick="gql('AdminStats',{{}})">AdminStats</button><pre id="out">click a button</pre></div>
    <script>
    const token = {json.dumps(token)};
    async function gql(operationName, variables){{const body=JSON.stringify({{operationName,variables,query:'query '+operationName+' {{ dummy }}'}});const r=await fetch('/graphql',{{method:'POST',headers:{{'Authorization':'Bearer '+token,'Content-Type':'application/json'}},body}});document.getElementById('out').textContent=r.status+"\\n"+await r.text();}}
    </script>''')

@app.route("/api/v1/me")
def v1_me():
    auth, err = require_session()
    if err: return err
    u, sess = auth
    return jsonify({"username":u,"role":role(u),"orgs":USERS[u]["orgs"],"email":USERS[u]["email"]})

@app.route("/api/v1/preferences")
def v1_preferences():
    auth, err = require_session()
    if err: return err
    u, sess = auth
    return jsonify({"owner":u,"timezone":"America/Sao_Paulo","theme":request.cookies.get("ui_theme","light"),"note":"Safe endpoint: current user's own preferences."})

@app.route("/api/v1/public/profiles/<username>")
def public_profile(username):
    if username not in USERS: return make_response(jsonify({"error":"not found"}), 404)
    return jsonify({"username":username,"display":USERS[username]["display"],"public":True,"note":"Public profile by design."})

@app.route("/api/v1/projects/<project_id>")
def v1_project(project_id):
    auth, err = require_session()
    if err: return err
    p = PROJECTS.get(project_id)
    if not p: return make_response(jsonify({"error":"project not found"}), 404)
    return jsonify({"id":project_id,**p,"flag":"FLAG{hard_bola_project_cross_org}","vulnerability":"BOLA: authenticated user can read project from another org"})

@app.route("/api/v1/documents/<doc_id>")
def v1_document(doc_id):
    auth, err = require_session()
    if err: return err
    d = DOCUMENTS.get(doc_id)
    if not d: return make_response(jsonify({"error":"document not found"}), 404)
    return jsonify({"id":doc_id,**d,"flag":"FLAG{hard_bola_private_document}","vulnerability":"BOLA: document owner check missing"})

@app.route("/api/v1/invoices/<invoice_id>")
def v1_invoice(invoice_id):
    auth, err = require_session()
    if err: return err
    inv = INVOICES.get(invoice_id)
    if not inv: return make_response(jsonify({"error":"invoice not found"}), 404)
    return jsonify({"id":invoice_id,**inv,"flag":"FLAG{hard_bola_invoice_cookie}","vulnerability":"BOLA: invoice owner/org check missing"})

@app.route("/api/v1/tickets/<ticket_id>")
def v1_ticket(ticket_id):
    auth, err = require_session()
    if err: return err
    u, sess = auth
    t = TICKETS.get(ticket_id)
    if not t: return make_response(jsonify({"error":"ticket not found"}), 404)
    if role(u) == "member" and t["owner"] != u:
        if role(t["owner"]) == "manager":
            return make_response(jsonify({"error":"manager-owned tickets are protected"}), 403)
        return jsonify({"id":ticket_id,**t,"flag":"FLAG{hard_rest_ticket_bola}","vulnerability":"BOLA: user can read another member's ticket"})
    if not is_manager_or_admin(u) and t["owner"] != u: return make_response(jsonify({"error":"ticket access denied"}), 403)
    if is_manager_or_admin(u) and not user_in_org(u, t["org"]): return make_response(jsonify({"error":"wrong org"}), 403)
    return jsonify({"id":ticket_id,**t})

@app.route("/api/v1/orgs/<org_id>/audit-log")
def v1_audit_log(org_id):
    auth, err = require_session()
    if err: return err
    u, sess = auth
    if not is_manager_or_admin(u) or not user_in_org(u, org_id): return make_response(jsonify({"error":"manager/admin in this org only"}), 403)
    return jsonify({"org":org_id,"audit_log":AUDIT_LOG.get(org_id,[])})

@app.route("/api/v1/admin/users")
def v1_admin_users():
    auth, err = require_session()
    if err: return err
    return jsonify({"users":[{"username":u,"role":d["role"],"orgs":d["orgs"],"email":d["email"]} for u,d in USERS.items()],"flag":"FLAG{hard_bfla_admin_users_cookie}","vulnerability":"BFLA: admin user listing lacks role check"})

@app.route("/api/v1/admin/users/<target>/suspend", methods=["POST"])
def v1_suspend_user(target):
    auth, err = require_session()
    if err: return err
    u, sess = auth
    csrf = request.form.get("csrf") or request.headers.get("X-CSRF-Token","")
    if not any_csrf_ok(csrf): return make_response(jsonify({"error":"csrf invalid"}), 403)
    if target not in USERS: return make_response(jsonify({"error":"target not found"}), 404)
    SUSPENDED.add(target)
    return jsonify({"status":"suspended","target":target,"performed_by":u,"flag":"FLAG{hard_bfla_suspend_action_csrf_misbound}","vulnerability":"BFLA + CSRF token not bound to actor"})

@app.route("/api/v1/refunds/<refund_id>/approve", methods=["POST"])
def v1_approve_refund(refund_id):
    auth, err = require_session()
    if err: return err
    u, sess = auth
    csrf = request.form.get("csrf") or request.headers.get("X-CSRF-Token","")
    if not bound_csrf_ok(u, csrf): return make_response(jsonify({"error":"csrf bound to different session"}), 403)
    r = REFUNDS.get(refund_id)
    if not r: return make_response(jsonify({"error":"refund not found"}), 404)
    if not is_manager_or_admin(u) or not user_in_org(u, r["org"]): return make_response(jsonify({"error":"manager/admin in refund org only"}), 403)
    r["approved"] = True
    return jsonify({"status":"approved","refund":refund_id,"approved_by":u})

@app.route("/api/v1/reports/<report_id>/export")
def v1_report_export(report_id):
    auth, err = require_session()
    if err: return err
    rep = REPORTS.get(report_id)
    if not rep: return make_response(jsonify({"error":"report not found"}), 404)
    requested_org = request.headers.get("X-Org-ID") or request.cookies.get("workspace_hint")
    if requested_org != rep["org"]: return make_response(jsonify({"error":"wrong org context; set X-Org-ID"}), 403)
    return jsonify({"id":report_id,**rep,"flag":"FLAG{hard_trusted_header_x_org_id}","vulnerability":"Trusted client-controlled org header/cookie"})

@app.route("/api/v2/me")
def v2_me():
    u, err = require_bearer()
    if err: return err
    return jsonify({"username":u,"role":role(u),"auth":"bearer"})

@app.route("/api/v2/billing/invoices/<invoice_id>")
def v2_invoice(invoice_id):
    u, err = require_bearer()
    if err: return err
    inv = INVOICES.get(invoice_id)
    if not inv: return make_response(jsonify({"error":"invoice not found"}), 404)
    return jsonify({"id":invoice_id,**inv,"flag":"FLAG{hard_bola_bearer_invoice}","vulnerability":"BOLA in bearer-token API"})

@app.route("/api/v2/projects/<project_id>/rotate-secret", methods=["POST"])
def v2_rotate_secret(project_id):
    u, err = require_bearer()
    if err: return err
    p = PROJECTS.get(project_id)
    if not p: return make_response(jsonify({"error":"project not found"}), 404)
    p["secret"] = "rotated-" + secrets.token_hex(5)
    return jsonify({"project":project_id,"rotated_by":u,"new_secret_preview":p["secret"],"flag":"FLAG{hard_bfla_v2_rotate_secret}","vulnerability":"BFLA: token holder can rotate any project secret"})

@app.route("/api/v2/admin/feature-flags")
def v2_admin_flags():
    u, err = require_bearer()
    if err: return err
    if not is_admin(u): return make_response(jsonify({"error":"global admin only"}), 403)
    return jsonify({"flags":{"newAdminConsole":True,"billingV2":True,"riskEngine":"beta"}})

@app.route("/graphql", methods=["POST"])
def graphql():
    u, mode = auth_any()
    if not u: return make_response(jsonify({"errors":[{"message":"auth required"}]}), 401)
    try: data = request.get_json(force=True)
    except Exception: return make_response(jsonify({"errors":[{"message":"invalid json"}]}), 400)
    op, variables = data.get("operationName"), data.get("variables") or {}
    if op == "GetCurrentUser": return jsonify({"data":{"currentUser":{"username":u,"role":role(u),"auth":mode}}})
    if op == "AdminStats":
        if not is_admin(u): return make_response(jsonify({"errors":[{"message":"global admin only"}]}), 403)
        return jsonify({"data":{"adminStats":{"users":len(USERS),"orgs":2}}})
    if op == "GetTicket":
        tid = variables.get("id")
        t = TICKETS.get(tid)
        if not t: return make_response(jsonify({"errors":[{"message":"ticket not found"}]}), 404)
        return jsonify({"data":{"ticket":{"id":tid,**t,"flag":"FLAG{hard_graphql_ticket_bola}","vulnerability":"BOLA in GraphQL resolver"}}})
    return make_response(jsonify({"errors":[{"message":"unknown operation"}]}), 400)

@app.route("/debug/sessions")
def debug_sessions():
    return jsonify({"sessions":{sid[:8]+"...":d for sid,d in SESSIONS.items()},"tokens":{tok[:10]+"...":u for tok,u in TOKENS.items()},"suspended":list(SUSPENDED)})

@app.route("/reset", methods=["POST"])
def reset():
    SUSPENDED.clear()
    REFUNDS["REF-A-500"]["approved"] = False
    REFUNDS["REF-B-500"]["approved"] = False
    return jsonify({"status":"reset mutable state"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
