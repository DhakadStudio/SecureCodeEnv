"""
SecureCodeEnv - Reward Aggregator v3

KEY CHANGES:
1. SECURITY GATE: episode cannot be DONE unless attack_resist >= 0.75
   AND static_security >= 0.70. Prevents insecure code from "winning".
2. Weights rebalanced: static_security raised, performance lowered.
3. DONE threshold raised to 0.92.
4. Security floor penalty: if attack_resist < 0.5 OR static_security < 0.5,
   total reward is capped at 0.65 (cannot fool the system with correctness alone).
"""
from graders.correctness import grade_correctness
from graders.attacks import grade_attacks
from graders.static_analysis import grade_static_analysis
from graders.performance import grade_performance
from graders.consistency import grade_consistency
from graders.documentation import grade_documentation, grade_code_structure
from codegraph.extractor import extract_metadata
from codegraph.graph import CodeGraph

# REBALANCED weights — security dimensions raised
WEIGHTS = {
    "correctness":      0.25,   # was 0.30 — still most important
    "attack_resist":    0.25,   # was 0.20 — raised: must resist real attacks
    "static_security":  0.20,   # was 0.15 — raised: must pass static analysis
    "consistency":      0.10,   # was 0.15 — reduced
    "performance":      0.08,   # was 0.10 — reduced (too noisy)
    "documentation":    0.07,   # was 0.05
    "code_structure":   0.05,   # unchanged
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

# Security gate: these minimums must ALL be met for episode to be DONE
SECURITY_GATE = {
    "attack_resist":   0.75,  # Must block >= 75% of attacks
    "static_security": 0.70,  # Must pass >= 70% of static checks
    "correctness":     0.80,  # Must pass >= 80% of tests
}
DONE_THRESHOLD = 0.92  # Raised from 0.90

# Security floor: if security is critically low, cap total reward
SECURITY_FLOOR_DIMS = ["attack_resist", "static_security"]
SECURITY_FLOOR_THRESHOLD = 0.50
SECURITY_FLOOR_CAP = 0.65


def grade_submission(code, filename, task, graph, step, seed):
    corr  = grade_correctness(code, task)
    atk   = grade_attacks(code, task, seed)
    stat  = grade_static_analysis(code, task)
    perf  = grade_performance(code, task)
    cons  = grade_consistency(code, filename, graph, step)
    doc   = grade_documentation(code)
    struct = grade_code_structure(code)

    scores = {
        "correctness":     corr["score"],
        "attack_resist":   atk["score"],
        "static_security": stat["score"],
        "consistency":     cons["score"],
        "performance":     perf["score"],
        "documentation":   doc["score"],
        "code_structure":  struct["score"],
    }

    raw_reward = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

    # SECURITY FLOOR: insecure code is capped regardless of correctness
    security_critical_fail = any(
        scores[dim] < SECURITY_FLOOR_THRESHOLD
        for dim in SECURITY_FLOOR_DIMS
    )
    if security_critical_fail:
        raw_reward = min(raw_reward, SECURITY_FLOOR_CAP)

    total_reward = round(max(0.0, min(1.0, raw_reward)), 4)

    # SECURITY GATE for done determination
    gate_passed = all(scores[dim] >= threshold
                      for dim, threshold in SECURITY_GATE.items())
    done_eligible = total_reward >= DONE_THRESHOLD and gate_passed

    feedback = {
        "correctness":     corr.get("feedback", ""),
        "attack_resist":   atk.get("feedback", ""),
        "static_security": stat.get("feedback", ""),
        "consistency":     cons.get("feedback", ""),
        "performance":     perf.get("feedback", ""),
        "documentation":   doc.get("feedback", ""),
        "code_structure":  struct.get("feedback", ""),
        "summary":         _summary(total_reward, scores, gate_passed),
        "security_gate":   "PASSED" if gate_passed else _gate_status(scores),
    }

    details = {
        "correctness": {"passed": corr.get("passed"), "total": corr.get("total")},
        "attacks": {"blocked": atk.get("blocked"), "total": atk.get("total"),
                    "type": atk.get("attack_type")},
        "static": {"bandit_score": stat.get("bandit_score"),
                   "hard_fail": stat.get("hard_fail", False),
                   "issues": stat.get("issues", [])[:3]},
        "security_gate_passed": gate_passed,
        "done_eligible": done_eligible,
    }

    return {
        "scores": scores,
        "total_reward": total_reward,
        "done_eligible": done_eligible,
        "feedback": feedback,
        "details": details,
        "agent_ms": perf.get("agent_ms"),
        "naive_ms": perf.get("naive_ms"),
        "optimal_ms": perf.get("optimal_ms"),
        "new_metadata": extract_metadata(code, filename, step),
    }


def _gate_status(scores: dict) -> str:
    failing = [f"{dim} ({scores[dim]:.2f} < {thr})"
               for dim, thr in SECURITY_GATE.items()
               if scores[dim] < thr]
    return f"BLOCKED — security gate not met: {', '.join(failing)}"


def _summary(reward, scores, gate_passed):
    if reward >= DONE_THRESHOLD and gate_passed:
        return f"✅ Excellent ({reward:.3f}) — production-ready, security gate passed"
    if not gate_passed:
        gate_msg = _gate_status(scores)
        return f"🔒 {gate_msg} (reward: {reward:.3f})"
    if reward >= 0.75:
        weakest = min(scores, key=scores.get)
        return f"🟡 Good ({reward:.3f}) — improve: {weakest} ({scores[weakest]:.2f})"
    if reward >= 0.55:
        weak = [k for k, v in scores.items() if v < 0.5]
        return f"🟠 Needs work ({reward:.3f}) — fix: {', '.join(weak[:3])}"
    return f"🔴 Poor ({reward:.3f}) — major security/correctness failures"
