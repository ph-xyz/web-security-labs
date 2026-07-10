// auth-context.js
const authState = {
  isAuthenticated: false,
  activeAccount: null,
  accountName: '',
  accountEmail: '',
  role: '',
  sessionId: ''
};

function handleUserDetails(user) {
  authState.isAuthenticated = true;
  authState.accountName = user.name;
  authState.accountEmail = user.username;
}

function renderAuthStatus(message, kind) {
  const box = document.getElementById('auth-status');
  if (!box) return;

  const klass = kind === 'ok' ? 'ok' : kind === 'error' ? 'error' : 'muted';
  box.innerHTML = `
    <h2>Auth status</h2>
    <p class="${klass}">${message}</p>
    <pre>${JSON.stringify(authState, null, 2)}</pre>
  `;
}

async function bootRecruiterPortal() {
  renderAuthStatus('Checking MSAL active account...', 'muted');

  if (authState.activeAccount) {
    handleUserDetails(authState.activeAccount);
  } else {
    const active = msal.instance.getActiveAccount();
    authState.activeAccount = active;

    if (active) {
      handleUserDetails(active);
    }
  }

  if (!authState.isAuthenticated) {
    renderAuthStatus('Not authenticated. The frontend did not find an active MSAL account.', 'error');
    return;
  }

  try {
    const session = await campusApi.startSession(authState.activeAccount);
    authState.sessionId = session.sessionId;
    authState.role = session.user.role;
    renderAuthStatus(`Authenticated as ${authState.accountName} (${authState.accountEmail}), role: ${authState.role}`, 'ok');

    const data = await campusApi.getStudents(authState.sessionId);
    renderStudents(data.students);
  } catch (err) {
    renderAuthStatus(err.message, 'error');
  }
}

function renderStudents(students) {
  const target = document.getElementById('students');
  if (!target) return;
  target.innerHTML = students.map(s => `
    <article class="student">
      <h3>${s.name}</h3>
      <p class="muted">${s.program}</p>
      <p><code>${s.email}</code></p>
      <p>${s.notes}</p>
    </article>
  `).join('');
}
