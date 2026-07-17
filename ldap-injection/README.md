# LDAP Injection Lab

Small Flask and OpenLDAP lab created to practice LDAP injection through a login page.

The application inserts form input directly into an LDAP filter and prints the resulting filter in the logs. It is intentionally vulnerable and should only be used locally.

## Run

```bash
docker compose up --build
```

Open `http://localhost:5000`.

## Tests

Valid login:

```text
Username: alice
Password: wonderland123
```

Authentication bypass:

```text
Username: *
Password: *
```

View the generated filters:

```bash
docker logs ldap-app
```

The bypass produces:

```text
(&(uid=*)(userPassword=*))
```

Both conditions become presence checks, so LDAP returns an existing user without verifying valid credentials. The application authenticates the first returned entry.

## Fix

Escape LDAP special characters before building the filter:

```python
safe_username = escape_filter_chars(username)
safe_password = escape_filter_chars(password)
ldap_filter = f"(&(uid={safe_username})(userPassword={safe_password}))"
```

The vulnerable and corrected versions are included in `app.py` for comparison.
