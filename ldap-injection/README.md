# LDAP Injection Lab

Small Flask and OpenLDAP lab created to practice LDAP injection.

The login endpoint inserts user input directly into an LDAP filter and prints the resulting filter in the application logs. This project is intentionally vulnerable and should only be used locally.

## Run

```bash
docker compose up --build
```

The application will be available at `http://localhost:5000`.

## Tests

Valid login:

```bash
curl -i -X POST http://localhost:5000/login \
  -d "username=alice" \
  -d "password=wonderland123"
```

Authentication bypass:

```bash
curl -i -X POST http://localhost:5000/login \
  -d "username=*" \
  -d "password=*"
```

View the generated filters:

```bash
docker logs ldap-app
```

The injected values produce this filter:

```text
(&(uid=*)(userPassword=*))
```

Both conditions become presence checks, so LDAP returns an existing user without verifying valid credentials. The application then authenticates the first returned entry.

## Fix

Escape LDAP special characters before building the filter:

```python
safe_username = escape_filter_chars(username)
safe_password = escape_filter_chars(password)
ldap_filter = f"(&(uid={safe_username})(userPassword={safe_password}))"
```

The vulnerable and corrected versions are included in `app.py` for comparison.
