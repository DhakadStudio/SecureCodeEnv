---
title: SecureCodeEnv
emoji: 🔒
colorFrom: red
colorTo: blue
sdk: docker
pinned: true
license: apache-2.0
---

# SecureCodeEnv

**An RL environment for training LLM agents to write production-ready, secure Python code.**

---

## The Problem

Studies show **12–65% of LLM-generated code contains security vulnerabilities**. Secure-pass@1 rates remain below 12% for all frontier models even when functional pass@1 exceeds 50%.

Every existing RL environment trains agents to write code that **works**. None train agents to write code that is **safe, consistent, and production-ready**. SecureCodeEnv closes that gap.

---

## What Makes This Environment Different

| Feature | SecureCodeEnv | Typical RL Code Envs |
|---|---|---|
| Dynamic adversarial grading | ✅ Real attacks fired per episode | ❌ Static patterns only |
| CodeGraph memory | ✅ Cross-step convention tracking | ❌ Single-function only |
| CWE-grounded tasks | ✅ 9 tasks, 12+ CWE IDs | ❌ Generic correctness |
| Security gate on done | ✅ Attack + static thresholds | ❌ Pass/fail only |
| Anti-reward-hacking | ✅ Seeded random payloads | ❌ Fixed test cases |

---

## Reward System — 7 Dimensions

| Dimension | Weight | Tool | What It Measures |
|---|---|---|---|
| correctness | 25% | Custom test runner | Test cases passed |
| attack_resist | 25% | Dynamic harness | Real attack payloads blocked |
| static_security | 20% | bandit + AST | CWE-mapped vulnerability patterns |
| consistency | 10% | CodeGraph | Convention adherence across steps |
| performance | 8% | timeit | Speed vs naive/optimal baselines |
| documentation | 7% | AST | Docstring + type hint coverage |
| code_structure | 5% | AST | Clean code (no bare print/except) |

**Security gate:** episode cannot complete unless `attack_resist ≥ 0.75` AND `static_security ≥ 0.70` AND `correctness ≥ 0.80`.

---

## Tasks — 9 Tasks Across 3 Difficulty Levels

### Easy
| Task | CWE Targets |
|---|---|
| Password Validator | CWE-916, CWE-521 |
| Input Sanitizer | CWE-20, CWE-116 |
| Token Generator | CWE-338, CWE-330 |

### Medium
| Task | CWE Targets |
|---|---|
| SQL Query Builder | CWE-89 |
| File Path Handler | CWE-22 |
| Rate Limiter | CWE-770, CWE-400 |

### Hard
| Task | CWE Targets |
|---|---|
| File Upload Handler | CWE-22, CWE-434 |
| JWT Validator | CWE-347, CWE-613 |
| Auth Middleware | CWE-287, CWE-352 |

---

## Quick Start

```python
import requests

BASE = "http://localhost:7860"

# Start episode
ep = requests.post(f"{BASE}/reset", json={"difficulty": "medium"}).json()
sid = ep["session_id"]
print(ep["problem_statement"])

# Submit code
result = requests.post(f"{BASE}/step", json={
    "session_id": sid,
    "code": "def build_user_query(u, r):\n    return ('SELECT * FROM users WHERE username=%s', (u,))",
    "filename": "solution.py"
}).json()

print(f"reward={result['total_reward']:.3f}")
print(result["feedback"]["summary"])
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /reset | Start new episode |
| POST | /step | Submit code for grading |
| GET | /state | Current episode state |
| GET | /tasks | List all tasks |
| GET | /tasks/{id} | Task detail + starter code |
| GET | /docs | Swagger UI |

---

## Setup

```bash
# Docker (recommended)
docker build -t secure-code-env .
docker run -p 7860:7860 secure-code-env

# Direct
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

## Run Baseline Inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token
export ENV_URL=http://localhost:7860
python inference.py
```

## Pre-submission Validation

```bash
python validate.py --url http://localhost:7860
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_BASE_URL` | Yes (inference) | LLM API endpoint |
| `MODEL_NAME` | Yes (inference) | Model identifier |
| `HF_TOKEN` | Yes (inference) | API authentication token |
| `ENV_URL` | No | Override environment URL (default: localhost:7860) |
