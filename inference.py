"""
SecureCodeEnv - Baseline Inference Script
Required by hackathon. Runs an LLM agent through the environment.

Usage:
    export API_BASE_URL=https://api.openai.com/v1
    export MODEL_NAME=gpt-4o-mini
    export HF_TOKEN=hf_your_token
    export ENV_URL=http://localhost:7860  # or your HF Space URL
    python inference.py

Completes in under 20 minutes on 2 vCPU / 8GB RAM.
"""
import os
import json
import time
import sys
import requests
from openai import OpenAI

# ── Required environment variables ──────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")
ENV_URL      = os.environ.get("ENV_URL", "http://localhost:7860")

if not HF_TOKEN:
    print("⚠️  HF_TOKEN not set. Some model endpoints may reject requests.", file=sys.stderr)

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "sk-placeholder")

# ── System prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior Python security engineer.
You write production-ready, secure Python code with no shortcuts.

Rules:
1. Output ONLY raw Python code — no markdown fences, no explanations.
2. Never use: eval(), exec(), shell=True, hashlib.md5, random.random() for security.
3. Always use parameterized queries (never f-string SQL).
4. Use secrets module (not random) for tokens and session IDs.
5. Use bcrypt (not hashlib) for password hashing.
6. Use hmac.compare_digest for secret comparison (not ==).
7. Validate all inputs — handle None, empty string, type errors.
8. Add type hints and docstrings to every function.
9. Follow the naming and style conventions shown in CODEBASE CONTEXT.
10. Use pathlib.Path.resolve() for file path validation (not string checks)."""


def run_episode(difficulty: str = "medium") -> dict:
    """Run one full episode at the given difficulty and return results."""
    print(f"\n{'='*60}")
    print(f"  Episode: {difficulty.upper()}")
    print(f"{'='*60}")

    # ── Step 1: Reset environment ─────────────────────────────────────────
    try:
        reset_resp = requests.post(
            f"{ENV_URL}/reset",
            json={"difficulty": difficulty},
            timeout=30,
        )
        reset_resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ /reset failed: {e}")
        return {"task": "unknown", "scores": [], "final_score": 0.0, "improved": False, "error": str(e)}

    episode = reset_resp.json()
    sid = episode["session_id"]
    task_id = episode["task_id"]
    print(f"  Task: {task_id}")
    print(f"  CWE targets: {episode.get('cwe_targets', [])}")

    scores_history = []
    prev_feedback = {}

    for step_num in range(5):
        # ── Step 2: Build prompt ──────────────────────────────────────────
        context = episode.get("codegraph", {})
        context_prompt = context.get("context_prompt", "")
        # Cap context at 3000 chars to stay within token budget
        context_str = context_prompt[:3000] if context_prompt else json.dumps(context, indent=2)[:2000]

        feedback_str = ""
        if prev_feedback:
            feedback_str = "\n\nPREVIOUS ATTEMPT FEEDBACK:\n" + "\n".join(
                f"  {k}: {v}" for k, v in prev_feedback.items() if v
            )

        user_message = f"""Task: {episode['problem_statement']}

Security targets: {episode.get('cwe_targets', [])}

{context_str}
{feedback_str}

Write the complete Python implementation now:"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # ── Step 3: Call LLM ──────────────────────────────────────────────
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=1500,
                temperature=0.1,  # Low temperature for consistent, focused code
            )
            code = response.choices[0].message.content.strip()

            # Strip markdown fences if model added them anyway
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()

        except Exception as e:
            print(f"  ⚠️  LLM call failed at step {step_num+1}: {e}")
            break

        # ── Step 4: Submit to environment ─────────────────────────────────
        try:
            step_resp = requests.post(
                f"{ENV_URL}/step",
                json={
                    "session_id": sid,
                    "code": code,
                    "filename": f"solution_step{step_num}.py",
                    "task_id": task_id,
                },
                timeout=60,  # Grading can take up to 60s (bandit + attacks)
            )
            step_resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ⚠️  /step failed: {e}")
            break

        result = step_resp.json()
        reward = result["total_reward"]
        scores_history.append(reward)
        prev_feedback = result.get("feedback", {})

        # Pretty print step result
        scores = result.get("scores", {})
        print(f"\n  Step {step_num+1} → reward={reward:.3f}")
        print(f"    correctness={scores.get('correctness',0):.2f}  "
              f"attack={scores.get('attack_resist',0):.2f}  "
              f"static={scores.get('static_security',0):.2f}  "
              f"consistency={scores.get('consistency',0):.2f}")
        print(f"    summary: {prev_feedback.get('summary', '')}")

        if result["done"]:
            print(f"\n  ✅ Episode complete in {step_num+1} steps!")
            break

        # Feed updated CodeGraph back for next step
        episode["codegraph"] = result.get("codegraph", {})

    if not scores_history:
        scores_history = [0.0]

    improved = len(scores_history) > 1 and scores_history[-1] > scores_history[0]
    return {
        "task": task_id,
        "difficulty": difficulty,
        "scores": scores_history,
        "final_score": scores_history[-1],
        "improved": improved,
        "steps": len(scores_history),
    }


def main():
    """Run one episode per difficulty and print aggregate results."""
    print(f"\n{'='*60}")
    print(f"  SecureCodeEnv — Baseline Inference")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Env:   {ENV_URL}")
    print(f"{'='*60}")

    # Verify environment is up
    try:
        health = requests.get(f"{ENV_URL}/health", timeout=10)
        health.raise_for_status()
        print(f"\n  ✅ Environment healthy: {health.json()}")
    except Exception as e:
        print(f"\n  ❌ Environment not reachable at {ENV_URL}: {e}")
        print("  Start the server: uvicorn app.main:app --host 0.0.0.0 --port 7860")
        sys.exit(1)

    results = []
    start = time.time()

    for difficulty in ["easy", "medium", "hard"]:
        r = run_episode(difficulty)
        results.append(r)
        # Small pause between episodes
        time.sleep(1)

    elapsed = time.time() - start

    # ── Final report ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  FINAL RESULTS  ({elapsed:.1f}s total)")
    print(f"{'='*60}")

    for r in results:
        status = "✅" if r["final_score"] >= 0.7 else "⚠️ " if r["final_score"] >= 0.4 else "❌"
        improved_str = "↑ improved" if r.get("improved") else "—"
        print(f"  {status} {r['task']:45s}  {r['final_score']:.3f}  {improved_str}")

    valid_scores = [r["final_score"] for r in results]
    avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    print(f"\n  Average final score: {avg:.3f}")
    print(f"  Scores: {[round(s, 3) for s in valid_scores]}")

    # Write machine-readable results
    output = {
        "model": MODEL_NAME,
        "env_url": ENV_URL,
        "elapsed_seconds": round(elapsed, 1),
        "results": results,
        "average_score": round(avg, 4),
    }
    with open("inference_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to inference_results.json")

    return 0 if avg >= 0.4 else 1


if __name__ == "__main__":
    sys.exit(main())
