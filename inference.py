"""
SecureCodeEnv - Baseline Inference Script
Required by hackathon. Runs an LLM agent through the environment.
"""
import os
import json
import time
import sys
import requests
from openai import OpenAI
from typing import Dict, List, Any, Optional

# ── Constants & Configuration ──────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860").rstrip("/")

# Typed Exception for environment issues
class EnvironmentConnectionError(Exception):
    """Raised when the sandbox environment is unreachable or returns 5xx."""
    pass

if not HF_TOKEN:
    print("⚠️  HF_TOKEN not set. Some model endpoints may reject requests.", file=sys.stderr)

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "sk-placeholder")

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
9. Use pathlib.Path.resolve() for file path validation."""


def clean_code_output(raw_code: str) -> str:
    """Removes markdown fences and surrounding whitespace safely."""
    lines = raw_code.splitlines()
    if not lines:
        return ""
    
    # Filter out markdown code fence markers
    filtered = [line for line in lines if not line.strip().startswith("```")]
    return "\n".join(filtered).strip()


def run_episode(difficulty: str = "medium") -> Dict[str, Any]:
    """Run one full episode at the given difficulty and return results."""
    print(f"\n{'='*60}\n  Episode: {difficulty.upper()}\n{'='*60}")

    try:
        reset_resp = requests.post(
            f"{ENV_URL}/reset",
            json={"difficulty": difficulty},
            timeout=30,
        )
        reset_resp.raise_for_status()
    except Exception as e:
        print(f"❌ /reset failed: {e}")
        return {"task": f"reset_fail_{difficulty}", "scores": [0.0], "final_score": 0.0, "error": str(e)}

    episode = reset_resp.json()
    sid = episode["session_id"]
    task_id = episode["task_id"]
    
    scores_history: List[float] = []
    prev_feedback: Dict[str, Any] = {}

    for step_num in range(5):
        context = episode.get("codegraph", {})
        context_prompt = context.get("context_prompt", "")
        context_str = context_prompt[:3000] if context_prompt else json.dumps(context)[:2000]

        feedback_list = [f"{k}: {v}" for k, v in prev_feedback.items() if v]
        feedback_str = "\n\nPREVIOUS FEEDBACK:\n" + "\n".join(feedback_list) if feedback_list else ""

        user_message = f"Task: {episode['problem_statement']}\nTargets: {episode.get('cwe_targets', [])}\n{context_str}{feedback_str}\n\nImplementation:"

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1500,
                temperature=0.1,
            )
            raw_content = response.choices[0].message.content or ""
            code = clean_code_output(raw_content)
            
            if not code:
                print(f"  ⚠️ Step {step_num}: LLM returned empty code.")
                break

            step_resp = requests.post(
                f"{ENV_URL}/step",
                json={
                    "session_id": sid,
                    "code": code,
                    "filename": f"solution_s{step_num}.py",
                    "task_id": task_id,
                },
                timeout=65,
            )
            step_resp.raise_for_status()
            result = step_resp.json()
            
            reward = result.get("total_reward", 0.0)
            scores_history.append(reward)
            prev_feedback = result.get("feedback", {})
            
            print(f"  Step {step_num+1} → reward={reward:.3f}")

            if result.get("done"):
                break
            
            episode["codegraph"] = result.get("codegraph", {})

        except Exception as e:
            print(f"  ⚠️ Error during step {step_num+1}: {e}")
            break

    final_score = scores_history[-1] if scores_history else 0.0
    return {
        "task": task_id,
        "difficulty": difficulty,
        "scores": scores_history,
        "final_score": final_score,
        "steps": len(scores_history),
    }


def main() -> int:
    """Main execution loop."""
    print(f"Model: {MODEL_NAME} | Env: {ENV_URL}")

    try:
        health = requests.get(f"{ENV_URL}/health", timeout=10)
        health.raise_for_status()
    except Exception as e:
        print(f"❌ Environment unreachable at {ENV_URL}. Ensure server is running.\nError: {e}")
        return 1

    results = []
    start_time = time.time()

    for diff in ["easy", "medium", "hard"]:
        try:
            results.append(run_episode(diff))
        except Exception as e:
            print(f"Critical failure in {diff} episode: {e}")
        time.sleep(1)

    elapsed = time.time() - start_time
    avg_score = sum(r["final_score"] for r in results) / len(results) if results else 0.0

    print(f"\n{'='*60}\n  FINAL AVERAGE: {avg_score:.3f} ({elapsed:.1f}s)\n{'='*60}")
    
    with open("inference_results.json", "w") as f:
        json.dump({"results": results, "avg": avg_score}, f, indent=2)

    # Return 0 to indicate the script finished its logic, regardless of score
    # Unless there were absolutely no results (total failure)
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
