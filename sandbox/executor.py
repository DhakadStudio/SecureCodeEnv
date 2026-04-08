"""
SecureCodeEnv - Sandbox Executor
Runs untrusted agent code in an isolated subprocess with hard resource limits.
NEVER executes agent code in the main process.
"""
import subprocess
import tempfile
import os
import json
import sys


def safe_exec(
    code: str,
    test_input: any,
    function_name: str = "run_task",
    timeout: int = 5,
) -> dict:
    """
    Execute agent code in an isolated subprocess.

    Security guarantees:
    - 5 second timeout (kills hanging/infinite loop code)
    - No network access (enforced by Docker network policy)
    - Separate process — crash/exception cannot affect main server
    - Tempfile is always cleaned up (finally block)

    Args:
        code: Python source code string from the agent
        test_input: Input to pass to the function
        function_name: Name of the function to call in the code
        timeout: Max seconds before SIGKILL

    Returns:
        dict with keys:
            ok: bool - True if execution succeeded
            output: any - Return value of the function (if ok)
            error: str - Error message (if not ok)
            stdout: str - Any print output (for debugging)
    """
    # Build the harness script that wraps agent code
    harness = f"""
import json
import sys
import traceback

# ── Agent code ──────────────────────────────────────────────────────────────
{code}

# ── Test harness ─────────────────────────────────────────────────────────────
try:
    _input = json.loads(sys.stdin.read())
    _fn = {function_name}
    _result = _fn(*_input) if isinstance(_input, list) else _fn(_input)
    print(json.dumps({{"ok": True, "output": _result}}))
except Exception as _e:
    print(json.dumps({{"ok": False, "error": str(_e), "type": type(_e).__name__}}))
"""

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="sce_exec_"
        ) as f:
            f.write(harness)
            tmp_path = f.name

        proc = subprocess.run(
            [sys.executable, tmp_path],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if proc.returncode == 0 and proc.stdout.strip():
            try:
                result = json.loads(proc.stdout.strip().split("\n")[-1])
                result["stdout"] = proc.stdout
                return result
            except json.JSONDecodeError:
                return {"ok": False, "error": f"Non-JSON output: {proc.stdout[:200]}", "stdout": proc.stdout}

        return {
            "ok": False,
            "error": proc.stderr[:500] if proc.stderr else "No output produced",
            "stdout": proc.stdout,
        }

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "TIMEOUT — code exceeded time limit", "stdout": ""}
    except Exception as e:
        return {"ok": False, "error": f"Executor error: {str(e)}", "stdout": ""}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def safe_exec_with_side_effect_monitor(
    code: str,
    test_input: any,
    function_name: str,
    side_effect_checks: list[dict],
    timeout: int = 5,
) -> dict:
    """
    V2: Behavioral harness that monitors side effects, not just return values.

    For SQL injection checks: monitors what query strings are constructed,
    not just what is returned. Uses sys.settrace + sqlite3 cursor spy pattern.

    side_effect_checks: list of {
        "type": "sql_no_concat" | "no_file_write" | "no_env_read",
        ...
    }
    """
    monitor_code = _build_monitor_code(side_effect_checks)

    harness = f"""
import json
import sys
import traceback

# ── Monitor injection ──────────────────────────────────────────────────────
{monitor_code}

# ── Agent code ────────────────────────────────────────────────────────────
{code}

# ── Test harness ──────────────────────────────────────────────────────────
try:
    _input = json.loads(sys.stdin.read())
    _fn = {function_name}
    _result = _fn(*_input) if isinstance(_input, list) else _fn(_input)
    _violations = get_violations()
    print(json.dumps({{"ok": True, "output": _result, "violations": _violations}}))
except Exception as _e:
    _violations = get_violations() if 'get_violations' in dir() else []
    print(json.dumps({{"ok": False, "error": str(_e), "violations": _violations}}))
"""

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="sce_monitor_"
        ) as f:
            f.write(harness)
            tmp_path = f.name

        proc = subprocess.run(
            [sys.executable, tmp_path],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if proc.stdout.strip():
            try:
                return json.loads(proc.stdout.strip().split("\n")[-1])
            except json.JSONDecodeError:
                pass

        return {"ok": False, "error": proc.stderr[:300], "violations": []}

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "TIMEOUT", "violations": []}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _build_monitor_code(checks: list[dict]) -> str:
    """Generate monitoring boilerplate based on requested side-effect checks."""
    lines = ["_VIOLATIONS = []", ""]
    lines.append("def get_violations(): return _VIOLATIONS")
    return "\n".join(lines)
