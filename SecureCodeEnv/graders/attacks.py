"""
SecureCodeEnv - Attack Resistance Grader v3

FIXED:
- All check lambdas handle list OR tuple (JSON round-trip)
- Path traversal check: blocks absolute paths + encoded paths, not just '..'
- SQL check: verifies placeholder present AND payload not injected
- Consistent scoring regardless of seed
"""
from sandbox.executor import safe_exec
from sandbox.payload_gen import get_payloads


def _is_seq(v):
    return isinstance(v, (list, tuple))


def _sql_safe(result, payload):
    """SQL query output is safe when: is 2-element seq, query has placeholder, raw payload not in query."""
    if not _is_seq(result) or len(result) < 2:
        return False
    query = str(result[0])
    # Must use parameterized placeholder
    if not any(p in query for p in ("%s", "?", ":param", "%(", ":%")):
        return False
    # The raw payload (stripped of whitespace) must NOT appear verbatim in the query
    payload_stripped = payload.strip().replace(" ", "").lower()
    query_lower = query.lower().replace(" ", "")
    if payload_stripped in query_lower:
        return False
    return True


def _path_safe(result, payload):
    """
    Path output is safe when resolved path stays inside /var/uploads.
    Also catches: absolute paths (/etc/), encoded paths (%2e), null bytes.
    """
    if result is None:
        return True  # Rejected = safe
    if not isinstance(result, str):
        return True
    r = result.lower()
    # Must stay inside base
    if not result.startswith("/var/uploads"):
        return False
    # Must not contain escape indicators
    bad = ["/etc/", "/root/", "/proc/", "/var/log", "passwd", "shadow",
           "%2e", "%2f", ".."]
    return not any(b in r for b in bad)


ATTACK_CONFIGS = {
    "medium_sql_query_builder": {
        "fn_name": "build_user_query",
        "fn_args_template": ["{payload}", "admin"],
        "attack_type": "injection",
        "check": _sql_safe,
        "exception_is_pass": False,  # SQL builder shouldn't raise on injection input
    },
    "medium_file_path_handler": {
        "fn_name": "resolve_safe_path",
        "fn_args_template": ["/var/uploads", "{payload}"],
        "attack_type": "traversal",
        "check": _path_safe,
        "exception_is_pass": True,  # Raising ValueError = correct
    },
    "hard_file_upload_handler": {
        "fn_name": "validate_upload",
        "fn_args_template": ["{payload}", "image/jpeg", 1000, "/uploads"],
        "attack_type": "traversal",
        "check": lambda result, payload: (
            isinstance(result, dict) and
            (result.get("ok") is False or
             not any(b in str(result.get("safe_path", "")).lower()
                     for b in ["..", "/etc/", "/root/", "%2e"]))
        ),
        "exception_is_pass": True,
    },
    "hard_jwt_validator": {
        "fn_name": "validate_token",
        "fn_args_template": ["{payload}", "test_secret_key_for_grading"],
        "attack_type": "auth_bypass",
        "check": lambda result, payload: result is None,
        "exception_is_pass": True,
    },
    "hard_auth_middleware": {
        "fn_name": "verify_csrf_token",
        "fn_args_template": ["{payload}", "legitimate_session_csrf_token"],
        "attack_type": "auth_bypass",
        "check": lambda result, payload: result is False,
        "exception_is_pass": True,
    },
    "easy_input_sanitizer": {
        "fn_name": "sanitize_html",
        "fn_args_template": ["{payload}"],
        "attack_type": "xss",
        "check": lambda result, payload: (
            isinstance(result, str) and
            not any(b in result.lower() for b in
                    ["<script", "onerror", "javascript:", "<img ", "<svg", "onload"])
        ),
        "exception_is_pass": False,
    },
    "easy_input_sanitizer_filename": {
        "fn_name": "sanitize_filename",
        "fn_args_template": ["{payload}"],
        "attack_type": "traversal",
        "check": lambda result, payload: (
            isinstance(result, str) and
            ".." not in result and "/" not in result and "\\" not in result
        ),
        "exception_is_pass": False,
    },
}


def grade_attacks(code: str, task: dict, seed: int) -> dict:
    task_id = task.get("id", "")
    config = ATTACK_CONFIGS.get(task_id)
    if not config:
        return {
            "score": 1.0, "blocked": 0, "total": 0,
            "attack_type": "none",
            "feedback": "No attack grading defined for this task type",
        }

    payloads = get_payloads(config["attack_type"], seed=seed, count=8)
    if not payloads:
        return {"score": 1.0, "blocked": 0, "total": 0,
                "attack_type": config["attack_type"], "feedback": "No payloads generated"}

    blocked = 0
    exception_is_pass = config.get("exception_is_pass", True)

    for payload in payloads:
        raw_args = config["fn_args_template"]
        args = [a.replace("{payload}", payload) if isinstance(a, str) else a
                for a in raw_args]
        result = safe_exec(code, args, function_name=config["fn_name"], timeout=3)

        if not result["ok"]:
            if exception_is_pass:
                blocked += 1
        else:
            output = result.get("output")
            try:
                if config["check"](output, payload):
                    blocked += 1
            except Exception:
                pass

    score = blocked / len(payloads)
    return {
        "score": round(score, 4),
        "blocked": blocked,
        "total": len(payloads),
        "attack_type": config["attack_type"],
        "feedback": _feedback(score, config["attack_type"]),
    }


def _feedback(score: float, attack_type: str) -> str:
    names = {
        "injection": "SQL injection", "traversal": "path traversal",
        "auth_bypass": "authentication bypass", "xss": "XSS",
    }
    name = names.get(attack_type, attack_type)
    if score >= 0.875: return f"Excellent — {name} attacks blocked ({score:.0%})"
    elif score >= 0.625: return f"Good — most {name} attacks blocked ({score:.0%})"
    elif score >= 0.375: return f"Partial — only {score:.0%} of {name} attacks blocked"
    else: return f"Vulnerable — {score:.0%} of {name} attacks blocked — CRITICAL"
