import os
import re
import sys
import json
import hmac
import secrets
import subprocess
import urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HOST = os.environ.get("YUNAY_HOST", "127.0.0.1")
PORT = int(os.environ.get("YUNAY_PORT", "8000"))
BASE_WORKSPACE = os.environ.get("YUNAY_WORKSPACE", "/root")
CURRENT_PROJECT = os.environ.get("YUNAY_PROJECT", "/root/yunay-agent")
GITHUB_USER = os.environ.get("YUNAY_GITHUB_USER", "vermasushil1130-lab")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
PYTHON_BIN = sys.executable or "python3"
TOKEN_FILE = os.environ.get(
    "YUNAY_TOKEN_FILE", os.path.join(os.path.expanduser("~"), ".yunay_studio_token")
)


def _load_token():
    env_token = os.environ.get("YUNAY_TOKEN")
    if env_token:
        return env_token
    try:
        if os.path.isfile(TOKEN_FILE):
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                saved = f.read().strip()
            if saved:
                return saved
    except OSError:
        pass
    token = secrets.token_urlsafe(24)
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token)
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass
    return token


STUDIO_TOKEN = _load_token()
COOKIE = f"yunay_token={STUDIO_TOKEN}; Path=/; HttpOnly; SameSite=Strict; Max-Age=31536000"

AI_TIMEOUT = int(os.environ.get("YUNAY_AI_TIMEOUT", "240"))
CMD_TIMEOUT = int(os.environ.get("YUNAY_CMD_TIMEOUT", "60"))

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YUNAY AI Coding Studio v1.3</title>
<style>
  :root { --bg: #0f172a; --card: #1e293b; --accent: #38bdf8; --text: #f8fafc; --muted: #94a3b8; --green: #22c55e; --term: #020617; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
  body { background: var(--bg); color: var(--text); padding: 10px; max-width: 920px; margin: auto; }
  header { display: flex; justify-content: space-between; align-items: center; background: var(--card); padding: 12px 14px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #334155; }
  h1 { font-size: 1.1rem; color: var(--accent); }
  .badge { background: #0284c7; color: white; padding: 4px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: bold; }
  .repo-bar { background: #172033; padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; display: flex; gap: 8px; align-items: center; }
  .repo-bar select { margin: 0; flex: 1; }
  .tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 10px; }
  .tab { text-align: center; background: var(--card); padding: 10px 4px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.8rem; border: 1px solid #334155; }
  .tab.active { background: var(--accent); color: #0f172a; border-color: var(--accent); }
  .panel { display: none; background: var(--card); padding: 14px; border-radius: 10px; border: 1px solid #334155; }
  .panel.active { display: block; }
  label { font-size: 0.82rem; color: var(--muted); display: block; margin-top: 4px; }
  input, textarea, select { width: 100%; background: #0f172a; color: var(--text); border: 1px solid #334155; padding: 10px; border-radius: 8px; margin-top: 5px; margin-bottom: 10px; font-family: monospace; font-size: 0.88rem; }
  button { background: var(--accent); color: #0f172a; border: none; padding: 10px 12px; border-radius: 8px; font-weight: 700; cursor: pointer; width: 100%; margin-bottom: 8px; font-size: 0.85rem; }
  button.green { background: var(--green); color: #052e16; }
  button.secondary { background: #475569; color: white; }
  pre { background: var(--term); color: #38bdf8; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; white-space: pre-wrap; max-height: 250px; border: 1px solid #1e293b; margin-top: 6px; font-family: monospace; }
  .term-box { background: #000000; color: #4ade80; height: 220px; overflow-y: auto; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 0.82rem; border: 1px solid #22c55e44; white-space: pre-wrap; margin-bottom: 8px; }
  .row { display: flex; gap: 8px; }
  .cmd-card { background: #0f172a; border: 1px solid #334155; padding: 8px; border-radius: 6px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
  .cmd-card code { color: #38bdf8; font-size: 0.78rem; font-family: monospace; }
  .cmd-card span { font-size: 0.75rem; color: #94a3b8; }
</style>
</head>
<body>

<header>
  <h1>⚡ YUNAY AI Coding Studio</h1>
  <span class="badge">v1.3.0 Pro</span>
</header>

<div class="repo-bar">
  <span style="font-size:0.8rem; color:#94a3b8; white-space:nowrap;">📁 Repo:</span>
  <select id="projectSelect" onchange="switchProject()"></select>
  <button class="secondary" style="width:auto; margin:0;" onclick="loadProjects()">🔄</button>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('code', this)">📂 Editor</div>
  <div class="tab" onclick="switchTab('term', this)">💻 Terminal</div>
  <div class="tab" onclick="switchTab('ai', this)">🤖 AI Build</div>
  <div class="tab" onclick="switchTab('git', this)">🐙 GitHub</div>
</div>

<!-- TAB 1: EDITOR -->
<div id="tab-code" class="panel active">
  <label>Select File in Current Repo:</label>
  <div class="row">
    <select id="fileList" onchange="loadFile()"></select>
    <button class="secondary" style="width:auto;" onclick="fetchFiles()">🔄</button>
  </div>
  <input type="text" id="currentFile" placeholder="Filename (e.g. main.py)">
  <textarea id="codeArea" rows="11" placeholder="Select a file or create new..."></textarea>
  <div class="row">
    <button onclick="saveFile()">💾 Save Code</button>
    <button class="green" onclick="runFile()">🚀 Run File</button>
  </div>
  <button class="secondary" onclick="autoFixFile()">🔧 AI Auto-Fix Error</button>
  <pre id="runOutput">Terminal output will appear here...</pre>
</div>

<!-- TAB 2: SMART TERMINAL & COMMAND HELPER -->
<div id="tab-term" class="panel">
  <label>💡 Project-Wise Useful Commands (Tap to Run or Copy):</label>
  <div id="smartCmds" style="max-height: 140px; overflow-y: auto; margin-bottom: 8px;"></div>

  <div id="termScreen" class="term-box">root@yunay-studio:~# Terminal ready. Type or click any command below...</div>
  <div class="row">
    <input type="text" id="termInput" placeholder="Type Linux / Python / Git command..." style="margin:0;" onkeydown="if(event.key==='Enter')sendTermCmd()">
    <button class="green" style="width:auto; margin:0; padding:0 16px;" onclick="sendTermCmd()">Run ↵</button>
  </div>
</div>

<!-- TAB 3: AI BUILDER -->
<div id="tab-ai" class="panel">
  <label>Target File (Optional):</label>
  <input type="text" id="aiTargetFile" placeholder="e.g. app.py">
  <label>Ask YUNAY AI / Describe Code:</label>
  <textarea id="aiPrompt" rows="4" placeholder="e.g. Ek naya script banao..."></textarea>
  <button onclick="askAI()">✨ Generate with DeepSeek AI</button>
  <pre id="aiOutput">AI response will appear here...</pre>
</div>

<!-- TAB 4: GITHUB -->
<div id="tab-git" class="panel">
  <label>📥 Clone Repo from GitHub:</label>
  <div class="row">
    <select id="ghRepoList" onchange="selectGhRepo()">
      <option value="">-- Click Fetch Repos --</option>
    </select>
    <button class="secondary" style="width:auto;" onclick="fetchGithubRepos()">📥 Fetch</button>
  </div>
  <div class="row">
    <input type="text" id="cloneUrl" placeholder="https://github.com/..." style="margin:0;">
    <button style="width:auto; margin:0; white-space:nowrap;" onclick="cloneRepo()">⬇️ Clone</button>
  </div>
  <hr style="border:0; border-top:1px solid #334155; margin: 12px 0;">
  <button onclick="gitAction('status')">📊 Git Status</button>
  <button class="green" onclick="gitAction('push')">🚀 AI Smart Commit & Push</button>
  <pre id="gitOutput">Git logs...</pre>
</div>

<script>
const AUTH_TOKEN = "__AUTH_TOKEN__";

function switchTab(t, el) {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + t).classList.add('active');
  if (t === 'term') loadSmartCommands();
}

async function api(action, data = {}) {
  const res = await fetch('/api', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Auth-Token': AUTH_TOKEN },
    body: JSON.stringify({ action, ...data })
  });
  if (!res.ok) return { output: '❌ Request failed (' + res.status + ')' };
  return await res.json();
}

async function loadProjects() {
  const res = await api('list_projects');
  const sel = document.getElementById('projectSelect');
  sel.innerHTML = '';
  (res.projects || []).forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.path;
    opt.textContent = p.name;
    if (p.path === res.current) opt.selected = true;
    sel.appendChild(opt);
  });
  fetchFiles();
  loadSmartCommands();
}

async function switchProject() {
  const path = document.getElementById('projectSelect').value;
  const res = await api('switch_project', { path });
  if (res.message) document.getElementById('runOutput').textContent = res.message;
  fetchFiles();
  loadSmartCommands();
}

async function loadSmartCommands() {
  const res = await api('get_smart_cmds');
  const box = document.getElementById('smartCmds');
  box.innerHTML = '';
  (res.cmds || []).forEach(c => {
    const card = document.createElement('div');
    card.className = 'cmd-card';
    const info = document.createElement('div');
    const span = document.createElement('span');
    span.textContent = c.desc;
    const br = document.createElement('br');
    const code = document.createElement('code');
    code.textContent = c.cmd;
    info.append(span, br, code);
    const btns = document.createElement('div');
    btns.style.cssText = 'display:flex; gap:4px;';
    const copy = document.createElement('button');
    copy.className = 'secondary';
    copy.style.cssText = 'width:auto; padding:4px 8px; font-size:0.7rem; margin:0;';
    copy.textContent = '📋 Copy';
    copy.onclick = () => navigator.clipboard.writeText(c.cmd);
    const run = document.createElement('button');
    run.className = 'green';
    run.style.cssText = 'width:auto; padding:4px 8px; font-size:0.7rem; margin:0;';
    run.textContent = '▶ Run';
    run.onclick = () => runQuickCmd(c.cmd);
    btns.append(copy, run);
    card.append(info, btns);
    box.appendChild(card);
  });
}

async function fetchFiles() {
  const res = await api('list_files');
  const sel = document.getElementById('fileList');
  sel.innerHTML = '<option value="">-- Choose a file --</option>';
  (res.files || []).forEach(f => {
    const opt = document.createElement('option');
    opt.value = f; opt.textContent = f;
    sel.appendChild(opt);
  });
}

async function loadFile() {
  const fn = document.getElementById('fileList').value;
  if (!fn) return;
  document.getElementById('currentFile').value = fn;
  const res = await api('read_file', { filename: fn });
  document.getElementById('codeArea').value = res.content || '';
}

async function saveFile() {
  const fn = document.getElementById('currentFile').value.trim();
  if (!fn) { document.getElementById('runOutput').textContent = '⚠️ Filename khali hai!'; return; }
  const content = document.getElementById('codeArea').value;
  const res = await api('save_file', { filename: fn, content });
  document.getElementById('runOutput').textContent = res.message || res.output;
  fetchFiles();
}

async function runFile() {
  const fn = document.getElementById('currentFile').value.trim();
  if (!fn) { document.getElementById('runOutput').textContent = '⚠️ Filename khali hai!'; return; }
  document.getElementById('runOutput').textContent = '🚀 Running ' + fn + '...';
  const res = await api('run_file', { filename: fn });
  document.getElementById('runOutput').textContent = res.output;
}

async function autoFixFile() {
  const fn = document.getElementById('currentFile').value.trim();
  if (!fn) return;
  const err = document.getElementById('runOutput').textContent;
  document.getElementById('runOutput').textContent = '⏳ AI fixing ' + fn + '...';
  const res = await api('autofix', { filename: fn, error: err });
  document.getElementById('runOutput').textContent = res.output;
  if (res.fixed_code) document.getElementById('codeArea').value = res.fixed_code;
}

async function sendTermCmd() {
  const inp = document.getElementById('termInput');
  const cmd = inp.value.trim();
  if (!cmd) return;
  inp.value = '';
  runQuickCmd(cmd);
}

async function runQuickCmd(cmd) {
  const screen = document.getElementById('termScreen');
  const marker = '⏳ Running...';
  screen.textContent += `\n\n$ ${cmd}\n` + marker;
  screen.scrollTop = screen.scrollHeight;
  const res = await api('terminal', { cmd });
  const text = screen.textContent;
  screen.textContent = text.slice(0, text.length - marker.length) + (res.output || '');
  screen.scrollTop = screen.scrollHeight;
}

async function askAI() {
  const prompt = document.getElementById('aiPrompt').value;
  const filename = document.getElementById('aiTargetFile').value;
  if (!prompt.trim()) return;
  document.getElementById('aiOutput').textContent = '⏳ Thinking...';
  const res = await api('ask_ai', { prompt, filename });
  document.getElementById('aiOutput').textContent = res.output;
  fetchFiles();
}

async function fetchGithubRepos() {
  const res = await api('fetch_gh_repos');
  const sel = document.getElementById('ghRepoList');
  sel.innerHTML = '<option value="">-- Select Repo --</option>';
  (res.repos || []).forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.clone_url;
    opt.textContent = r.name + (r.private ? ' 🔒' : '');
    sel.appendChild(opt);
  });
  document.getElementById('gitOutput').textContent = res.message || '';
}

function selectGhRepo() {
  document.getElementById('cloneUrl').value = document.getElementById('ghRepoList').value;
}

async function cloneRepo() {
  const url = document.getElementById('cloneUrl').value.trim();
  if (!url) return;
  const res = await api('clone_repo', { url });
  document.getElementById('gitOutput').textContent = res.output;
  loadProjects();
}

async function gitAction(sub) {
  const res = await api('git', { sub });
  document.getElementById('gitOutput').textContent = res.output;
}

loadProjects();
</script>
</body>
</html>
"""

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YUNAY Studio — Login</title>
<style>
  body { background:#0f172a; color:#f8fafc; font-family:system-ui,sans-serif; display:flex; min-height:100vh; align-items:center; justify-content:center; margin:0; padding:16px; }
  .card { background:#1e293b; border:1px solid #334155; border-radius:12px; padding:22px; width:100%; max-width:420px; }
  h1 { color:#38bdf8; font-size:1.15rem; margin:0 0 6px; }
  p { color:#94a3b8; font-size:0.85rem; margin:0 0 14px; line-height:1.4; }
  input { width:100%; background:#0f172a; color:#f8fafc; border:1px solid #334155; padding:12px; border-radius:8px; font-family:monospace; font-size:0.9rem; box-sizing:border-box; }
  button { background:#38bdf8; color:#0f172a; border:none; padding:12px; border-radius:8px; font-weight:700; width:100%; margin-top:10px; cursor:pointer; font-size:0.9rem; }
  .err { color:#f87171; font-size:0.82rem; margin-top:10px; }
  code { background:#0f172a; padding:1px 5px; border-radius:4px; color:#38bdf8; }
</style>
</head>
<body>
<div class="card">
  <h1>⚡ YUNAY AI Studio</h1>
  <p>Access token daalein. Token terminal me printed link me hota hai:
  <code>?token=...</code> wala hissa.</p>
  __ERROR__
  <form method="POST" action="/login">
    <input type="password" name="token" placeholder="Studio token" autofocus autocomplete="off">
    <button type="submit">🔓 Login</button>
  </form>
</div>
</body>
</html>
"""


def extract_code_block(text):
    blocks = re.findall(r"```[ \t]*([a-zA-Z0-9_+-]*)[ \t]*\r?\n(.*?)```", text, re.DOTALL)
    python_blocks = [code for lang, code in blocks if lang.lower() in ("python", "py")]
    if python_blocks:
        return python_blocks[0].strip()
    return blocks[0][1].strip() if blocks else None


def safe_path(rel):
    base = os.path.realpath(CURRENT_PROJECT)
    target = os.path.realpath(os.path.join(base, rel))
    if target != base and not target.startswith(base + os.sep):
        raise ValueError("Path workspace ke bahar hai!")
    return target


def run_python_file(rel):
    fp = safe_path(rel)
    if not os.path.isfile(fp):
        return f"❌ File nahi mili: {rel}"
    try:
        res = subprocess.run(
            [PYTHON_BIN, fp],
            capture_output=True, text=True, timeout=CMD_TIMEOUT, cwd=CURRENT_PROJECT,
        )
        if res.returncode == 0:
            return f"✅ SUCCESS:\n{res.stdout or '(No output)'}"
        return f"❌ ERROR:\n{res.stderr or res.stdout}"
    except subprocess.TimeoutExpired:
        return f"⚠️ Timeout ({CMD_TIMEOUT}s) — code shayad input maang raha hai."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


def ai_fix(fn, err):
    fp = safe_path(fn)
    old_code = ""
    if os.path.isfile(fp):
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            old_code = f.read()
    prompt = (
        f"Fix the Python error in file '{fn}':\n{err}\n\n"
        f"Current code:\n{old_code}\n\n"
        f"Return the complete corrected Python code inside a ```python block."
    )
    try:
        res = subprocess.run(
            ["opencode", "run", "--dir", CURRENT_PROJECT, prompt],
            capture_output=True, text=True, timeout=AI_TIMEOUT, cwd=CURRENT_PROJECT,
        )
        ai_out = res.stdout.strip() or res.stderr.strip()
    except subprocess.TimeoutExpired:
        return None, f"⚠️ AI timeout ({AI_TIMEOUT}s)"
    except FileNotFoundError:
        return None, "❌ 'opencode' command nahi mili."
    except Exception as e:
        return None, f"⚠️ Error: {str(e)}"

    fixed_code = extract_code_block(ai_out)
    if fixed_code:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(fixed_code + "\n")
        return fixed_code, "✅ Bug Fixed & Saved!"
    return None, ai_out or "(Koi jawab nahi)"


def ask_ai(prompt, filename):
    try:
        res = subprocess.run(
            ["opencode", "run", "--dir", CURRENT_PROJECT, prompt],
            capture_output=True, text=True, timeout=AI_TIMEOUT, cwd=CURRENT_PROJECT,
        )
        ai_out = res.stdout.strip() or res.stderr.strip()
    except subprocess.TimeoutExpired:
        return f"⚠️ AI timeout ({AI_TIMEOUT}s)"
    except FileNotFoundError:
        return "❌ 'opencode' command nahi mili."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

    if filename:
        code = extract_code_block(ai_out)
        if code:
            fp = safe_path(filename)
            os.makedirs(os.path.dirname(fp) or CURRENT_PROJECT, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(code + "\n")
    return ai_out or "(Koi jawab nahi)"


def list_github_repos():
    headers = {"User-Agent": "YUNAY-Studio", "Accept": "application/vnd.github+json"}
    repos = []
    page = 1
    while True:
        if GITHUB_TOKEN:
            url = f"https://api.github.com/user/repos?sort=updated&per_page=100&page={page}"
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        else:
            url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data:
            break
        repos.extend(
            {"name": r["name"], "clone_url": r["clone_url"], "private": r.get("private", False)}
            for r in data
        )
        if len(data) < 100:
            break
        page += 1
    return repos


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[studio] " + (fmt % args) + "\n")

    def _send(self, code, body, content_type="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authed(self):
        token = self.headers.get("X-Auth-Token", "")
        return bool(token) and hmac.compare_digest(token, STUDIO_TOKEN)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            qs = parse_qs(parsed.query)
            supplied = (qs.get("token") or [""])[0]
            cookie = self.headers.get("Cookie", "")
            cookie_token = ""
            for part in cookie.split(";"):
                k, _, v = part.strip().partition("=")
                if k == "yunay_token":
                    cookie_token = v
            if hmac.compare_digest(supplied, STUDIO_TOKEN) or (
                cookie_token and hmac.compare_digest(cookie_token, STUDIO_TOKEN)
            ):
                page = HTML_PAGE.replace("__AUTH_TOKEN__", STUDIO_TOKEN)
                data = page.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Set-Cookie", COOKIE)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send(
                    401,
                    LOGIN_PAGE.replace("__ERROR__", ""),
                    "text/html; charset=utf-8",
                )
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        global CURRENT_PROJECT
        from urllib.parse import urlparse, parse_qs
        path = urlparse(self.path).path

        if path == "/login":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                raw = ""
            supplied = (parse_qs(raw).get("token") or [""])[0]
            if hmac.compare_digest(supplied, STUDIO_TOKEN):
                self.send_response(302)
                self.send_header("Set-Cookie", COOKIE)
                self.send_header("Location", "/")
                self.end_headers()
            else:
                self._send(
                    401,
                    LOGIN_PAGE.replace("__ERROR__", '<p class="err">❌ Galat token, dobara try karein.</p>'),
                    "text/html; charset=utf-8",
                )
            return

        if path != "/api":
            self._send(404, {"output": "not found"})
            return
        if not self._authed():
            self._send(401, {"output": "❌ Unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"output": "❌ Invalid JSON"})
            return

        action = body.get("action")
        response = {"output": ""}
        try:
            response = self._dispatch(action, body, response)
        except ValueError as e:
            self._send(400, {"output": f"❌ {e}"})
            return
        except Exception as e:
            self._send(500, {"output": f"⚠️ Server error: {e}"})
            return

        self._send(200, response)

    def _dispatch(self, action, body, response):
        global CURRENT_PROJECT

        if action == "list_projects":
            projects = []
            for item in sorted(os.listdir(BASE_WORKSPACE)):
                full_p = os.path.join(BASE_WORKSPACE, item)
                if os.path.isdir(full_p) and not item.startswith("."):
                    projects.append({"name": item, "path": full_p})
            response["projects"] = projects
            response["current"] = CURRENT_PROJECT

        elif action == "switch_project":
            new_p = os.path.realpath(body.get("path", ""))
            base = os.path.realpath(BASE_WORKSPACE)
            if not (new_p == base or new_p.startswith(base + os.sep)):
                response["message"] = "❌ Workspace ke bahar switch allowed nahi!"
            elif os.path.isdir(new_p):
                CURRENT_PROJECT = new_p
                response["message"] = f"✅ Switched to: {CURRENT_PROJECT}"
            else:
                response["message"] = "❌ Directory not found!"

        elif action == "get_smart_cmds":
            cmds = [
                {"desc": "📁 Current directory ki files dekhein", "cmd": "ls -la"},
                {"desc": "🐍 Python version check karein", "cmd": f"{os.path.basename(PYTHON_BIN)} --version"},
                {"desc": "📦 Installed Python libraries dekhein", "cmd": f"{PYTHON_BIN} -m pip list"},
                {"desc": "📊 Git status check karein", "cmd": "git status"},
                {"desc": "🌿 Git branch check karein", "cmd": "git branch"},
            ]
            if os.path.exists(os.path.join(CURRENT_PROJECT, "requirements.txt")):
                cmds.insert(0, {"desc": "📦 Requirements install karein", "cmd": f"{PYTHON_BIN} -m pip install -r requirements.txt"})
            py_files = [
                f for f in sorted(os.listdir(CURRENT_PROJECT))
                if f.endswith(".py") and not f.startswith("studio")
            ]
            if py_files:
                cmds.insert(0, {"desc": f"🚀 Main script run karein ({py_files[0]})", "cmd": f"{PYTHON_BIN} {py_files[0]}"})
            response["cmds"] = cmds

        elif action == "list_files":
            file_list = []
            for root, dirs, files in os.walk(CURRENT_PROJECT):
                dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "node_modules")]
                for f in sorted(files):
                    file_list.append(os.path.relpath(os.path.join(root, f), CURRENT_PROJECT))
            response["files"] = file_list[:500]

        elif action == "read_file":
            fp = safe_path(body.get("filename", ""))
            if os.path.isfile(fp):
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    response["content"] = f.read()
            else:
                response["content"] = ""
                response["output"] = "❌ File nahi mili"

        elif action == "save_file":
            fn = body.get("filename", "").strip()
            if not fn:
                raise ValueError("Filename zaroori hai")
            fp = safe_path(fn)
            os.makedirs(os.path.dirname(fp) or CURRENT_PROJECT, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(body.get("content", ""))
            response["message"] = f"✅ Saved {fn}!"

        elif action == "run_file":
            fn = body.get("filename", "").strip()
            if not fn:
                raise ValueError("Filename zaroori hai")
            response["output"] = run_python_file(fn)

        elif action == "autofix":
            fn = body.get("filename", "").strip()
            if not fn:
                raise ValueError("Filename zaroori hai")
            fixed, output = ai_fix(fn, body.get("error", ""))
            response["output"] = output
            if fixed:
                response["fixed_code"] = fixed

        elif action == "terminal":
            cmd = body.get("cmd", "").strip()
            if cmd.startswith("cd "):
                target = os.path.expanduser(cmd[3:].strip())
                new_dir = os.path.abspath(os.path.join(CURRENT_PROJECT, target))
                if os.path.isdir(new_dir):
                    CURRENT_PROJECT = new_dir
                    response["output"] = f"Changed directory to {CURRENT_PROJECT}"
                else:
                    response["output"] = f"bash: cd: {target}: No such directory"
            elif cmd:
                try:
                    res = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True,
                        timeout=CMD_TIMEOUT, cwd=CURRENT_PROJECT,
                    )
                    response["output"] = ((res.stdout or "") + (res.stderr or "")).strip() or "(Done)"
                except subprocess.TimeoutExpired:
                    response["output"] = f"⚠️ Timeout ({CMD_TIMEOUT}s)"
                except Exception as e:
                    response["output"] = f"Error: {str(e)}"

        elif action == "ask_ai":
            response["output"] = ask_ai(body.get("prompt", ""), body.get("filename", "").strip())

        elif action == "fetch_gh_repos":
            try:
                response["repos"] = list_github_repos()
                mode = "private+public" if GITHUB_TOKEN else "public only"
                response["message"] = f"✅ Loaded {len(response['repos'])} repos ({mode})!"
            except Exception as e:
                response["repos"] = []
                response["message"] = f"Error: {str(e)}"

        elif action == "clone_repo":
            url = body.get("url", "").strip()
            if not url.startswith(("https://", "git@")):
                raise ValueError("Valid git URL dein")
            repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
            if not re.fullmatch(r"[A-Za-z0-9._-]+", repo_name):
                raise ValueError("Repo name invalid hai")
            target_path = os.path.join(BASE_WORKSPACE, repo_name)
            if not os.path.exists(target_path):
                res = subprocess.run(
                    ["git", "clone", url, target_path],
                    capture_output=True, text=True, cwd=BASE_WORKSPACE,
                )
                if res.returncode == 0:
                    CURRENT_PROJECT = target_path
                    response["output"] = "✅ Cloned & switched successfully!"
                else:
                    response["output"] = f"❌ Clone error:\n{res.stderr or res.stdout}"
            else:
                CURRENT_PROJECT = target_path
                response["output"] = "ℹ️ Already exists, switched to it."

        elif action == "git":
            sub = body.get("sub")
            if sub == "status":
                res = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=CURRENT_PROJECT)
                response["output"] = f"📁 {CURRENT_PROJECT}\n\n" + (res.stdout or res.stderr)
            elif sub == "push":
                subprocess.run(["git", "add", "."], cwd=CURRENT_PROJECT)
                diff = subprocess.run(
                    ["git", "diff", "--cached", "--stat"],
                    capture_output=True, text=True, cwd=CURRENT_PROJECT,
                )
                if not diff.stdout.strip():
                    response["output"] = "ℹ️ Koi change nahi hai commit karne ke liye."
                else:
                    subprocess.run(
                        ["git", "commit", "-m", "feat: update via YUNAY Web Studio"],
                        capture_output=True, text=True, cwd=CURRENT_PROJECT,
                    )
                    res = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=CURRENT_PROJECT)
                    head = "✅ Pushed to GitHub!\n" if res.returncode == 0 else "❌ Push failed:\n"
                    response["output"] = head + (res.stdout or res.stderr)
            else:
                response["output"] = "❌ Unknown git action"

        else:
            response["output"] = f"❌ Unknown action: {action}"

        return response


def start_studio():
    url = f"http://{'localhost' if HOST in ('0.0.0.0', '') else HOST}:{PORT}/?token={STUDIO_TOKEN}"
    print("\n🌐 YUNAY AI Studio v1.3.0 chalu ho gaya hai!")
    print(f"👉 Browser mein kholein: {url}")
    print(f"   Workspace: {BASE_WORKSPACE}  |  Project: {CURRENT_PROJECT}")
    print(f"🔑 Token: {STUDIO_TOKEN}")
    print(f"   (Token file: {TOKEN_FILE} — restart par bhi same rehta hai)")
    if HOST == "0.0.0.0":
        print("⚠️  Server 0.0.0.0 par khula hai — koi bhi network se access kar sakta hai (token ke saath).")
    print("\n(Band karne ke liye Ctrl + C)\n")
    server = ThreadingHTTPServer((HOST, PORT), StudioHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Web Studio band kiya gaya.")
    finally:
        server.server_close()


if __name__ == "__main__":
    start_studio()
