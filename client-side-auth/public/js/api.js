// api.js
(function () {
  function getConfig() {
    if (!window.__CAMPUS_CONFIG__) throw new Error('Missing campus config');
    return window.__CAMPUS_CONFIG__;
  }

  async function startSession(account) {
    const cfg = getConfig();
    const response = await fetch(cfg.apiBase + '/api/session/start', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        [cfg.headers.apiKeyHeader]: cfg.getApiKey(),
        // This header looks official, but the backend ignores it.
        // A secure backend would require Authorization: Bearer <real MSAL token>.
        'x-client-view': 'recruiter'
      },
      body: JSON.stringify({ account })
    });

    if (!response.ok) {
      throw new Error('Session failed: HTTP ' + response.status);
    }

    return response.json();
  }

  async function getStudents(sessionId) {
    const cfg = getConfig();
    const response = await fetch(cfg.apiBase + '/api/students', {
      method: 'GET',
      headers: {
        [cfg.headers.apiKeyHeader]: cfg.getApiKey(),
        [cfg.headers.sessionHeader]: sessionId
      }
    });

    if (!response.ok) {
      throw new Error('Students failed: HTTP ' + response.status);
    }

    return response.json();
  }

  async function getAuditUsers(sessionId) {
    const cfg = getConfig();
    const response = await fetch(cfg.apiBase + '/api/audit/users', {
      method: 'GET',
      headers: {
        [cfg.headers.apiKeyHeader]: cfg.getApiKey(),
        [cfg.headers.sessionHeader]: sessionId
      }
    });

    if (!response.ok) {
      throw new Error('Audit failed: HTTP ' + response.status);
    }

    return response.json();
  }

  window.campusApi = {
    startSession,
    getStudents,
    getAuditUsers
  };
})();
