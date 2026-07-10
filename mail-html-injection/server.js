const express = require("express");
const cookieParser = require("cookie-parser");
const nodemailer = require("nodemailer");
const escapeHtml = require("escape-html");

const app = express();
const PORT = 3000;
const SAFE_MODE = process.env.SAFE_MODE === "true";

app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || "localhost",
  port: Number(process.env.SMTP_PORT || 1025),
  secure: false
});

const users = [
  {
    id: 1,
    name: "Pedro",
    handle: "pedro",
    email: "attacker@taskflow.local",
    password: "attacker123"
  },
  {
    id: 2,
    name: "Victim User",
    handle: "victim",
    email: "victim@taskflow.local",
    password: "victim123"
  }
];

const projects = [
  {
    id: 42,
    name: "Acme Security Review",
    members: [1, 2]
  }
];

const tasks = [
  {
    id: 1001,
    projectId: 42,
    title: "Review onboarding security checklist",
    status: "In progress",
    assigneeId: 2,
    description: "Check account recovery, invite links, and email notifications before launch."
  },
  {
    id: 1002,
    projectId: 42,
    title: "Document SOC escalation path",
    status: "Open",
    assigneeId: 1,
    description: "Write the first version of the incident escalation process."
  }
];

const comments = [
  {
    id: 1,
    taskId: 1001,
    authorId: 2,
    body: "Initial note: remember to test invite and notification emails.",
    createdAt: new Date().toISOString()
  }
];

function findCurrentUser(req) {
  const userId = Number(req.cookies.session_user_id);
  return users.find((user) => user.id === userId) || null;
}

function requireLogin(req, res, next) {
  const user = findCurrentUser(req);
  if (!user) return res.redirect("/login");
  req.user = user;
  next();
}

function layout(title, body, user = null) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} · TaskFlow</title>
  <style>
    :root { color-scheme: light dark; }
    body { margin: 0; font-family: Arial, sans-serif; background: #f3f5f7; color: #17202a; }
    header { background: #1f2937; color: white; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
    header a { color: white; margin-left: 12px; }
    main { max-width: 980px; margin: 28px auto; padding: 0 20px; }
    .card { background: white; border: 1px solid #d9dee5; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
    .muted { color: #6b7280; }
    .pill { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e5e7eb; font-size: 12px; }
    .task { display: block; padding: 14px; border: 1px solid #e5e7eb; border-radius: 10px; margin: 10px 0; text-decoration: none; color: inherit; }
    .task:hover { background: #f9fafb; }
    input, textarea { width: 100%; box-sizing: border-box; padding: 10px; border: 1px solid #cfd6df; border-radius: 8px; font: inherit; }
    textarea { min-height: 110px; }
    button { background: #2563eb; color: white; border: 0; border-radius: 8px; padding: 10px 14px; cursor: pointer; font-weight: 700; }
    button:hover { background: #1d4ed8; }
    .comment { border-left: 4px solid #d1d5db; padding-left: 12px; margin: 14px 0; white-space: pre-wrap; }
    .warning { background: #fff7ed; border-color: #fed7aa; }
    code { background: #eef2f7; padding: 2px 5px; border-radius: 4px; }
  </style>
</head>
<body>
  <header>
    <div><b>TaskFlow</b> <span class="muted">Project workspace</span></div>
    <nav>
      ${user ? `Signed in as ${escapeHtml(user.name)} · <a href="/logout">Logout</a>` : `<a href="/login">Login</a>`}
    </nav>
  </header>
  <main>${body}</main>
</body>
</html>`;
}

function renderMentionedHandles(rawText) {
  const matches = rawText.match(/@([a-zA-Z0-9_-]+)/g) || [];
  const handles = [...new Set(matches.map((handle) => handle.slice(1).toLowerCase()))];
  return users.filter((user) => handles.includes(user.handle));
}

function renderCommentForWeb(commentBody) {
  // The web page is intentionally safe. This makes the email bug less obvious.
  return escapeHtml(commentBody);
}

function renderCommentForEmail(commentBody) {
  // Vulnerable mode: raw user input is inserted into the HTML email.
  // Safe mode: input is escaped before line breaks are converted.
  const value = SAFE_MODE ? escapeHtml(commentBody) : commentBody;
  return value.replace(/\n/g, "<br>");
}

function renderEmailTemplate({ recipient, actor, task, project, commentBody }) {
  const commentHtml = renderCommentForEmail(commentBody);

  return `
  <div style="font-family:Arial,sans-serif;background:#f6f8fb;padding:24px;color:#111827">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;margin:auto;background:white;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
      <tr>
        <td style="background:#111827;color:white;padding:18px 22px;font-size:18px;font-weight:bold">
          TaskFlow
        </td>
      </tr>
      <tr>
        <td style="padding:22px">
          <p style="margin-top:0">Hi ${escapeHtml(recipient.name)},</p>

          <p>
            <b>${escapeHtml(actor.name)}</b> mentioned you in a comment on
            <b>${escapeHtml(task.title)}</b> inside
            <b>${escapeHtml(project.name)}</b>.
          </p>

          <div style="border-left:4px solid #2563eb;background:#f9fafb;padding:14px 16px;margin:18px 0">
            ${commentHtml}
          </div>

          <p style="margin-bottom:0">
            <a href="http://localhost:3000/tasks/${task.id}" style="display:inline-block;background:#2563eb;color:white;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:bold">
              Open task
            </a>
          </p>
        </td>
      </tr>
      <tr>
        <td style="border-top:1px solid #e5e7eb;padding:14px 22px;color:#6b7280;font-size:12px">
          This notification was sent by TaskFlow because you were mentioned in a project comment.
        </td>
      </tr>
    </table>
  </div>`;
}

async function sendMentionEmail({ recipient, actor, task, project, commentBody }) {
  const html = renderEmailTemplate({ recipient, actor, task, project, commentBody });

  await transporter.sendMail({
    from: '"TaskFlow Notifications" <notifications@taskflow.local>',
    to: recipient.email,
    subject: `${actor.name} mentioned you on "${task.title}"`,
    html
  });
}

app.get("/", requireLogin, (req, res) => {
  const project = projects[0];
  const body = `
    <div class="card">
      <h1>${escapeHtml(project.name)}</h1>
      <p class="muted">Internal project board. Mention a teammate in a task comment using <code>@victim</code>.</p>
      <p><span class="pill">SAFE_MODE: ${SAFE_MODE}</span></p>
    </div>

    <div class="card">
      <h2>Tasks</h2>
      ${tasks.map((task) => {
        const assignee = users.find((user) => user.id === task.assigneeId);
        return `<a class="task" href="/tasks/${task.id}">
          <b>${escapeHtml(task.title)}</b><br>
          <span class="muted">${escapeHtml(task.status)} · Assigned to ${escapeHtml(assignee.name)}</span>
        </a>`;
      }).join("")}
    </div>
  `;
  res.send(layout("Dashboard", body, req.user));
});

app.get("/login", (req, res) => {
  const body = `
    <div class="card">
      <h1>Login</h1>
      <p class="muted">Use the attacker account to post a comment. Use Mailpit to read notification emails.</p>
      <form method="POST" action="/login">
        <label>Email</label><br>
        <input name="email" value="attacker@taskflow.local"><br><br>
        <label>Password</label><br>
        <input name="password" type="password" value="attacker123"><br><br>
        <button type="submit">Sign in</button>
      </form>
    </div>

    <div class="card warning">
      <b>Accounts</b>
      <p><code>attacker@taskflow.local</code> / <code>attacker123</code></p>
      <p><code>victim@taskflow.local</code> / <code>victim123</code></p>
    </div>
  `;
  res.send(layout("Login", body));
});

app.post("/login", (req, res) => {
  const email = String(req.body.email || "").toLowerCase();
  const password = String(req.body.password || "");
  const user = users.find((candidate) => candidate.email === email && candidate.password === password);

  if (!user) {
    return res.status(401).send(layout("Login failed", `<div class="card"><h1>Login failed</h1><p>Invalid credentials.</p><p><a href="/login">Try again</a></p></div>`));
  }

  res.cookie("session_user_id", String(user.id), { httpOnly: true, sameSite: "lax" });
  res.redirect("/");
});

app.get("/logout", (req, res) => {
  res.clearCookie("session_user_id");
  res.redirect("/login");
});

app.get("/tasks/:id", requireLogin, (req, res) => {
  const task = tasks.find((candidate) => candidate.id === Number(req.params.id));
  if (!task) return res.status(404).send("Task not found");

  const project = projects.find((candidate) => candidate.id === task.projectId);
  const taskComments = comments.filter((comment) => comment.taskId === task.id);
  const assignee = users.find((user) => user.id === task.assigneeId);

  const body = `
    <div class="card">
      <p><a href="/">← Back to dashboard</a></p>
      <h1>${escapeHtml(task.title)}</h1>
      <p>${escapeHtml(task.description)}</p>
      <p><span class="pill">${escapeHtml(task.status)}</span> <span class="muted">Assigned to ${escapeHtml(assignee.name)}</span></p>
    </div>

    <div class="card">
      <h2>Comments</h2>
      ${taskComments.map((comment) => {
        const author = users.find((user) => user.id === comment.authorId);
        return `<div class="comment">
          <b>${escapeHtml(author.name)}</b> <span class="muted">${new Date(comment.createdAt).toLocaleString()}</span><br>
          ${renderCommentForWeb(comment.body)}
        </div>`;
      }).join("")}
    </div>

    <div class="card">
      <h2>Add comment</h2>
      <p class="muted">Mention <code>@victim</code> to trigger an email notification.</p>
      <form method="POST" action="/tasks/${task.id}/comments">
        <textarea name="body" placeholder="Write a comment..."></textarea><br><br>
        <button type="submit">Post comment</button>
      </form>
    </div>
  `;

  res.send(layout(task.title, body, req.user));
});

app.post("/tasks/:id/comments", requireLogin, async (req, res) => {
  const task = tasks.find((candidate) => candidate.id === Number(req.params.id));
  if (!task) return res.status(404).send("Task not found");

  const project = projects.find((candidate) => candidate.id === task.projectId);
  const body = String(req.body.body || "");

  const comment = {
    id: comments.length + 1,
    taskId: task.id,
    authorId: req.user.id,
    body,
    createdAt: new Date().toISOString()
  };
  comments.push(comment);

  const mentionedUsers = renderMentionedHandles(body)
    .filter((user) => user.id !== req.user.id)
    .filter((user) => project.members.includes(user.id));

  for (const recipient of mentionedUsers) {
    await sendMentionEmail({
      recipient,
      actor: req.user,
      task,
      project,
      commentBody: body
    });
  }

  res.redirect(`/tasks/${task.id}`);
});

app.get("/health", (req, res) => {
  res.json({ ok: true, safeMode: SAFE_MODE });
});

app.listen(PORT, () => {
  console.log(`TaskFlow lab running at http://localhost:${PORT}`);
  console.log(`SAFE_MODE=${SAFE_MODE}`);
});
