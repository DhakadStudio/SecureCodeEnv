"""
SecureCodeEnv - Baseline Inference Script
Required by hackathon. Runs an LLM agent through the environment.
Outputs structured [START]/[STEP]/[END] blocks for automated parsing.
"""
import os
import json
import time
import sys
import requests
from openai import OpenAI
from typing import Dict, List, Any

# ── Configuration ──────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860").rstrip("/")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "sk-placeholder")

SYSTEM_PROMPT = """You are a senior Python security engineer.
Output ONLY raw Python code with type hints and docstrings. No markdown.
Follow SOLID principles and use cryptographically secure libraries."""

def clean_code(raw: str) -> str:
    """Strictly removes markdown and whitespace."""
    lines = [line for line in raw.splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip()

def run_episode(difficulty: str) -> None:
    """Runs episode and prints [START], [STEP], and [END] blocks."""
    try:
        r = requests.post(f"{ENV_URL}/reset", json={"difficulty": difficulty}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return

    sid = data["session_id"]
    tid = data["task_id"]

    # REQUIRED: [START] block
    print(f"[START] task={tid} difficulty={difficulty}", flush=True)

    final_score = 0.0
    total_steps = 0

    for i in range(1, 6):
        total_steps = i
        # Simple prompt construction
        prompt = f"Task: {data['problem_statement']}\nCode context: {json.dumps(data.get('codegraph', {}))}"
        
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                temperature=0.1
            )
            code = clean_code(resp.choices[0].message.content or "")
            
            step_r = requests.post(
                f"{ENV_URL}/step",
                json={"session_id": sid, "code": code, "filename": f"step_{i}.py", "task_id": tid},
                timeout=65
            )
            step_r.raise_for_status()
            res = step_r.json()
            
            reward = res.get("total_reward", 0.0)
            final_score = reward
            
            # REQUIRED: [STEP] block
            print(f"[STEP] step={i} reward={reward:.3f}", flush=True)

            if res.get("done"):
                break
            data["codegraph"] = res.get("codegraph", {})
            
        except Exception:
            break

    # REQUIRED: [END] block
    print(f"[END] task={tid} score={final_score:.3f} steps={total_steps}", flush=True)

def main():
    # Verify health first
    try:
        requests.get(f"{ENV_URL}/health", timeout=5).raise_for_status()
    except:
        sys.exit(1)

    for diff in ["easy", "medium", "hard"]:
        run_episode(diff)
        time.sleep(1)

if __name__ == "__main__":
    main()
