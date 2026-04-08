"""
SecureCodeEnv - Pre-Submission Validator
Run this before pushing to HuggingFace Spaces.
All checks must pass before submission.

Usage:
    python validate.py
    python validate.py --url https://vishaldhakad-securecodeenv.hf.space
"""
import sys
import os
import json
import requests
import argparse
import subprocess

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def check(name: str, ok: bool, detail: str = "") -> bool:
    icon = PASS if ok else FAIL
    line = f"  {icon}  {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def validate_files() -> bool:
    print("\n── File Structure ──────────────────────────────────────────")
    required = [
        "openenv.yaml",
        "Dockerfile",
        "inference.py",
        "requirements.txt",
        "README.md",
        "app/main.py",
        "app/routes.py",
        "app/models.py",
        "app/state.py",
        "graders/reward_aggregator.py",
        "graders/correctness.py",
        "graders/attacks.py",
        "graders/static_analysis.py",
        "graders/performance.py",
        "graders/consistency.py",
        "graders/documentation.py",
        "codegraph/graph.py",
        "codegraph/extractor.py",
        "codegraph/serializer.py",
        "sandbox/executor.py",
        "sandbox/payload_gen.py",
        "tasks/task_registry.py",
    ]
    all_ok = True
    for path in required:
        exists = os.path.exists(path)
        if not check(path, exists):
            all_ok = False
    return all_ok


def validate_imports() -> bool:
    print("\n── Python Imports ──────────────────────────────────────────")
    checks = [
        ("fastapi", "from fastapi import FastAPI"),
        ("pydantic", "from pydantic import BaseModel"),
        ("uvicorn", "import uvicorn"),
        ("bandit CLI", None),
    ]
    all_ok = True
    for name, stmt in checks:
        if stmt:
            try:
                exec(stmt)
                check(name, True)
            except ImportError as e:
                check(name, False, str(e))
                all_ok = False
        else:
            # Check CLI tool
            result = subprocess.run(["bandit", "--version"], capture_output=True, text=True)
            ok = result.returncode == 0
            check(f"bandit CLI", ok, result.stdout.strip()[:40] if ok else "not found — pip install bandit")
            if not ok:
                all_ok = False
    return all_ok


def validate_task_registry() -> bool:
    print("\n── Task Registry ───────────────────────────────────────────")
    try:
        sys.path.insert(0, ".")
        from tasks.task_registry import TASK_REGISTRY, TASKS_BY_DIFFICULTY
        total = len(TASK_REGISTRY)
        check("Task registry loads", True, f"{total} tasks loaded")

        for diff in ["easy", "medium", "hard"]:
            n = len(TASKS_BY_DIFFICULTY.get(diff, []))
            check(f"{diff} tasks", n >= 3, f"{n} tasks (need ≥ 3)")

        # Validate task structure
        for tid, task in TASK_REGISTRY.items():
            has_required = all(k in task for k in ["id", "difficulty", "cwe_targets", "problem_statement", "test_cases"])
            check(f"task {tid} structure", has_required)

        return True
    except Exception as e:
        check("Task registry import", False, str(e)[:80])
        return False


def validate_api(base_url: str) -> bool:
    print(f"\n── Live API: {base_url} ─────────────────────────────────────")
    all_ok = True

    # Health check
    try:
        r = requests.get(f"{base_url}/health", timeout=10)
        ok = r.status_code == 200
        check("GET /health → 200", ok, r.json().get("env", "") if ok else f"HTTP {r.status_code}")
        if not ok:
            all_ok = False
    except Exception as e:
        check("GET /health", False, str(e)[:60])
        return False

    # Reset
    for diff in ["easy", "medium", "hard"]:
        try:
            r = requests.post(f"{base_url}/reset", json={"difficulty": diff}, timeout=15)
            ok = r.status_code == 200
            if ok:
                data = r.json()
                has_fields = all(k in data for k in ["session_id", "task_id", "problem_statement", "cwe_targets"])
                check(f"POST /reset ({diff})", has_fields, data.get("task_id", ""))
                if not has_fields:
                    all_ok = False

                # Step with trivial code
                sid = data["session_id"]
                step_r = requests.post(f"{base_url}/step", json={
                    "session_id": sid,
                    "code": "def solution(): pass",
                    "filename": "test.py",
                }, timeout=60)
                step_ok = step_r.status_code == 200
                if step_ok:
                    sdata = step_r.json()
                    reward = sdata.get("total_reward", -1)
                    in_range = 0.0 <= reward <= 1.0
                    check(f"POST /step ({diff}) → reward in [0,1]", in_range, f"reward={reward:.3f}")
                    if not in_range:
                        all_ok = False
                else:
                    check(f"POST /step ({diff})", False, f"HTTP {step_r.status_code}")
                    all_ok = False
            else:
                check(f"POST /reset ({diff})", False, f"HTTP {r.status_code}")
                all_ok = False
        except Exception as e:
            check(f"POST /reset ({diff})", False, str(e)[:60])
            all_ok = False

    # State
    try:
        r2 = requests.post(f"{base_url}/reset", json={"difficulty": "easy"}, timeout=10)
        if r2.status_code == 200:
            sid = r2.json()["session_id"]
            state_r = requests.get(f"{base_url}/state", params={"session_id": sid}, timeout=10)
            check("GET /state", state_r.status_code == 200)
    except Exception:
        pass

    return all_ok


def validate_openenv_yaml() -> bool:
    print("\n── openenv.yaml ────────────────────────────────────────────")
    try:
        import yaml
        with open("openenv.yaml") as f:
            spec = yaml.safe_load(f)
        required_keys = ["name", "version", "description", "action_space", "observation_space", "tasks", "reward"]
        for k in required_keys:
            check(f"has '{k}' field", k in spec)
        check("9 tasks defined", len(spec.get("tasks", [])) == 9, f"found {len(spec.get('tasks', []))}")
        return True
    except ImportError:
        print(f"  {WARN} yaml not installed — skipping YAML validation (pip install pyyaml)")
        return True
    except Exception as e:
        check("openenv.yaml parses", False, str(e)[:80])
        return False


def main():
    parser = argparse.ArgumentParser(description="SecureCodeEnv pre-submission validator")
    parser.add_argument("--url", default="http://localhost:7860", help="Base URL of the running environment")
    parser.add_argument("--skip-api", action="store_true", help="Skip live API checks")
    args = parser.parse_args()

    print("=" * 60)
    print("  SecureCodeEnv — Pre-Submission Validator")
    print("=" * 60)

    results = [
        validate_files(),
        validate_imports(),
        validate_task_registry(),
        validate_openenv_yaml(),
    ]

    if not args.skip_api:
        results.append(validate_api(args.url))
    else:
        print(f"\n  {WARN} Skipping live API checks (--skip-api)")

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"  {PASS} ALL CHECKS PASSED ({passed}/{total}) — ready to submit!")
        sys.exit(0)
    else:
        print(f"  {FAIL} {total - passed} check group(s) failed ({passed}/{total} passed)")
        print("  Fix failures before submitting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
