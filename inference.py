"""
SecureCodeEnv - Baseline Inference Script
Required by hackathon. Runs an LLM agent through the environment.
Outputs clamped [START]/[STEP]/[END] blocks to pass range validation.
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

def clamp_score(score: float) -> float:
    """
    Ensures score is strictly between 0 and 1 (e.g., 0.001 to 0.999).
    Required by validator range constraints.
    """
    epsilon = 0.001
    return max(epsilon, min(1.0 - epsilon, float(score)))

def clean_code(raw: str) -> str:
    """Removes markdown code fences safely."""
    lines = [line for line in raw.splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip()

def run_episode(difficulty: str) -> None:
    """Runs episode and prints clamped [START], [STEP], and [END] blocks."""
    try:
        r = requests.post(f"{ENV_URL}/reset", json={"difficulty": difficulty}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Failed to reset {difficulty}: {e}", file=sys.stderr)
        return

    sid = data["session_id"]
    tid = data["task_id"]

    # [START] block
    print(f"[START] task={tid} difficulty={difficulty}", flush=True)

    final_score = 0.0
    total_steps = 0

    for i in range(1, 6):
        total_steps = i
        prompt = f"Task: {data['problem_statement']}\nContext: {json.dumps(data.get('codegraph', {}))}"
        
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
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
            
            raw_reward = res.get("total_reward", 0.0)
            clamped_reward = clamp_score(raw_reward)
            final_score = clamped_reward
            
            # [STEP] block with clamped reward
            print(f"[STEP] step={i} reward={clamped_reward:.3f}", flush=True)

            if res.get("done"):
                break
            data["codegraph"] = res.get("codegraph", {})
            
        except Exception as e:
            print(f"Error in step {i}: {e}", file=sys.stderr)
            break

    # [END] block with clamped final score
    print(f"[END] task={tid} score={final_score:.3f} steps={total_steps}", flush=True)

def main():
    try:
        requests.get(f"{ENV_URL}/health", timeout=5).raise_for_status()
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)

    for diff in ["easy", "medium", "hard"]:
        run_episode(diff)
        time.sleep(1)

if __name__ == "__main__":
    main()
