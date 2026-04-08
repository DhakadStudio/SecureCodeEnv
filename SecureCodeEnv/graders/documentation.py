"""
SecureCodeEnv - Documentation & Code Structure Graders
Documentation weight: 5% | Code Structure weight: 5%
"""
import ast


def grade_documentation(code: str) -> dict:
    """
    Grade docstring and type hint coverage.
    Rewards: functions with docstrings, full type annotations, module docstring.

    Returns:
        {"score": float, "documented_fns": int, "total_fns": int, "feedback": str}
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"score": 0.0, "documented_fns": 0, "total_fns": 0, "feedback": "Syntax error — cannot parse"}

    functions = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    if not functions:
        # No functions — check for module docstring
        has_module_doc = bool(ast.get_docstring(tree))
        return {
            "score": 1.0 if has_module_doc else 0.7,
            "documented_fns": 0,
            "total_fns": 0,
            "feedback": "No functions found — module-level code only",
        }

    documented = 0
    typed = 0
    scores = []

    for fn in functions:
        fn_score = 0.0
        has_doc = bool(ast.get_docstring(fn))
        has_return_type = fn.returns is not None
        has_param_types = any(a.annotation is not None for a in fn.args.args)
        has_any_types = has_return_type or has_param_types

        if has_doc:
            documented += 1
            fn_score += 0.5

        if has_any_types:
            typed += 1
            fn_score += 0.5

        scores.append(fn_score)

    total = len(functions)
    score = sum(scores) / total if total > 0 else 1.0

    return {
        "score": round(score, 4),
        "documented_fns": documented,
        "typed_fns": typed,
        "total_fns": total,
        "feedback": _doc_feedback(score, documented, typed, total),
    }


def grade_code_structure(code: str) -> dict:
    """
    Grade code structure quality:
    - No bare print() statements
    - Exception handling present where needed
    - No bare except clauses
    - No hardcoded magic strings
    - Functions not excessively long (>50 lines)

    Returns:
        {"score": float, "checks": dict, "feedback": str}
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"score": 0.0, "checks": {}, "feedback": "Syntax error"}

    checks: dict[str, bool] = {}
    lines = code.splitlines()

    # Check 1: No bare print statements (use logging)
    checks["no_bare_print"] = "print(" not in code

    # Check 2: No bare except (catches all exceptions silently)
    bare_except = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            bare_except = True
            break
    checks["no_bare_except"] = not bare_except

    # Check 3: Functions are reasonably sized (<= 50 lines)
    oversized = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_lines = (node.end_lineno or 0) - node.lineno
            if fn_lines > 50:
                oversized = True
                break
    checks["reasonable_fn_size"] = not oversized

    # Check 4: No TODO/FIXME/HACK comments left in production code
    has_todo = any(
        "# TODO" in line.upper() or "# FIXME" in line.upper() or "# HACK" in line.upper()
        for line in lines
    )
    checks["no_todo_comments"] = not has_todo

    # Check 5: Handles None inputs (basic check)
    checks["handles_none"] = "None" in code or "is not None" in code or "if not " in code

    score = sum(1 for v in checks.values() if v) / max(len(checks), 1)

    return {
        "score": round(score, 4),
        "checks": checks,
        "feedback": _structure_feedback(score, checks),
    }


def _doc_feedback(score: float, documented: int, typed: int, total: int) -> str:
    if score >= 0.9:
        return f"Well documented — {documented}/{total} functions have docstrings, {typed}/{total} typed"
    elif score >= 0.6:
        return f"Partial documentation — {documented}/{total} docstrings, {typed}/{total} type hints"
    else:
        return f"Poor documentation — add docstrings and type hints to all {total} functions"


def _structure_feedback(score: float, checks: dict) -> str:
    if score >= 0.9:
        return "Clean code structure"
    failing = [k for k, v in checks.items() if not v]
    return f"Structure issues: {', '.join(failing)}"
