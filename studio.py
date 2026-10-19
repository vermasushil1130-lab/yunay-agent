import os
import re
import json
import subprocess
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_WORKSPACE = "/root"
CURRENT_PROJECT = "/root/yunay-agent"
GITHUB_USER = "vermasushil1130-lab"
PORT = 8000

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YUNAY AI Coding Studio v1.2</title>
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
  <span class="badge">v1.2.0 Pro</span>
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
  <div id="smartCmds" style="max-height: 140px; overflow-y: auto; margin-bottom: 8px;">
    <!-- Dynamic project commands will load here -->
  </div>

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
function switchTab(t, el) {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + t).classList.add('active');
  if(t === 'term') loadSmartCommands();
}

async function api(action, data={}) {
  const res = await fetch('/api', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action, ...data})
  });
  return await res.json();
}

async function loadProjects() {
  const res = await api('list_projects');
  const sel = document.getElementById('projectSelect');
  sel.innerHTML = '';
  res.projects.forEach(p => {
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
  await api('switch_project', {path});
  fetchFiles();
  loadSmartCommands();
}

async function loadSmartCommands() {
  const res = await api('get_smart_cmds');
  const box = document.getElementById('smartCmds');
  box.innerHTML = '';
  res.cmds.forEach(c => {
    box.innerHTML += `
      <div class="cmd-card">
        <div><span>${c.desc}</span><br><code>${c.cmd}</code></div>
        <div style="display:flex; gap:4px;">
          <button class="secondary" style="width:auto; padding:4px 8px; font-size:0.7rem; margin:0;" onclick="navigator.clipboard.writeText('${c.cmd}')">📋 Copy</button>
          <button class="green" style="width:auto; padding:4px 8px; font-size:0.7rem; margin:0;" onclick="runQuickCmd('${c.cmd}')">▶ Run</button>
        </div>
      </div>`;
  });
}

async function fetchFiles() {
  const res = await api('list_files');
  const sel = document.getElementById('fileList');
  sel.innerHTML = '<option value="">-- Choose a file --</option>';
  res.files.forEach(f => {
    const opt = document.createElement('option');
    opt.value = f; opt.textContent = f;
    sel.appendChild(opt);
  });
}

async function loadFile() {
  const fn = document.getElementById('fileList').value;
  if (!fn) return;
  document.getElementById('currentFile').value = fn;
  const res = await api('read_file', {filename: fn});
  document.getElementById('codeArea').value = res.content || '';
}

async function saveFile() {
  const fn = document.getElementById('currentFile').value;
  const content = document.getElementById('codeArea').value;
  const res = await api('save_file', {filename: fn, content});
  document.getElementById('runOutput').textContent = res.message;
  fetchFiles();
}

async function runFile() {
  const fn = document.getElementById('currentFile').value;
  document.getElementById('runOutput').textContent = '🚀 Running ' + fn + '...';
  const res = await api('run_file', {filename: fn});
  document.getElementById('runOutput').textContent = res.output;
}

async function autoFixFile() {
  const fn = document.getElementById('currentFile').value;
  if (!fn) return;
  const err = document.getElementById('runOutput').textContent;
  document.getElementById('runOutput').textContent = '⏳ AI fixing ' + fn + '...';
  const res = await api('autofix', {filename: fn, error: err});
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
  screen.textContent += `\n\n$ ${cmd}\n⏳ Running...`;
  screen.scrollTop = screen.scrollHeight;
  const res = await api('terminal', {cmd});
  screen.textContent = screen.textContent.replace('⏳ Running...', res.output);
  screen.scrollTop = screen.scrollHeight;
}

async function askAI() {
  const prompt = document.getElementById('aiPrompt').value;
  const filename = document.getElementById('aiTargetFile').value;
  document.getElementById('aiOutput').textContent = '⏳ Thinking...';
  const res = await api('ask_ai', {prompt, filename});
  document.getElementById('aiOutput').textContent = res.output;
  fetchFiles();
}

async function fetchGithubRepos() {
  const res = await api('fetch_gh_repos');
  const sel = document.getElementById('ghRepoList');
  sel.innerHTML = '<option value="">-- Select Repo --</option>';
  (res.repos || []).forEach(r => {
    sel.innerHTML += `<option value="${r.clone_url}">${r.name}</option>`;
  });
  document.getElementById('gitOutput').textContent = res.message;
}

function selectGhRepo() {
  document.getElementById('cloneUrl').value = document.getElementById('ghRepoList').value;
}

async function cloneRepo() {
  const url = document.getElementById('cloneUrl').value.trim();
  if (!url) return;
  const res = await api('clone_repo', {url});
  document.getElementById('gitOutput').textContent = res.output;
  loadProjects();
}

async function gitAction(sub) {
  const res = await api('git', {sub});
  document.getElementById('gitOutput').textContent = res.output;
}

loadProjects();
</script>
</body>
</html>
"""

def extract_code_block(text):
    matches = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return matches[0].strip() if matches else None

class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        global CURRENT_PROJECT
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        action = body.get("action")
        response = {"output": ""}

        if action == "list_projects":
            projects = []
            for item in sorted(os.listdir(BASE_WORKSPACE)):
                full_p = os.path.join(BASE_WORKSPACE, item)
                if os.path.isdir(full_p) and not item.startswith("."):
                    projects.append({"name": item, "path": full_p})
            response["projects"] = projects
            response["current"] = CURRENT_PROJECT

        elif action == "switch_project":
            new_p = body.get("path", "")
            if os.path.isdir(new_p): CURRENT_PROJECT = new_p

        elif action == "get_smart_cmds":
            # Project ke hisab se zaroori commands detect karna
            cmds = [
                {"desc": "📁 Current directory ki files dekhein", "cmd": "ls -la"},
                {"desc": "🐍 Python version check karein", "cmd": "python --version"},
                {"desc": "📦 Installed Python libraries dekhein", "cmd": "pip list"},
                {"desc": "📊 Git status check karein", "cmd": "git status"},
                {"desc": "🌿 Git branch check karein", "cmd": "git branch"}
            ]
            # Agar requirements.txt hai toh pip install command dikhao
            if os.path.exists(os.path.join(CURRENT_PROJECT, "requirements.txt")):
                cmds.insert(0, {"desc": "📦 Requirements install karein", "cmd": "pip install -r requirements.txt"})
            
            # Agar koi .py file hai toh run command dikhao
            py_files = [f for f in os.listdir(CURRENT_PROJECT) if f.endswith(".py") and not f.startswith("studio")]
            if py_files:
                cmds.insert(0, {"desc": f"🚀 Main script run karein ({py_files[0]})", "cmd": f"python {py_files[0]}"})

            response["cmds"] = cmds

        elif action == "list_files":
            file_list = []
            for root, dirs, files in os.walk(CURRENT_PROJECT):
                dirs[:] = [d for d in dirs if d not in [".git", ".venv", "__pycache__", "node_modules"]]
                for f in sorted(files):
                    if not f.startswith("main_backup"):
                        file_list.append(os.path.relpath(os.path.join(root, f), CURRENT_PROJECT))
            response["files"] = file_list

        elif action == "read_file":
            fp = os.path.join(CURRENT_PROJECT, body.get("filename", ""))
            if os.path.exists(fp):
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    response["content"] = f.read()

        elif action == "save_file":
            fn = body.get("filename", "").strip()
            fp = os.path.join(CURRENT_PROJECT, fn)
            os.makedirs(os.path.dirname(fp) or CURRENT_PROJECT, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f: f.write(body.get("content", ""))
            response["message"] = f"✅ Saved {fn}!"

        elif action == "run_file":
            fn = body.get("filename", "").strip()
            fp = os.path.join(CURRENT_PROJECT, fn)
            try:
                res = subprocess.run(["python", fp], capture_output=True, text=True, timeout=40, cwd=CURRENT_PROJECT)
                response["output"] = f"✅ SUCCESS:\n{res.stdout or '(No output)'}" if res.returncode == 0 else f"❌ ERROR:\n{res.stderr or res.stdout}"
            except Exception as e: response["output"] = f"⚠️ Error: {str(e)}"

        elif action == "autofix":
            fn = body.get("filename", "").strip()
            err = body.get("error", "")
            fp = os.path.join(CURRENT_PROJECT, fn)
            old_code = open(fp, "r", encoding="utf-8").read() if os.path.exists(fp) else ""
            res = subprocess.run(["opencode", "run", "--dir", CURRENT_PROJECT, f"Fix error in '{fn}':\n{err}\nCode:\n{old_code}\nProvide full code in ```python block."], capture_output=True, text=True, cwd=CURRENT_PROJECT)
            ai_out = res.stdout.strip() or res.stderr.strip()
            fixed_code = extract_code_block(ai_out)
            if fixed_code:
                with open(fp, "w", encoding="utf-8") as f: f.write(fixed_code + "\n")
                response["fixed_code"] = fixed_code
                response["output"] = f"✅ Bug Fixed & Saved!"
            else: response["output"] = ai_out

        elif action == "terminal":
            cmd = body.get("cmd", "").strip()
            if cmd.startswith("cd "):
                target = cmd[3:].strip()
                new_dir = os.path.abspath(os.path.join(CURRENT_PROJECT, target))
                if os.path.isdir(new_dir):
                    CURRENT_PROJECT = new_dir
                    response["output"] = f"Changed directory to {CURRENT_PROJECT}"
                else:
                    response["output"] = f"bash: cd: {target}: No such directory"
            else:
                try:
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=CURRENT_PROJECT)
                    response["output"] = ((res.stdout or "") + (res.stderr or "")).strip() or "(Done)"
                except Exception as e: response["output"] = f"Error: {str(e)}"

        elif action == "ask_ai":
            prompt = body.get("prompt", "")
            fn = body.get("filename", "").strip()
            res = subprocess.run(["opencode", "run", "--dir", CURRENT_PROJECT, prompt], capture_output=True, text=True, cwd=CURRENT_PROJECT)
            ai_out = res.stdout.strip() or res.stderr.strip()
            if fn:
                code = extract_code_block(ai_out)
                if code:
                    with open(os.path.join(CURRENT_PROJECT, fn), "w", encoding="utf-8") as f: f.write(code + "\n")
            response["output"] = ai_out

        elif action == "fetch_gh_repos":
            try:
                url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=30"
                req = urllib.request.Request(url, headers={"User-Agent": "YUNAY-Studio"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    response["repos"] = [{"name": r["name"], "clone_url": r["clone_url"]} for r in data]
                    response["message"] = f"✅ Loaded {len(response['repos'])} repos!"
            except Exception as e: response["repos"] = []; response["message"] = f"Error: {str(e)}"

        elif action == "clone_repo":
            url = body.get("url", "").strip()
            repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
            target_path = os.path.join(BASE_WORKSPACE, repo_name)
            if not os.path.exists(target_path):
                res = subprocess.run(["git", "clone", url, target_path], capture_output=True, text=True, cwd=BASE_WORKSPACE)
                response["output"] = f"✅ Cloned successfully!" if res.returncode == 0 else res.stderr
            else:
                CURRENT_PROJECT = target_path
                response["output"] = f"ℹ️ Already exists, switched to it."

        elif action == "git":
            sub = body.get("sub")
            if sub == "status":
                res = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=CURRENT_PROJECT)
                response["output"] = res.stdout or res.stderr
            elif sub == "push":
                subprocess.run(["git", "add", "."], cwd=CURRENT_PROJECT)
                subprocess.run(["git", "commit", "-m", "feat: update via Web Studio"], cwd=CURRENT_PROJECT)
                res = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=CURRENT_PROJECT)
                response["output"] = ("✅ Pushed to GitHub!\n" if res.returncode == 0 else "❌ Push failed:\n") + (res.stdout or res.stderr)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

def start_studio():
    print(f"\n🌐 YUNAY AI Studio v1.2.0 Chalu Ho Gaya Hai!")
    print(f"👉 Browser mein dekhein: http://localhost:{PORT}\n")
    HTTPServer(("0.0.0.0", PORT), StudioHandler).serve_forever()

if __name__ == "__main__":
    start_studio()
