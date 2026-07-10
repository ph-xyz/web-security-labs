// Tiny fake MSAL-like bundle for this lab.
// In real production apps, this would usually be inside a minified chunk.
(function () {
  const vi = '@azure/msal-browser-demo';
  const yi = 'lab-medium-2.0.0';

  function PublicClientApplication(config) {
    this.clientId = config.clientId;
    this.packageName = vi;
    this.version = yi;
  }

  PublicClientApplication.prototype.getAllAccounts = function () {
    // Original behavior: no real Microsoft login happened, so no accounts exist.
    return [];
  };

  PublicClientApplication.prototype.getActiveAccount = function () {
    const accounts = this.getAllAccounts();

    if (accounts.length > 0) {
      return accounts[0];
    }

    return null;
  };

  window.msal = {
    instance: new PublicClientApplication({
      clientId: 'campus-recruiting-medium-client-id'
    })
  };
})();
