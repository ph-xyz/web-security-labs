from flask import Flask, request
from ldap3 import Server, Connection
from ldap3.utils.conv import escape_filter_chars

app = Flask(__name__)


@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    server = Server("ldap")
    conn = Connection(
        server,
        user="cn=admin,dc=lab,dc=local",
        password="admin",
        auto_bind=True
    )

    # Intentionally vulnerable: user input is interpolated into the LDAP filter.
    ldap_filter = f"(&(uid={username})(userPassword={password}))"

    # Secure version: escape special LDAP filter characters before interpolation.
    # safe_username = escape_filter_chars(username)
    # safe_password = escape_filter_chars(password)
    # ldap_filter = f"(&(uid={safe_username})(userPassword={safe_password}))"

    # Printed intentionally so the generated filter can be inspected in the lab.
    print(ldap_filter, flush=True)

    conn.search(
        "ou=users,dc=lab,dc=local",
        ldap_filter,
        attributes=["uid", "cn"]
    )

    if conn.entries:
        return f"Login successful: {conn.entries[0].uid}", 200

    return "Invalid credentials", 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
