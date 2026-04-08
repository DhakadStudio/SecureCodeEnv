"""
SecureCodeEnv - Correctness Grader
Runs each task's test cases against the agent's submitted code.
Weight: 30% of total reward — the highest single weight.
"""
from sandbox.executor import safe_exec

def _is_seq(v):
    return isinstance(v, (list, tuple))


def grade_correctness(code: str, task: dict) -> dict:
    """
    Runs the task's test cases against the agent's code.

    Returns:
        {
            "score": float 0.0-1.0,
            "passed": int,
            "total": int,
            "details": list of per-test results
        }
    """
    test_cases = task.get("test_cases", [])
    if not test_cases:
        return {"score": 1.0, "passed": 0, "total": 0, "details": [], "feedback": "No test cases defined"}

    passed = 0
    details = []

    for tc in test_cases:
        result = _run_test_case(code, tc)
        if result["passed"]:
            passed += 1
        details.append(result)

    score = passed / len(test_cases) if test_cases else 1.0
    return {
        "score": round(score, 4),
        "passed": passed,
        "total": len(test_cases),
        "details": details,
        "feedback": _correctness_feedback(score, passed, len(test_cases)),
    }


def _run_test_case(code: str, tc: dict) -> dict:
    """Execute a single test case and evaluate the result."""
    fn_name = tc.get("fn", "solution")
    inputs = tc.get("input", [])
    description = tc.get("description", "")

    # Handle class-based tasks
    if "fn_class" in tc:
        return _run_class_test(code, tc)

    exec_result = safe_exec(code, inputs, function_name=fn_name, timeout=5)

    if not exec_result["ok"]:
        expected_exc = tc.get("expected_exception")
        error_str = exec_result.get("error", "")
        exc_type = exec_result.get("type", "")  # executor returns type field
        if expected_exc:
            exc_raised = (
                exc_type == expected_exc or
                expected_exc.lower() in error_str.lower() or
                expected_exc.lower() in exc_type.lower()
            )
            if exc_raised:
                return {"passed": True, "description": description, "note": f"Expected {expected_exc} raised"}
        return {"passed": False, "description": description, "error": error_str[:200]}

    output = exec_result.get("output")

    # Not-None check
    if "expected_not_none" in tc:
        ok = output is not None
        return {"passed": ok, "description": description}

    # SQL injection safety check: payload must NOT appear in query, placeholder must exist
    if tc.get("sql_injection_check"):
        if not _is_seq(output) or len(output) < 2:
            return {"passed": False, "description": description, "error": "Not a 2-element tuple"}
        query = str(output[0])
        payload_val = inputs[0] if inputs else ""
        has_placeholder = any(p in query for p in ("%s", "?", ":param", "%(username"))
        payload_not_in_query = str(payload_val).strip() not in query
        ok = has_placeholder and payload_not_in_query
        return {"passed": ok, "description": description,
                "note": f"placeholder={has_placeholder} payload_safe={payload_not_in_query}"}

    # Standard equality check
    if "expected" in tc:
        expected = tc["expected"]
        ok = output == expected
        return {"passed": ok, "description": description, "got": output, "expected": expected}

    # Type check (JSON serialization converts tuple→list, so treat them as equivalent)
    if "expected_type" in tc:
        type_name = tc["expected_type"]
        actual_type = type(output).__name__
        # tuple and list are equivalent after JSON round-trip
        equivalent = {("tuple", "list"), ("list", "tuple")}
        ok = actual_type == type_name or (actual_type, type_name) in equivalent or (type_name, actual_type) in equivalent
        if ok and "expected_len" in tc:
            ok = hasattr(output, "__len__") and len(output) == tc["expected_len"]
        return {"passed": ok, "description": description, "got_type": actual_type}

    # Contains check
    if "expected_contains" in tc:
        ok = tc["expected_contains"] in str(output)
        return {"passed": ok, "description": description}

    # Not-contains check
    if "expected_not_contains" in tc:
        forbidden = tc["expected_not_contains"]
        if isinstance(forbidden, list):
            ok = not any(f in str(output) for f in forbidden)
        else:
            ok = forbidden not in str(output)
        return {"passed": ok, "description": description, "got": str(output)[:100]}

    # Min length check
    if "expected_min_len" in tc:
        ok = output is not None and len(str(output)) >= tc["expected_min_len"]
        return {"passed": ok, "description": description}

    # Max length check
    if "expected_max_len" in tc:
        ok = output is not None and len(str(output)) <= tc["expected_max_len"]
        return {"passed": ok, "description": description}

    # Ok-flag check (for validate_upload style returns)
    if "expected_ok" in tc:
        ok = isinstance(output, dict) and output.get("ok") == tc["expected_ok"]
        return {"passed": ok, "description": description}

    # No expected value defined — just check it didn't crash
    return {"passed": True, "description": description, "note": "No assertion defined"}


def _run_class_test(code: str, tc: dict) -> dict:
    """Run a test against a class-based task (e.g. RateLimiter)."""
    class_name = tc.get("fn_class", "Solution")
    init_args = tc.get("init_args", [])
    method = tc.get("method", "is_allowed")
    inputs = tc.get("input", [])
    description = tc.get("description", "")

    harness_code = f"""
{code}

def run_task(args):
    init_args = args[0]
    method = args[1]
    inputs = args[2]
    obj = {class_name}(*init_args)
    if method == "is_allowed_multi":
        result = None
        for _ in range(3):
            result = obj.is_allowed(inputs[0])
        return result
    if method == "independent_clients":
        r1 = obj.is_allowed("client_a")
        r2 = obj.is_allowed("client_b")
        return r1 == r2 == True
    fn = getattr(obj, method)
    return fn(*inputs)
"""
    test_input = [[init_args, method, inputs]]  # wrap in list so safe_exec unpacks correctly
    result = safe_exec(harness_code, test_input, function_name="run_task", timeout=5)

    if not result["ok"]:
        return {"passed": False, "description": description, "error": result.get("error", "")[:200]}

    output = result.get("output")
    if "expected" in tc:
        ok = output == tc["expected"]
        return {"passed": ok, "description": description}
    if "expected_last" in tc:
        ok = output == tc["expected_last"]
        return {"passed": ok, "description": description}
    return {"passed": True, "description": description}


def _correctness_feedback(score: float, passed: int, total: int) -> str:
    if score >= 0.9:
        return f"Excellent — {passed}/{total} tests passed"
    elif score >= 0.7:
        return f"Good — {passed}/{total} tests passed. Minor edge cases missing"
    elif score >= 0.5:
        return f"Partial — {passed}/{total} tests passed. Fix failing cases"
    else:
        return f"Poor — {passed}/{total} tests passed. Core logic incorrect"
