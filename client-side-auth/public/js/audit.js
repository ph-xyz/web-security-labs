// audit.js
(function () {
  async function bootAuditPortal() {
    await bootRecruiterPortal();

    const target = document.getElementById('audit-users');
    if (!target) return;

    if (!authState.sessionId) {
      target.innerHTML = '<p class="error">No session. Audit API not called.</p>';
      return;
    }

    try {
      const data = await campusApi.getAuditUsers(authState.sessionId);
      target.innerHTML = data.users.map(u => `
        <article class="student">
          <h3>${u.name}</h3>
          <p class="muted">${u.department}</p>
          <p><code>${u.email}</code></p>
          <p>Role: <strong>${u.role}</strong></p>
        </article>
      `).join('');
    } catch (err) {
      target.innerHTML = `<p class="error">${err.message}</p>`;
    }
  }

  bootAuditPortal();
})();
