"""
SecureCodeEnv - Consistency Grader v3
FIXED: Step 0 no longer gives free 1.0 — rewards ESTABLISHING good practices
"""
from codegraph.graph import CodeGraph
from codegraph.extractor import extract_metadata


# Minimum quality bar for first submission (establishing conventions)
GOOD_PRACTICES = {
    "uses_type_hints": ("Type hints present", 0.15),
    "uses_docstrings":  ("Docstrings present", 0.15),
    "uses_try_catch":   ("Error handling present", 0.10),
    "no_print_stmts":   ("No debug print statements", 0.10),
    "no_hardcoded_secrets": ("No hardcoded secrets detected", 0.10),
}


def grade_consistency(code: str, filename: str, graph: CodeGraph, step: int) -> dict:
    new_meta = extract_metadata(code, filename, step)
    conv = new_meta.conventions

    if not graph.components:
        # Step 0: score on how well the agent ESTABLISHES good practices
        checks = {}
        for key, (label, _) in GOOD_PRACTICES.items():
            checks[key] = 1.0 if conv.get(key, False) else 0.0

        score = sum(checks.values()) / max(len(checks), 1)
        # Minimum 0.5 so this doesn't destroy reward on first step
        score = max(0.5, score)

        return {
            "score": round(score, 4),
            "checks": checks,
            "feedback": _first_step_feedback(score, checks),
        }

    # Step 1+: check consistency with established conventions
    established = graph.conventions
    checks = {}

    # Naming convention
    naming = established.get("naming")
    if naming and naming != "mixed" and new_meta.functions:
        fns = new_meta.functions
        if naming == "snake_case":
            correct = sum(1 for f in fns if "_" in f["name"] or f["name"].islower())
        else:
            correct = sum(1 for f in fns if f["name"] and f["name"][0].islower()
                          and any(c.isupper() for c in f["name"]))
        checks["naming_convention"] = correct / len(fns)

    # Error handling
    if established.get("error_handling") == "try_catch":
        checks["error_handling"] = 1.0 if conv.get("uses_try_catch") else 0.3

    # Type hints
    if established.get("uses_type_hints"):
        checks["type_hints"] = 1.0 if conv.get("uses_type_hints") else 0.4

    # Docstrings
    if established.get("uses_docstrings"):
        checks["docstrings"] = 1.0 if conv.get("uses_docstrings") else 0.5

    # No print drift
    existing_no_print = all(c.conventions.get("no_print_stmts", True)
                            for c in graph.components.values())
    if existing_no_print:
        checks["no_print_drift"] = 1.0 if conv.get("no_print_stmts", True) else 0.3

    # Component reuse
    reuse_opp = reuse_taken = 0
    for comp_name in graph.components:
        if comp_name.lower() in code.lower():
            reuse_opp += 1
            if comp_name in code:
                reuse_taken += 1
    if reuse_opp > 0:
        checks["component_reuse"] = reuse_taken / reuse_opp

    score = sum(checks.values()) / max(len(checks), 1) if checks else 0.8
    return {
        "score": round(score, 4),
        "checks": checks,
        "feedback": _consistency_feedback(score, checks),
    }


def _first_step_feedback(score: float, checks: dict) -> str:
    missing = [k for k, v in checks.items() if v == 0.0]
    if not missing:
        return f"Good conventions established (score: {score:.2f})"
    return f"Missing good practices: {', '.join(missing)} — add type hints, docstrings, error handling"


def _consistency_feedback(score: float, checks: dict) -> str:
    if score >= 0.9:
        return "Excellent consistency with existing codebase conventions"
    failing = [k for k, v in checks.items() if isinstance(v, float) and v < 0.5]
    if failing:
        return f"Convention drift in: {', '.join(failing)}"
    return f"Minor convention drift (score: {score:.2f})"
