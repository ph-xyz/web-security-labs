const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = process.env.PORT || 31338;
const PUBLIC_DIR = path.join(__dirname, 'public');

const API_KEY = 'campus-medium-public-api-key-2026';
const sessions = new Map();

const students = [
  { id: 'stu-1041', name: 'Lina Costa', program: 'Software Engineering', email: 'lina.costa@university.example', notes: 'Interview: backend internship' },
  { id: 'stu-1188', name: 'Mateus Lima', program: 'Cybersecurity', email: 'mateus.lima@university.example', notes: 'Strong web security portfolio' },
  { id: 'stu-1213', name: 'Ana Ribeiro', program: 'Data Science', email: 'ana.ribeiro@university.example', notes: 'Needs recruiter follow-up' }
];

const auditUsers = [
  { id: 'emp-001', name: 'Recruiter Admin', email: 'admin@corp.local', role: 'admin', department: 'Campus Recruiting' },
  { id: 'emp-014', name: 'Recruiter One', email: 'recruiter@corp.local', role: 'recruiter', department: 'Campus Recruiting' },
  { id: 'emp-061', name: 'Audit Viewer', email: 'audit.viewer@corp.local', role: 'auditor', department: 'Internal Audit' }
];

const roleByEmail = new Map([
  ['admin@corp.local', 'admin'],
  ['recruiter@corp.local', 'recruiter'],
  ['audit.viewer@corp.local', 'auditor']
]);

function sendJson(res, status, data) {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'content-type, x-api-key, x-session-id, authorization, x-client-view',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', chunk => {
      raw += chunk;
      if (raw.length > 1e6) req.destroy();
    });
    req.on('end', () => {
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch (err) {
        reject(err);
      }
    });
    req.on('error', reject);
  });
}

function hasApiKey(req) {
  return req.headers['x-api-key'] === API_KEY;
}

function getSession(req) {
  const id = req.headers['x-session-id'];
  if (!id) return null;
  return sessions.get(id) || null;
}

function serveStatic(req, res) {
  const safeUrl = decodeURIComponent(req.url.split('?')[0]);
  let filePath = safeUrl === '/' ? '/index.html' : safeUrl;
  filePath = path.normalize(filePath).replace(/^\.\.(\/|\\|$)/, '');
  const abs = path.join(PUBLIC_DIR, filePath);

  if (!abs.startsWith(PUBLIC_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(abs, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not found');
      return;
    }

    const ext = path.extname(abs).toLowerCase();
    const types = {
      '.html': 'text/html; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.json': 'application/json; charset=utf-8'
    };
    res.writeHead(200, {
      'Content-Type': types[ext] || 'application/octet-stream',
      'Cache-Control': 'no-store'
    });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === 'OPTIONS') {
    sendJson(res, 200, { ok: true });
    return;
  }

  try {
    if (url.pathname === '/api/session/start' && req.method === 'POST') {
      if (!hasApiKey(req)) {
        sendJson(res, 403, { error: 'Missing or invalid x-api-key' });
        return;
      }

      const body = await readBody(req);
      const account = body.account || {};
      const email = String(account.username || account.email || '').toLowerCase();
      const name = String(account.name || 'Unknown User');

      // INTENTIONAL VULNERABILITY:
      // The backend trusts the frontend-provided MSAL account object.
      // It does not validate a Microsoft Bearer token at all.
      if (!email.endsWith('@corp.local')) {
        sendJson(res, 401, { error: 'Only corp.local employees may start a recruiter session' });
        return;
      }

      const role = roleByEmail.get(email) || 'recruiter';
      const id = 'sess_' + crypto.randomBytes(10).toString('hex');
      const session = { id, email, name, role, createdAt: new Date().toISOString() };
      sessions.set(id, session);
      sendJson(res, 200, { sessionId: id, user: { email, name, role } });
      return;
    }

    if (url.pathname === '/api/me' && req.method === 'GET') {
      const session = getSession(req);
      if (!session) {
        sendJson(res, 401, { error: 'Missing or invalid session' });
        return;
      }
      sendJson(res, 200, { user: session });
      return;
    }

    if (url.pathname === '/api/students' && req.method === 'GET') {
      if (!hasApiKey(req)) {
        sendJson(res, 403, { error: 'Missing or invalid x-api-key' });
        return;
      }
      const session = getSession(req);
      if (!session) {
        sendJson(res, 401, { error: 'Missing recruiter session' });
        return;
      }
      sendJson(res, 200, { count: students.length, students });
      return;
    }

    if (url.pathname === '/api/audit/users' && req.method === 'GET') {
      if (!hasApiKey(req)) {
        sendJson(res, 403, { error: 'Missing or invalid x-api-key' });
        return;
      }
      const session = getSession(req);
      if (!session) {
        sendJson(res, 401, { error: 'Missing session' });
        return;
      }
      if (session.role !== 'admin' && session.role !== 'auditor') {
        sendJson(res, 403, { error: 'Admin or auditor role required' });
        return;
      }
      sendJson(res, 200, { count: auditUsers.length, users: auditUsers });
      return;
    }

    if (url.pathname === '/api/debug/health' && req.method === 'GET') {
      sendJson(res, 200, {
        status: 'ok',
        service: 'campus-recruiting-medium-lab',
        hint: 'Health checks are public. Real data APIs should not be.'
      });
      return;
    }

    serveStatic(req, res);
  } catch (err) {
    sendJson(res, 500, { error: 'Server error', detail: err.message });
  }
});

server.listen(PORT, () => {
  console.log(`Medium auth lab running at http://127.0.0.1:${PORT}`);
  console.log('Goal: access recruiter data without a real Microsoft login.');
});
