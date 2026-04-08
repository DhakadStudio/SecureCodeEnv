"""
SecureCodeEnv - Static Analysis Grader v3

FIXED:
- HIGH severity issues now cap the score at 0.40 max (was just subtracting 0.30)
- Task-specific security checks have hard caps when violated
- bandit penalty curve is steeper
"""
import subprocess, json, tempfile, os, ast, re


def grade_static_analysis(code: str, task: dict) -> dict:
    bandit = _run_bandit(code)
    custom = _run_custom_checks(code, task)

    # If a HARD security requirement is violated, cap at 0.40 regardless of bandit
    if custom.get("hard_fail"):
        final_score = min(bandit["score"] * 0.4, 0.40)
    else:
        final_score = (bandit["score"] * 0.60) + (custom["score"] * 0.40)

    all_issues = bandit.get("issues", []) + custom.get("issues", [])

    return {
        "score": round(max(0.0, min(1.0, final_score)), 4),
        "bandit_score": bandit["score"],
        "ast_score": custom["score"],
        "hard_fail": custom.get("hard_fail", False),
        "issues": all_issues[:10],
        "feedback": _feedback(final_score, all_issues, custom.get("hard_fail", False)),
    }


def _run_bandit(code: str) -> dict:
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                         delete=False, prefix="sce_ban_") as f:
            f.write(code); tmp = f.name

        res = subprocess.run(
            ["bandit", "-r", tmp, "-f", "json", "-q", "--exit-zero"],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(res.stdout or '{"results":[]}')
        issues = data.get("results", [])

        # Steeper penalty curve + cap at 3 HIGH issues = 0.0
        penalty = 0.0
        for i in issues:
            sev = i.get("issue_severity", "LOW")
            if sev == "HIGH":   penalty += 0.40
            elif sev == "MEDIUM": penalty += 0.20
            else:               penalty += 0.05

        score = max(0.0, 1.0 - penalty)
        return {
            "score": round(score, 4),
            "issues": [{"severity": i.get("issue_severity"),
                        "text": i.get("issue_text", "")[:100],
                        "line": i.get("line_number")} for i in issues[:5]],
        }
    except FileNotFoundError:
        return {"score": 1.0, "issues": [], "note": "bandit not installed"}
    except Exception as e:
        return {"score": 1.0, "issues": [], "note": str(e)[:40]}
    finally:
        if tmp and os.path.exists(tmp):
            try: os.unlink(tmp)
            except OSError: pass


# Security requirements per task — violation = hard_fail (cap at 0.40)
HARD_REQUIREMENTS = {
    "easy_password_validator": [
        {"type": "forbidden_any", "patterns": ["hashlib.md5", "hashlib.sha1", "hashlib.sha256",
                                                "md5(", "sha1(", "sha256("],
         "message": "Weak hash function used — must use bcrypt"},
        {"type": "forbidden_any", "patterns": ["random.random(", "random.randint("],
         "message": "Insecure randomness"},
    ],
    "easy_token_generator": [
        {"type": "forbidden_any", "patterns": ["random.random(", "random.randint(",
                                                "random.choice(", "random.seed("],
         "message": "Weak PRNG used for token generation — must use secrets module"},
        {"type": "required_any", "patterns": ["secrets"],
         "message": "secrets module not imported"},
    ],
    "medium_sql_query_builder": [
        {"type": "forbidden_pattern",
         "regex": r'f["\'].*SELECT.*{',
         "message": "f-string SQL query — SQL injection vulnerability"},
        {"type": "forbidden_pattern",
         "regex": r'["\']\s*\+\s*(username|role|user_input|query)',
         "message": "String concatenation in SQL — SQL injection vulnerability"},
        {"type": "forbidden_pattern",
         "regex": r'%\s*\(',
         "message": "% formatting in SQL — potential injection"},
    ],
    "medium_file_path_handler": [
        {"type": "forbidden_any",
         "patterns": ['"..\" in', "'..' in", '".." in', "\"..\" in"],
         "message": "String check for '..' is bypassable — use Path.resolve()"},
        {"type": "required_any",
         "patterns": ["resolve()", ".resolve", "realpath"],
         "message": "Must use os.path.realpath or Path.resolve() to prevent traversal"},
    ],
    "hard_jwt_validator": [
        {"type": "forbidden_any",
         "patterns": ["verify_signature\": False", "verify_signature':False",
                      "verify_exp\": False", "algorithms=[\"none\"", "algorithms=['none'"],
         "message": "JWT verification disabled — security bypass"},
        {"type": "required_any",
         "patterns": ["algorithms="],
         "message": "algorithms= not specified — alg:none attack possible"},
    ],
    "hard_auth_middleware": [
        {"type": "required_any",
         "patterns": ["hmac.compare_digest"],
         "message": "hmac.compare_digest not used — timing attack possible"},
        {"type": "forbidden_pattern",
         "regex": r'==\s*(session_token|request_token|secret|token)',
         "message": "== used for secret comparison — timing attack"},
    ],
    "easy_input_sanitizer": [
        {"type": "forbidden_any",
         "patterns": ["eval(", "exec("],
         "message": "eval/exec used — remote code execution risk"},
    ],
    "hard_file_upload_handler": [
        {"type": "required_any",
         "patterns": ["uuid"],
         "message": "uuid not used — filename collisions possible"},
        {"type": "required_any",
         "patterns": [".suffix", "splitext", "os.path.splitext"],
         "message": "Extension not checked via proper method"},
    ],
}

# Soft checks (no hard cap) — applied to all tasks
GENERIC_CHECKS = [
    {"type": "forbidden_any", "patterns": ["eval(", "exec("],
     "message": "eval/exec usage", "severity": "HIGH"},
    {"type": "forbidden_any", "patterns": ["shell=True"],
     "message": "shell=True enables command injection", "severity": "HIGH"},
    {"type": "forbidden_any", "patterns": ["pickle.loads", "pickle.load"],
     "message": "Unsafe pickle deserialization", "severity": "HIGH"},
    {"type": "forbidden_any", "patterns": ["yaml.load("],
     "message": "Unsafe yaml.load", "severity": "MEDIUM"},
    {"type": "forbidden_any", "patterns": ["hashlib.md5", "hashlib.sha1"],
     "message": "Weak hash function", "severity": "HIGH"},
]


def _run_custom_checks(code: str, task: dict) -> dict:
    issues = []
    hard_fail = False
    checks_passed = 0
    total_checks = 0

    # Generic checks
    for chk in GENERIC_CHECKS:
        total_checks += 1
        found = _check_code(code, chk)
        if found:
            issues.append({"check": chk["message"], "severity": chk.get("severity","MEDIUM"),
                           "message": chk["message"]})
        else:
            checks_passed += 1

    # Task-specific hard requirements
    task_id = task.get("id", "")
    for req in HARD_REQUIREMENTS.get(task_id, []):
        total_checks += 1
        violated = _check_requirement_violated(code, req)
        if violated:
            hard_fail = True
            issues.append({"check": req["message"], "severity": "CRITICAL",
                           "message": req["message"]})
        else:
            checks_passed += 1

    score = checks_passed / max(total_checks, 1)
    return {"score": round(score, 4), "issues": issues, "hard_fail": hard_fail}


def _check_code(code: str, chk: dict) -> bool:
    """Returns True if the violation is found."""
    t = chk.get("type", "")
    if t == "forbidden_any":
        return any(p in code for p in chk.get("patterns", []))
    if t == "required_any":
        return not any(p in code for p in chk.get("patterns", []))
    if t == "forbidden_pattern":
        return bool(re.search(chk.get("regex", "NOMATCH"), code, re.IGNORECASE))
    return False


def _check_requirement_violated(code: str, req: dict) -> bool:
    """Returns True if requirement is violated (= bad)."""
    t = req.get("type", "")
    if t == "forbidden_any":
        return any(p in code for p in req.get("patterns", []))
    if t == "required_any":
        return not any(p in code for p in req.get("patterns", []))
    if t == "forbidden_pattern":
        return bool(re.search(req.get("regex", "NOMATCH"), code, re.IGNORECASE | re.DOTALL))
    return False


def _feedback(score: float, issues: list, hard_fail: bool) -> str:
    if hard_fail:
        critical = [i["message"] for i in issues if i.get("severity") == "CRITICAL"]
        return f"CRITICAL security violation: {'; '.join(critical[:2])}"
    if score >= 0.9: return "Clean — no significant security issues"
    high = sum(1 for i in issues if i.get("severity") == "HIGH")
    if high > 0: return f"{high} HIGH severity issue(s) — must fix"
    return f"Some security issues found (score: {score:.2f})"
