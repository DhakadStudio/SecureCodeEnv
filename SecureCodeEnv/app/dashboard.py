"""SecureCodeEnv - Interactive HTML Dashboard"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SecureCodeEnv — RL Playground</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@500;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#07090d;--surface:#0d1117;--s2:#161b22;--s3:#21262d;
  --border:#30363d;--accent:#f0883e;--a2:#79c0ff;--a3:#56d364;
  --danger:#ff7b72;--warn:#e3b341;--text:#e6edf3;--muted:#8b949e;
  --mono:'JetBrains Mono',monospace;--sans:'Syne',sans-serif;
  --radius:8px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans)}
body{display:flex;flex-direction:column;min-height:100vh}

body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(240,136,62,.025) 1px,transparent 1px),
  linear-gradient(90deg,rgba(240,136,62,.025) 1px,transparent 1px);
  background-size:48px 48px;pointer-events:none;z-index:0}

/* ── header ── */
header{position:sticky;top:0;z-index:200;background:rgba(7,9,13,.88);
  backdrop-filter:blur(12px);border-bottom:1px solid var(--border);
  padding:0 24px;height:52px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.hlogo{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-weight:700;font-size:14px;color:var(--accent)}
.hlogo-icon{width:26px;height:26px;background:var(--accent);border-radius:5px;display:grid;place-items:center;font-size:13px;color:#000}
.hbadges{display:flex;gap:6px;flex-wrap:wrap}
.badge{font-family:var(--mono);font-size:10px;padding:2px 8px;border-radius:99px;border:1px solid;letter-spacing:.4px}
.bo{color:var(--accent);border-color:rgba(240,136,62,.3);background:rgba(240,136,62,.07)}
.bb{color:var(--a2);border-color:rgba(121,192,255,.3);background:rgba(121,192,255,.07)}
.bg{color:var(--a3);border-color:rgba(86,211,100,.3);background:rgba(86,211,100,.07)}
.br{color:var(--danger);border-color:rgba(255,123,114,.3);background:rgba(255,123,114,.07)}
.hstatus{display:flex;align-items:center;gap:8px;font-size:12px;font-family:var(--mono)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--a3);box-shadow:0 0 6px var(--a3)}
.dot.red{background:var(--danger);box-shadow:0 0 6px var(--danger)}
.dot.pulse{animation:pulse 2s ease infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}

/* ── nav tabs ── */
.nav{display:flex;border-bottom:1px solid var(--border);background:var(--surface);
  padding:0 24px;gap:2px;position:sticky;top:52px;z-index:100}
.ntab{font-family:var(--mono);font-size:12px;padding:10px 16px;cursor:pointer;
  border-bottom:2px solid transparent;color:var(--muted);transition:.15s;
  background:none;border-top:none;border-left:none;border-right:none}
.ntab:hover{color:var(--text)}
.ntab.active{color:var(--accent);border-bottom-color:var(--accent)}

/* ── main layout ── */
.main{position:relative;z-index:1;flex:1;padding:24px;max-width:1200px;margin:0 auto;width:100%}
.panel{display:none}
.panel.active{display:block}

/* ── playground layout ── */
.playground{display:grid;grid-template-columns:1fr 400px;gap:16px;height:calc(100vh - 160px)}
@media(max-width:900px){.playground{grid-template-columns:1fr;height:auto}}

/* ── left pane ── */
.left-pane{display:flex;flex-direction:column;gap:12px;min-height:0}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.card-header{display:flex;align-items:center;justify-content:space-between;
  padding:10px 14px;border-bottom:1px solid var(--border);background:var(--s2)}
.card-title{font-size:11px;font-family:var(--mono);color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.card-body{padding:14px}

/* ── controls ── */
.controls-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
select,input[type=text]{font-family:var(--mono);font-size:12px;background:var(--s2);
  border:1px solid var(--border);color:var(--text);border-radius:5px;padding:7px 10px;
  outline:none;transition:border-color .15s}
select:focus,input:focus{border-color:var(--accent)}
.btn{font-family:var(--mono);font-size:12px;font-weight:700;padding:7px 16px;
  border-radius:5px;border:none;cursor:pointer;transition:all .12s;display:inline-flex;align-items:center;gap:6px}
.btn-primary{background:var(--accent);color:#000}
.btn-primary:hover{background:#ffaa5e;transform:translateY(-1px)}
.btn-primary:disabled{background:var(--s3);color:var(--muted);cursor:not-allowed;transform:none}
.btn-ghost{background:transparent;color:var(--text);border:1px solid var(--border)}
.btn-ghost:hover{border-color:var(--a2);color:var(--a2)}
.btn-green{background:var(--a3);color:#000}
.btn-green:hover{background:#6fe87a}
.btn-green:disabled{background:var(--s3);color:var(--muted);cursor:not-allowed}

/* ── task display ── */
.task-box{background:var(--s2);border:1px solid var(--border);border-radius:6px;padding:14px;
  font-size:13px;line-height:1.7;color:var(--text);white-space:pre-wrap;max-height:200px;
  overflow-y:auto;font-family:var(--mono)}
.task-meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.cwe{font-family:var(--mono);font-size:10px;padding:2px 7px;border-radius:4px;
  background:rgba(121,192,255,.08);color:var(--a2);border:1px solid rgba(121,192,255,.2)}
.diff-tag{font-family:var(--mono);font-size:10px;padding:2px 7px;border-radius:4px}
.easy{background:rgba(86,211,100,.1);color:var(--a3)}
.medium{background:rgba(240,136,62,.1);color:var(--accent)}
.hard{background:rgba(255,123,114,.1);color:var(--danger)}

/* ── code editor ── */
.editor-wrap{flex:1;display:flex;flex-direction:column;min-height:0}
.editor-header{display:flex;align-items:center;justify-content:space-between;
  padding:8px 14px;background:var(--s2);border-bottom:1px solid var(--border)}
.editor-dots{display:flex;gap:5px}
.editor-dots span{width:9px;height:9px;border-radius:50%}
.editor-dots span:nth-child(1){background:#ff5f57}
.editor-dots span:nth-child(2){background:#febc2e}
.editor-dots span:nth-child(3){background:#28c840}
#code-editor{flex:1;width:100%;background:var(--s2);border:none;color:var(--text);
  font-family:var(--mono);font-size:12px;line-height:1.65;padding:16px;
  resize:none;outline:none;tab-size:4;min-height:280px}
#code-editor::placeholder{color:var(--muted)}
.editor-footer{padding:8px 14px;background:var(--s2);border-top:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center;gap:8px}
.char-count{font-family:var(--mono);font-size:10px;color:var(--muted)}

/* ── right pane ── */
.right-pane{display:flex;flex-direction:column;gap:12px;overflow-y:auto;max-height:calc(100vh - 160px)}
@media(max-width:900px){.right-pane{max-height:none}}

/* ── reward display ── */
.reward-big{text-align:center;padding:20px 14px}
.reward-number{font-family:var(--mono);font-size:52px;font-weight:700;line-height:1;transition:all .4s ease}
.reward-label{font-size:11px;color:var(--muted);font-family:var(--mono);margin-top:4px}
.reward-bar-bg{height:6px;background:var(--s3);border-radius:99px;margin:12px 0}
.reward-bar{height:6px;border-radius:99px;background:var(--accent);transition:width .6s ease;width:0%}

/* ── score breakdown ── */
.score-row{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px}
.score-row:last-child{border:none}
.score-dim{flex:1;color:var(--muted);font-family:var(--mono)}
.score-val{font-family:var(--mono);font-weight:700;min-width:38px;text-align:right}
.score-bar-bg{width:60px;height:4px;background:var(--s3);border-radius:99px}
.score-bar-fg{height:4px;border-radius:99px;transition:width .5s ease;background:var(--a3)}
.weight-tag{font-size:9px;color:var(--s3);background:var(--border);padding:1px 5px;border-radius:3px;font-family:var(--mono)}

/* ── feedback ── */
.fb-item{font-size:11px;font-family:var(--mono);padding:5px 8px;border-radius:5px;
  background:var(--s2);border-left:3px solid var(--border);margin-bottom:4px;line-height:1.5}
.fb-item.good{border-left-color:var(--a3)}
.fb-item.warn{border-left-color:var(--warn)}
.fb-item.bad{border-left-color:var(--danger)}

/* ── history ── */
.history-item{display:flex;align-items:center;gap:8px;padding:7px 10px;
  border-bottom:1px solid var(--border);font-size:11px;font-family:var(--mono)}
.history-item:last-child{border:none}
.h-step{color:var(--muted);min-width:40px}
.h-reward{font-weight:700;min-width:50px}
.h-bar{flex:1;height:4px;background:var(--s3);border-radius:99px}
.h-bar-fg{height:4px;border-radius:99px;background:var(--a3);transition:width .4s}
.h-done{color:var(--a3);font-size:10px}

/* ── loading ── */
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.2);
  border-top-color:var(--accent);border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── empty state ── */
.empty{text-align:center;padding:40px 20px;color:var(--muted)}
.empty-icon{font-size:32px;margin-bottom:12px;opacity:.5}
.empty-text{font-size:13px;line-height:1.6}

/* ── alerts ── */
.alert{padding:10px 14px;border-radius:6px;font-size:12px;font-family:var(--mono);
  margin-bottom:8px;display:flex;gap:8px;align-items:flex-start}
.alert-error{background:rgba(255,123,114,.1);border:1px solid rgba(255,123,114,.3);color:var(--danger)}
.alert-success{background:rgba(86,211,100,.1);border:1px solid rgba(86,211,100,.3);color:var(--a3)}
.alert-info{background:rgba(121,192,255,.1);border:1px solid rgba(121,192,255,.3);color:var(--a2)}

/* ── overview panel ── */
.grid-2{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:20px;display:flex;flex-direction:column;gap:6px}
.stat-val{font-family:var(--mono);font-size:36px;font-weight:700;color:var(--accent)}
.stat-label{font-size:12px;color:var(--muted)}
.section-label{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:2px;
  text-transform:uppercase;padding:16px 0 8px;border-bottom:1px solid var(--border);margin-bottom:12px}

/* ── task list ── */
.task-list-item{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:14px 16px;cursor:pointer;transition:border-color .15s;margin-bottom:8px}
.task-list-item:hover{border-color:var(--accent)}
.tli-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.tli-name{font-weight:700;font-size:14px}
.tli-desc{font-size:12px;color:var(--muted);line-height:1.5}
.tli-footer{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}

/* ── docs panel ── */
.docs-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:12px}
.docs-h2{font-size:16px;font-weight:700;margin-bottom:8px}
.docs-p{font-size:13px;color:var(--muted);line-height:1.7;margin-bottom:12px}
.docs-code{background:var(--s2);border:1px solid var(--border);border-radius:6px;
  padding:14px;font-family:var(--mono);font-size:12px;line-height:1.65;overflow-x:auto;margin-bottom:12px;white-space:pre}
.method{font-weight:700;font-size:11px;padding:2px 7px;border-radius:4px;font-family:var(--mono)}
.method.post{background:rgba(86,211,100,.15);color:var(--a3)}
.method.get{background:rgba(121,192,255,.15);color:var(--a2)}
.ep-row{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px}
.ep-row:last-child{border:none}
.ep-path{font-family:var(--mono);color:var(--text);font-weight:700;min-width:180px}
.ep-desc{color:var(--muted);line-height:1.5}

/* ── weight chart ── */
.weight-bar-row{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:12px}
.wbr-name{flex:0 0 140px;font-family:var(--mono);color:var(--muted)}
.wbr-bg{flex:1;height:8px;background:var(--s3);border-radius:99px}
.wbr-fg{height:8px;border-radius:99px;background:var(--accent);transition:width .8s ease;width:0%}
.wbr-val{font-family:var(--mono);font-weight:700;color:var(--accent);min-width:36px;text-align:right}

::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="hlogo">
    <div class="hlogo-icon">🔒</div>
    SecureCodeEnv
  </div>
  <div class="hbadges">
    <span class="badge bo">v2.0.0</span>
    <span class="badge bb">RL Environment</span>
    <span class="badge bg">Live</span>
  </div>
  <div class="hstatus">
    <div class="dot pulse" id="status-dot"></div>
    <span id="status-text" style="font-size:11px"></span>
  </div>
</header>

<!-- NAV -->
<nav class="nav">
  <button class="ntab active" onclick="showPanel('playground', this)">⚡ Playground</button>
  <button class="ntab" onclick="showPanel('overview', this)">📊 Overview</button>
  <button class="ntab" onclick="showPanel('tasks', this)">📋 Tasks</button>
  <button class="ntab" onclick="showPanel('docs', this)">📖 API Docs</button>
</nav>

<!-- ══════════════════════════════════════════════════ -->
<!-- PLAYGROUND PANEL                                    -->
<!-- ══════════════════════════════════════════════════ -->
<div class="main">
<div id="panel-playground" class="panel active">
  <div class="playground">

    <!-- LEFT -->
    <div class="left-pane">

      <div class="card">
        <div class="card-header">
          <span class="card-title">Episode Control</span>
          <span id="session-badge" class="badge bb" style="display:none"></span>
        </div>
        <div class="card-body">
          <div id="alert-area"></div>
          <div class="controls-row">
            <select id="diff-select">
              <option value="easy">Easy</option>
              <option value="medium" selected>Medium</option>
              <option value="hard">Hard</option>
            </select>
            <select id="task-select" style="flex:1">
              <option value="">Random task</option>
            </select>
            <button class="btn btn-primary" id="btn-reset" onclick="doReset()">
              <span id="reset-spinner" style="display:none" class="spinner"></span>
              🔄 Reset
            </button>
          </div>
          <div id="task-area" style="margin-top:12px;display:none">
            <div class="task-meta" id="task-meta"></div>
            <div class="task-box" id="task-box"></div>
          </div>
        </div>
      </div>

      <div class="card editor-wrap">
        <div class="editor-header">
          <div class="editor-dots"><span></span><span></span><span></span></div>
          <span style="font-family:var(--mono);font-size:11px;color:var(--muted)" id="editor-filename">solution.py</span>
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost" style="padding:4px 10px;font-size:11px" onclick="loadStarter()">Load starter</button>
            <button class="btn btn-ghost" style="padding:4px 10px;font-size:11px" onclick="clearEditor()">Clear</button>
          </div>
        </div>
        <textarea id="code-editor" spellcheck="false"
          placeholder="# 1. Choose a difficulty and click Reset
# 2. Read the task description above
# 3. Click 'Load starter' to see the buggy code to fix
# 4. Write your secure solution here
# 5. Press Ctrl+Enter or click Submit

def your_function():
    pass"></textarea>
        <div class="editor-footer">
          <span class="char-count" id="char-count">0 chars</span>
          <div style="display:flex;gap:8px;align-items:center">
            <span id="step-counter" style="font-family:var(--mono);font-size:11px;color:var(--muted)">Step 0/5</span>
            <span style="font-family:var(--mono);font-size:10px;color:var(--s3)">Ctrl+Enter</span>
            <button class="btn btn-green" id="btn-submit" onclick="doStep()" disabled>
              <span id="submit-spinner" style="display:none" class="spinner"></span>
              ▶ Submit
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="right-pane">

      <div class="card">
        <div class="card-header">
          <span class="card-title">Total Reward</span>
          <span id="done-badge" style="display:none" class="badge bg">DONE ✓</span>
        </div>
        <div class="card-body">
          <div class="reward-big">
            <div class="reward-number" id="reward-number" style="color:var(--muted)">—</div>
            <div class="reward-label">/ 1.000 maximum</div>
          </div>
          <div class="reward-bar-bg"><div class="reward-bar" id="reward-bar"></div></div>
          <div id="summary-text" style="font-size:12px;font-family:var(--mono);color:var(--muted);text-align:center;padding:4px 0"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><span class="card-title">Score Breakdown</span></div>
        <div class="card-body" id="score-breakdown">
          <div class="empty"><div class="empty-icon">📊</div><div class="empty-text">Submit code to see scores</div></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><span class="card-title">Feedback</span></div>
        <div class="card-body" id="feedback-area">
          <div class="empty"><div class="empty-icon">💬</div><div class="empty-text">Feedback will appear here</div></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Episode History</span>
          <span class="char-count" id="history-count">0 steps</span>
        </div>
        <div id="history-area">
          <div class="empty" style="padding:20px"><div class="empty-text">No submissions yet</div></div>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════ -->
<!-- OVERVIEW PANEL                                      -->
<!-- ══════════════════════════════════════════════════ -->
<div id="panel-overview" class="panel">
  <div class="section-label">Environment Stats</div>
  <div class="grid-2">
    <div class="stat-card"><div class="stat-val">9</div><div class="stat-label">Security Tasks across 3 difficulty levels</div></div>
    <div class="stat-card"><div class="stat-val">7</div><div class="stat-label">Reward Dimensions</div></div>
    <div class="stat-card"><div class="stat-val">12+</div><div class="stat-label">CWE IDs Covered</div></div>
    <div class="stat-card"><div class="stat-val">5</div><div class="stat-label">Max Steps per Episode</div></div>
  </div>

  <div class="section-label" style="margin-top:24px">Reward Weights</div>
  <div class="card"><div class="card-body" id="weight-chart"></div></div>

  <div class="section-label" style="margin-top:24px">Design Principles</div>
  <div class="grid-2">
    <div class="stat-card" style="gap:10px">
      <div style="font-size:22px">⚔️</div>
      <div style="font-weight:700">Dynamic Attack Grading</div>
      <div class="stat-label">Real SQL injection, path traversal, JWT bypass, and XSS payloads are fired at submitted code each episode. Payloads are seeded-random so agents cannot memorise them.</div>
    </div>
    <div class="stat-card" style="gap:10px">
      <div style="font-size:22px">🧠</div>
      <div style="font-weight:700">CodeGraph Memory</div>
      <div class="stat-label">The agent's codebase context accumulates across steps. Naming conventions, error handling patterns, and type hint usage are tracked and enforced across submissions.</div>
    </div>
    <div class="stat-card" style="gap:10px">
      <div style="font-size:22px">🔒</div>
      <div style="font-weight:700">Security Gate</div>
      <div class="stat-label">An episode cannot be marked done unless attack resistance ≥ 75% AND static security ≥ 70%. Functional code that is insecure will never pass.</div>
    </div>
    <div class="stat-card" style="gap:10px">
      <div style="font-size:22px">📈</div>
      <div style="font-weight:700">Dense Reward Signal</div>
      <div class="stat-label">7 dimensions give partial credit at every step. Agents receive granular feedback on what to improve rather than a binary pass/fail signal.</div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════ -->
<!-- TASKS PANEL                                         -->
<!-- ══════════════════════════════════════════════════ -->
<div id="panel-tasks" class="panel">
  <div class="section-label">All Tasks</div>
  <div style="display:flex;gap:8px;margin-bottom:16px">
    <button class="btn btn-ghost" onclick="filterTasks('all')" id="f-all" style="border-color:var(--accent);color:var(--accent)">All</button>
    <button class="btn btn-ghost" onclick="filterTasks('easy')" id="f-easy">Easy</button>
    <button class="btn btn-ghost" onclick="filterTasks('medium')" id="f-medium">Medium</button>
    <button class="btn btn-ghost" onclick="filterTasks('hard')" id="f-hard">Hard</button>
  </div>
  <div id="task-list-container">
    <div class="empty"><div class="spinner" style="margin:0 auto"></div></div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════ -->
<!-- DOCS PANEL                                          -->
<!-- ══════════════════════════════════════════════════ -->
<div id="panel-docs" class="panel">
  <div class="docs-card">
    <div class="docs-h2">Quick Start</div>
    <div class="docs-p">Use the Playground tab for interactive testing, or call the API directly from any HTTP client.</div>
    <div class="docs-code">import requests

BASE = "http://localhost:7860"  # replace with your deployed URL

# 1. Start episode
ep = requests.post(f"{BASE}/reset", json={"difficulty": "medium"}).json()
sid = ep["session_id"]
print(ep["problem_statement"])

# 2. Submit code — graded across 7 dimensions
result = requests.post(f"{BASE}/step", json={
    "session_id": sid,
    "code": "def build_user_query(u, r):\n    return ('SELECT * FROM users WHERE username=%s', (u,))",
    "filename": "solution.py"
}).json()

print(f"reward = {result['total_reward']:.3f}")
print(result["feedback"]["summary"])</div>
  </div>

  <div class="docs-card">
    <div class="docs-h2">Endpoints</div>
    <div class="ep-row">
      <div class="ep-path"><span class="method get">GET</span>&nbsp;/health</div>
      <div class="ep-desc">Health check. Returns status, version, and tasks_loaded count.</div>
    </div>
    <div class="ep-row">
      <div class="ep-path"><span class="method post">POST</span>&nbsp;/reset</div>
      <div class="ep-desc">Start new episode. Body: <code>{"difficulty":"medium"}</code> or <code>{"task_id":"..."}</code>. Returns task, starter code, and initial CodeGraph.</div>
    </div>
    <div class="ep-row">
      <div class="ep-path"><span class="method post">POST</span>&nbsp;/step</div>
      <div class="ep-desc">Submit code. Body: <code>{"session_id":"...","code":"...","filename":"..."}</code>. Returns reward + per-dimension scores + feedback.</div>
    </div>
    <div class="ep-row">
      <div class="ep-path"><span class="method get">GET</span>&nbsp;/state</div>
      <div class="ep-desc">Current episode state. Query param: <code>session_id</code></div>
    </div>
    <div class="ep-row">
      <div class="ep-path"><span class="method get">GET</span>&nbsp;/tasks</div>
      <div class="ep-desc">List all tasks. Optional filter: <code>?difficulty=easy</code></div>
    </div>
    <div class="ep-row">
      <div class="ep-path"><span class="method get">GET</span>&nbsp;/tasks/{id}</div>
      <div class="ep-desc">Full task detail — problem statement, starter code, security checks.</div>
    </div>
    <div class="ep-row">
      <div class="ep-path"><span class="method get">GET</span>&nbsp;/docs</div>
      <div class="ep-desc">Auto-generated Swagger UI with full schema documentation.</div>
    </div>
  </div>

  <div class="docs-card">
    <div class="docs-h2">Reward Dimensions</div>
    <table style="width:100%;font-size:12px;font-family:var(--mono);border-collapse:collapse">
      <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
        <td style="padding:6px 8px">Dimension</td>
        <td style="padding:6px 8px">Weight</td>
        <td style="padding:6px 8px">Tool</td>
        <td style="padding:6px 8px">Measures</td>
      </tr>
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:6px 8px;color:var(--accent)">correctness</td>
        <td style="padding:6px 8px">25%</td>
        <td style="padding:6px 8px;color:var(--muted)">Custom runner</td>
        <td style="padding:6px 8px;color:var(--muted)">Test cases passed</td>
      </tr>
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:6px 8px;color:var(--accent)">attack_resist</td>
        <td style="padding:6px 8px">25%</td>
        <td style="padding:6px 8px;color:var(--muted)">Dynamic harness</td>
        <td style="padding:6px 8px;color:var(--muted)">Real attack payloads blocked</td>
      </tr>
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:6px 8px;color:var(--accent)">static_security</td>
        <td style="padding:6px 8px">20%</td>
        <td style="padding:6px 8px;color:var(--muted)">bandit + AST</td>
        <td style="padding:6px 8px;color:var(--muted)">CWE-mapped vulnerability patterns</td>
      </tr>
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:6px 8px;color:var(--accent)">consistency</td>
        <td style="padding:6px 8px">10%</td>
        <td style="padding:6px 8px;color:var(--muted)">CodeGraph</td>
        <td style="padding:6px 8px;color:var(--muted)">Convention adherence across steps</td>
      </tr>
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:6px 8px;color:var(--accent)">performance</td>
        <td style="padding:6px 8px">8%</td>
        <td style="padding:6px 8px;color:var(--muted)">timeit</td>
        <td style="padding:6px 8px;color:var(--muted)">Speed vs naive/optimal baselines</td>
      </tr>
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:6px 8px;color:var(--accent)">documentation</td>
        <td style="padding:6px 8px">7%</td>
        <td style="padding:6px 8px;color:var(--muted)">AST</td>
        <td style="padding:6px 8px;color:var(--muted)">Docstrings + type hint coverage</td>
      </tr>
      <tr>
        <td style="padding:6px 8px;color:var(--accent)">code_structure</td>
        <td style="padding:6px 8px">5%</td>
        <td style="padding:6px 8px;color:var(--muted)">AST</td>
        <td style="padding:6px 8px;color:var(--muted)">No bare print/except, clean structure</td>
      </tr>
    </table>
    <div style="margin-top:12px;padding:10px;background:var(--s2);border-radius:6px;font-size:11px;font-family:var(--mono);color:var(--warn)">
      ⚠ Security gate: episode cannot complete unless attack_resist ≥ 0.75 AND static_security ≥ 0.70 AND correctness ≥ 0.80
    </div>
  </div>

  <div class="docs-card">
    <div class="docs-h2">Step Response Example</div>
    <div class="docs-code">{
  "total_reward": 0.847,
  "scores": {
    "correctness": 1.0,
    "attack_resist": 0.875,
    "static_security": 0.9,
    "consistency": 0.75,
    "performance": 0.6,
    "documentation": 0.75,
    "code_structure": 0.8
  },
  "feedback": {
    "summary": "🟡 Good (0.847) — improve: consistency (0.75)",
    "attack_resist": "Good — SQL injection attacks blocked (87%)",
    "security_gate": "PASSED"
  },
  "details": {
    "correctness": {"passed": 5, "total": 5},
    "attacks": {"blocked": 7, "total": 8, "type": "injection"},
    "security_gate_passed": true
  },
  "done": false,
  "step_count": 1
}</div>
  </div>
</div>
</div><!-- /main -->

<script>
const state = {
  sessionId: null, task: null, stepCount: 0,
  done: false, history: [], allTasks: [],
};

const WEIGHTS = {
  correctness:0.25, attack_resist:0.25, static_security:0.20,
  consistency:0.10, performance:0.08, documentation:0.07, code_structure:0.05
};

document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  loadTasksDropdown();
  renderWeightChart();
  document.getElementById('code-editor').addEventListener('input', updateCharCount);
  updateCharCount();
});

async function checkHealth() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  try {
    const r = await fetch('/health');
    const d = await r.json();
    dot.className = 'dot pulse';
    txt.textContent = `${d.env} v${d.version} · ${d.tasks_loaded} tasks`;
  } catch(e) {
    dot.className = 'dot red';
    txt.textContent = 'Environment unreachable';
  }
}

function showPanel(id, btn) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.ntab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-'+id).classList.add('active');
  btn.classList.add('active');
  if (id === 'tasks' && state.allTasks.length === 0) loadTasksList();
}

async function loadTasksDropdown() {
  try {
    const tasks = await (await fetch('/tasks')).json();
    state.allTasks = tasks;
    const sel = document.getElementById('task-select');
    tasks.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.id.replace(/_/g,' ');
      sel.appendChild(opt);
    });
  } catch(e) {}
}

async function doReset() {
  const btn = document.getElementById('btn-reset');
  const spin = document.getElementById('reset-spinner');
  btn.disabled = true; spin.style.display = 'inline-block';
  clearAlert();

  const difficulty = document.getElementById('diff-select').value;
  const taskId = document.getElementById('task-select').value;
  const body = taskId ? {task_id: taskId} : {difficulty};

  try {
    const r = await fetch('/reset', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    if (!r.ok) { showAlert((await r.json()).detail || 'Reset failed', 'error'); return; }
    const d = await r.json();
    state.sessionId = d.session_id;
    state.task = d;
    state.stepCount = 0;
    state.done = false;
    state.history = [];
    renderTask(d);
    resetResultPanel();
    updateStepCounter();
    document.getElementById('btn-submit').disabled = false;
    document.getElementById('session-badge').style.display = 'inline';
    document.getElementById('session-badge').textContent = d.session_id.slice(0,8)+'…';
    showAlert(`✓ Episode started: ${d.task_id}`, 'success');
  } catch(e) {
    showAlert('Network error: '+e.message, 'error');
  } finally {
    btn.disabled = false; spin.style.display = 'none';
  }
}

async function doStep() {
  if (!state.sessionId) { showAlert('Reset an episode first', 'error'); return; }
  const code = document.getElementById('code-editor').value.trim();
  if (!code) { showAlert('Write some code first', 'error'); return; }

  const btn = document.getElementById('btn-submit');
  const spin = document.getElementById('submit-spinner');
  btn.disabled = true; spin.style.display = 'inline-block';
  clearAlert();

  try {
    const r = await fetch('/step', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        session_id: state.sessionId,
        code,
        filename: `solution_step${state.stepCount}.py`
      })
    });
    if (!r.ok) {
      const e = await r.json();
      showAlert(e.detail || 'Step failed', 'error');
      if (r.status === 400) btn.disabled = true;
      return;
    }
    const d = await r.json();
    state.stepCount = d.step_count;
    state.done = d.done;
    state.history.push({step: d.step_count, reward: d.total_reward, done: d.done});
    renderReward(d.total_reward);
    renderScores(d.scores, d.details);
    renderFeedback(d.feedback);
    renderHistory();
    updateStepCounter();
    if (d.done) {
      btn.disabled = true;
      document.getElementById('done-badge').style.display = 'inline';
      showAlert(
        d.total_reward >= 0.92 ? '🎉 Excellent! Security gate passed!' : `Episode complete after ${d.step_count} steps.`,
        d.total_reward >= 0.92 ? 'success' : 'info'
      );
    }
  } catch(e) {
    showAlert('Network error: '+e.message, 'error');
  } finally {
    if (!state.done) btn.disabled = false;
    spin.style.display = 'none';
  }
}

function renderTask(d) {
  document.getElementById('task-area').style.display = 'block';
  document.getElementById('task-meta').innerHTML =
    `<span class="diff-tag ${d.difficulty}">${d.difficulty}</span>` +
    d.cwe_targets.map(c=>`<span class="cwe">${c}</span>`).join('');
  document.getElementById('task-box').textContent = d.problem_statement;
  document.getElementById('editor-filename').textContent = d.task_id+'.py';
}

function renderReward(reward) {
  const n = document.getElementById('reward-number');
  const bar = document.getElementById('reward-bar');
  n.textContent = reward.toFixed(3);
  const color = reward >= 0.92 ? 'var(--a3)' : reward >= 0.65 ? 'var(--accent)' : 'var(--danger)';
  n.style.color = color;
  bar.style.width = (reward*100)+'%';
  bar.style.background = color;
}

function renderScores(scores, details) {
  const rows = Object.entries(scores).map(([k,v]) => {
    const pct = Math.round(v*100);
    const color = v >= 0.75 ? 'var(--a3)' : v >= 0.5 ? 'var(--accent)' : 'var(--danger)';
    const w = Math.round((WEIGHTS[k]||0)*100);
    let extra = '';
    if (details) {
      if (k==='correctness' && details.correctness_total)
        extra = ` (${details.correctness_passed}/${details.correctness_total})`;
      else if (k==='attack_resist' && details.attacks_total)
        extra = ` (${details.attacks_blocked}/${details.attacks_total})`;
    }
    return `<div class="score-row">
      <div class="score-dim">${k}${extra}</div>
      <div class="score-bar-bg"><div class="score-bar-fg" style="width:${pct}%;background:${color}"></div></div>
      <div class="score-val" style="color:${color}">${v.toFixed(2)}</div>
      <div class="weight-tag">${w}%</div>
    </div>`;
  });
  document.getElementById('score-breakdown').innerHTML = rows.join('');
  // Security gate status
  if (details) {
    const gateEl = document.createElement('div');
    gateEl.style.cssText = 'margin-top:8px;font-family:var(--mono);font-size:10px;padding:6px 8px;border-radius:4px;';
    if (details.security_gate_passed) {
      gateEl.style.background = 'rgba(86,211,100,.1)';
      gateEl.style.color = 'var(--a3)';
      gateEl.textContent = '🔒 Security gate: PASSED';
    } else {
      gateEl.style.background = 'rgba(255,123,114,.1)';
      gateEl.style.color = 'var(--danger)';
      gateEl.textContent = '🔒 Security gate: NOT MET — need attack≥0.75, static≥0.70, correctness≥0.80';
    }
    document.getElementById('score-breakdown').appendChild(gateEl);
  }
}

function renderFeedback(feedback) {
  const summary = feedback.summary || '';
  const items = Object.entries(feedback).filter(([k])=>k!=='summary'&&k!=='security_gate');
  const good = v => v.startsWith('Excellent')||v.startsWith('Clean')||v.startsWith('Well')||v.startsWith('Good conv');
  const bad  = v => v.includes('CRITICAL')||v.includes('Vulnerable')||v.includes('HIGH')||v.includes('Poor');
  document.getElementById('feedback-area').innerHTML =
    `<div class="fb-item ${summary.includes('✅')?'good':summary.includes('🔴')||summary.includes('🔒')?'bad':'warn'}">${esc(summary)}</div>` +
    items.map(([k,v])=>`<div class="fb-item ${good(v)?'good':bad(v)?'bad':'warn'}"><strong>${k}:</strong> ${esc(v)}</div>`).join('');
}

function renderHistory() {
  const n = state.history.length;
  document.getElementById('history-count').textContent = `${n} step${n!==1?'s':''}`;
  document.getElementById('history-area').innerHTML = !n
    ? '<div class="empty" style="padding:20px"><div class="empty-text">No submissions yet</div></div>'
    : state.history.map(h => {
        const color = h.reward >= 0.92 ? 'var(--a3)' : h.reward >= 0.65 ? 'var(--accent)' : 'var(--danger)';
        return `<div class="history-item">
          <span class="h-step">Step ${h.step}</span>
          <span class="h-reward" style="color:${color}">${h.reward.toFixed(3)}</span>
          <div class="h-bar"><div class="h-bar-fg" style="width:${h.reward*100}%;background:${color}"></div></div>
          ${h.done ? '<span class="h-done">done</span>' : ''}
        </div>`;
      }).join('');
}

function resetResultPanel() {
  document.getElementById('reward-number').textContent = '—';
  document.getElementById('reward-number').style.color = 'var(--muted)';
  document.getElementById('reward-bar').style.width = '0%';
  document.getElementById('score-breakdown').innerHTML = '<div class="empty"><div class="empty-icon">📊</div><div class="empty-text">Submit code to see scores</div></div>';
  document.getElementById('feedback-area').innerHTML = '<div class="empty"><div class="empty-icon">💬</div><div class="empty-text">Feedback will appear here</div></div>';
  document.getElementById('history-area').innerHTML = '<div class="empty" style="padding:20px"><div class="empty-text">No submissions yet</div></div>';
  document.getElementById('history-count').textContent = '0 steps';
  document.getElementById('done-badge').style.display = 'none';
  document.getElementById('summary-text').textContent = '';
}

function updateStepCounter() {
  document.getElementById('step-counter').textContent = `Step ${state.stepCount}/5`;
}
function updateCharCount() {
  document.getElementById('char-count').textContent = document.getElementById('code-editor').value.length+' chars';
}

async function loadStarter() {
  if (!state.task) { showAlert('Reset an episode first', 'error'); return; }
  try {
    const d = await (await fetch(`/tasks/${state.task.task_id}`)).json();
    if (d.starter_code) { document.getElementById('code-editor').value = d.starter_code; updateCharCount(); }
  } catch(e) {}
}
function clearEditor() {
  document.getElementById('code-editor').value = ''; updateCharCount();
}

function showAlert(msg, type='info') {
  const cls = type==='error'?'alert-error':type==='success'?'alert-success':'alert-info';
  document.getElementById('alert-area').innerHTML = `<div class="alert ${cls}">${esc(msg)}</div>`;
  setTimeout(()=>{ document.getElementById('alert-area').innerHTML=''; }, 5000);
}
function clearAlert() { document.getElementById('alert-area').innerHTML=''; }

async function loadTasksList() {
  if (!state.allTasks.length) state.allTasks = await (await fetch('/tasks')).json();
  filterTasks('all');
}

function filterTasks(diff) {
  ['all','easy','medium','hard'].forEach(d => {
    const el = document.getElementById('f-'+d);
    el.style.borderColor = ''; el.style.color = '';
  });
  document.getElementById('f-'+diff).style.borderColor = 'var(--accent)';
  document.getElementById('f-'+diff).style.color = 'var(--accent)';
  const tasks = diff==='all' ? state.allTasks : state.allTasks.filter(t=>t.difficulty===diff);
  document.getElementById('task-list-container').innerHTML = !tasks.length
    ? '<div class="empty"><div class="empty-text">No tasks found</div></div>'
    : tasks.map(t=>`
      <div class="task-list-item" onclick="tryTask('${t.id}')">
        <div class="tli-header">
          <div class="tli-name">${t.id.replace(/_/g,' ')}</div>
          <span class="diff-tag ${t.difficulty}">${t.difficulty}</span>
        </div>
        <div class="tli-desc">${esc((t.description||'').slice(0,120))}${(t.description||'').length>120?'…':''}</div>
        <div class="tli-footer">
          ${t.cwe_targets.map(c=>`<span class="cwe">${c}</span>`).join('')}
          <span class="badge bo" style="font-size:9px;margin-left:auto">Try →</span>
        </div>
      </div>`).join('');
}

function tryTask(id) {
  document.querySelectorAll('.ntab')[0].click();
  document.getElementById('task-select').value = id;
  doReset();
}

function renderWeightChart() {
  document.getElementById('weight-chart').innerHTML = Object.entries(WEIGHTS).map(([n,w])=>`
    <div class="weight-bar-row">
      <div class="wbr-name">${n}</div>
      <div class="wbr-bg"><div class="wbr-fg" style="width:${w*100*3.3}%"></div></div>
      <div class="wbr-val">${Math.round(w*100)}%</div>
    </div>`).join('');
}

function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

document.addEventListener('keydown', e => {
  if (e.target.id==='code-editor' && e.key==='Tab') {
    e.preventDefault();
    const s=e.target.selectionStart, en=e.target.selectionEnd;
    e.target.value=e.target.value.substring(0,s)+'    '+e.target.value.substring(en);
    e.target.selectionStart=e.target.selectionEnd=s+4;
    updateCharCount();
  }
  if ((e.ctrlKey||e.metaKey) && e.key==='Enter') doStep();
});
</script>
</body>
</html>"""
