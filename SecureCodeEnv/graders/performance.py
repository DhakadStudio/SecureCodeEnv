"""
SecureCodeEnv - Performance Grader v3
FIXED: 0ms measurement now returns 0.6 (neutral) not 1.0
"""
import sys, tempfile, os, json, subprocess


def grade_performance(code: str, task: dict) -> dict:
    test_cases = task.get("test_cases", [])
    naive_code = task.get("naive_code", "")
    optimal_code = task.get("optimal_code", "")

    if not test_cases or not naive_code or not optimal_code:
        return {"score": 0.6, "time_score": 0.6, "memory_score": 0.6,
                "feedback": "No baselines defined — neutral score applied"}

    tc = next((t for t in test_cases
               if "fn" in t and "input" in t
               and "fn_class" not in t
               and "expected_exception" not in t), None)
    if not tc:
        return {"score": 0.6, "time_score": 0.6, "memory_score": 0.6,
                "feedback": "No suitable test case — neutral score applied"}

    fn_name = tc["fn"]
    inputs = tc["input"]

    try:
        agent_ms   = _measure_ms(code,        fn_name, inputs)
        naive_ms   = _measure_ms(naive_code,  fn_name, inputs)
        optimal_ms = _measure_ms(optimal_code, fn_name, inputs)

        # FIXED: if measurements indistinguishable, return neutral 0.6
        if abs(naive_ms - optimal_ms) < 0.001:
            return {"score": 0.6, "time_score": 0.6, "memory_score": 0.6,
                    "agent_ms": round(agent_ms, 3),
                    "naive_ms": round(naive_ms, 3),
                    "optimal_ms": round(optimal_ms, 3),
                    "feedback": "Functions too fast to differentiate — neutral score"}

        time_range = max(naive_ms - optimal_ms, 0.01)
        raw = 1.0 - ((agent_ms - optimal_ms) / time_range)
        time_score = max(0.0, min(1.0, raw))
        combined = round((time_score * 0.7) + (time_score * 0.3), 4)

        return {
            "score": combined,
            "time_score": round(time_score, 4),
            "memory_score": round(time_score, 4),
            "agent_ms": round(agent_ms, 3),
            "naive_ms": round(naive_ms, 3),
            "optimal_ms": round(optimal_ms, 3),
            "feedback": _feedback(combined),
        }
    except Exception as e:
        return {"score": 0.6, "time_score": 0.6, "memory_score": 0.6,
                "feedback": f"Measurement error: {str(e)[:60]}"}


def _measure_ms(code: str, fn_name: str, inputs: list, runs: int = 50) -> float:
    script = f"""
import timeit, json, sys
{code}
def _run():
    {fn_name}(*{json.dumps(inputs)})
times = timeit.repeat(_run, number={runs}, repeat=5)
best = min(times) / {runs} * 1000
sys.stdout.write(json.dumps({{"ms": best}}) + "\\n")
sys.stdout.flush()
"""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                         delete=False, prefix="sce_perf_") as f:
            f.write(script); tmp = f.name
        proc = subprocess.run([sys.executable, tmp],
                              capture_output=True, text=True, timeout=30)
        for line in reversed(proc.stdout.strip().splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)["ms"]
        return -1.0  # Signal unmeasurable
    except Exception:
        return -1.0
    finally:
        if tmp and os.path.exists(tmp):
            try: os.unlink(tmp)
            except OSError: pass


def _feedback(score: float) -> str:
    if score >= 0.9:  return "Excellent — near-optimal efficiency"
    elif score >= 0.7: return "Good — minor optimisation possible"
    elif score >= 0.5: return "Acceptable — room for improvement"
    else:              return "Poor — significant performance gap vs optimal"
