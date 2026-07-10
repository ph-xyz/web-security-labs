// main.bundle.js - intentionally readable route hints for the lab.
(function () {
  const routes = [
    '/studentEventSelector',
    '/login.html',
    '/recruiter.html',
    '/audit.html',
    '/configureEvent',
    '/selectRecruitmentLeads'
  ];

  const chunks = [
    '/js/config.chunk.js',
    '/js/msal-bundle.js',
    '/js/auth-context.js',
    '/js/api.js',
    '/js/audit.js'
  ];

  window.__APP_MANIFEST__ = {
    app: 'campus-recruiting-medium-lab',
    routes,
    chunks,
    note: 'Routes in JS are not the bug. Sensitive APIs responding without real auth are the bug.'
  };
})();
