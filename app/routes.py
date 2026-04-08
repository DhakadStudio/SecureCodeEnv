"""SecureCodeEnv - Routes v2 (production-complete)"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models import (
    StepAction, StepObservation, ScoreDetails,
    ResetRequest, ResetObservation,
    StateResponse, TaskSummary,
)
from app.state import EpisodeState
from graders.reward_aggregator import grade_submission
from tasks.task_registry import sample_task, get_task, TASK_REGISTRY, list_tasks
from codegraph.graph import CodeGraph
from codegraph.serializer import serialize_graph
import uuid, threading

router = APIRouter()
_sessions: dict[str, EpisodeState] = {}
_lock = threading.Lock()
MAX_STEPS = 5
DONE_THRESHOLD = 0.90


def _cleanup():
    with _lock:
        expired = [k for k, v in _sessions.items() if v.is_expired()]
        for k in expired:
            del _sessions[k]


# ── POST /reset ──────────────────────────────────────────────────────────────
@router.post("/reset", response_model=ResetObservation, tags=["OpenEnv"])
def reset(body: ResetRequest = None):
    """Start a new episode. Returns task + initial CodeGraph."""
    _cleanup()
    if body is None:
        body = ResetRequest()

    # Support specific task_id override
    if body.task_id:
        try:
            task = get_task(body.task_id)
        except KeyError:
            raise HTTPException(404, f"task_id {body.task_id!r} not found. "
                                f"Available: {list(TASK_REGISTRY.keys())}")
        difficulty = task["difficulty"]
    else:
        difficulty = (body.difficulty or "medium").lower()
        if difficulty not in ("easy", "medium", "hard"):
            raise HTTPException(400, f"difficulty must be easy/medium/hard. Got: {difficulty!r}")
        task = sample_task(difficulty)

    sid = body.session_id or str(uuid.uuid4())
    graph = CodeGraph(episode_seed=abs(hash(sid)) % 999_999)
    state = EpisodeState(task=task, graph=graph, step=0, done=False)

    with _lock:
        _sessions[sid] = state

    return ResetObservation(
        session_id=sid,
        task_id=task["id"],
        problem_statement=task["problem_statement"],
        difficulty=difficulty,
        cwe_targets=task["cwe_targets"],
        codegraph=serialize_graph(graph),
        starter_code=task.get("starter_code", ""),
        naive_baseline={"code": task.get("naive_code", "")},
    )


# ── POST /step ───────────────────────────────────────────────────────────────
@router.post("/step", response_model=StepObservation, tags=["OpenEnv"])
def step(action: StepAction):
    """Submit code. Returns multi-dimensional reward + updated CodeGraph."""
    with _lock:
        state = _sessions.get(action.session_id)

    if state is None:
        raise HTTPException(404, "Session not found — call POST /reset first.")
    if state.done:
        raise HTTPException(400, "Episode done — call POST /reset to start a new one.")
    if not action.code or not action.code.strip():
        raise HTTPException(422, "code must be a non-empty Python string.")

    result = grade_submission(
        code=action.code,
        filename=action.filename or "solution.py",
        task=state.task,
        graph=state.graph,
        step=state.step,
        seed=state.graph.episode_seed + state.step,
    )

    state.graph.update(action.filename or "solution.py", result["new_metadata"])
    state.step += 1
    state.scores_history.append(result["total_reward"])
    state.done = result.get("done_eligible", False) or state.step >= MAX_STEPS

    # Build structured details object
    raw = result.get("details", {}) or {}
    details = ScoreDetails(
        correctness_passed=raw.get("correctness", {}).get("passed"),
        correctness_total=raw.get("correctness", {}).get("total"),
        attacks_blocked=raw.get("attacks", {}).get("blocked"),
        attacks_total=raw.get("attacks", {}).get("total"),
        attack_type=raw.get("attacks", {}).get("type"),
        bandit_score=raw.get("static", {}).get("bandit_score"),
        static_issues_count=len(raw.get("static", {}).get("issues", [])),
        agent_ms=result.get("agent_ms"),
        naive_ms=result.get("naive_ms"),
        optimal_ms=result.get("optimal_ms"),
    )

    return StepObservation(
        scores=result["scores"],
        total_reward=result["total_reward"],
        feedback=result["feedback"],
        codegraph=serialize_graph(state.graph),
        done=state.done,
        step_count=state.step,
        details=details,
    )


# ── GET /state ───────────────────────────────────────────────────────────────
@router.get("/state", response_model=StateResponse, tags=["OpenEnv"])
def get_state(session_id: str):
    """Get current episode state without advancing it."""
    with _lock:
        state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(404, "Session not found.")

    return StateResponse(
        session_id=session_id,
        task_id=state.task["id"],
        step=state.step,
        done=state.done,
        codegraph=serialize_graph(state.graph),
        difficulty=state.task.get("difficulty", "medium"),
        scores_history=state.scores_history,
    )


# ── GET /tasks ───────────────────────────────────────────────────────────────
@router.get("/tasks", response_model=List[TaskSummary], tags=["Discovery"])
def get_tasks(difficulty: Optional[str] = Query(None)):
    """List all available tasks, optionally filtered by difficulty."""
    raw = list_tasks(difficulty)
    return [
        TaskSummary(
            id=t["id"],
            difficulty=t["difficulty"],
            cwe_targets=t["cwe_targets"],
            description=TASK_REGISTRY[t["id"]].get("problem_statement", "")[:120] + "…",
        )
        for t in raw
    ]


# ── GET /tasks/{task_id} ─────────────────────────────────────────────────────
@router.get("/tasks/{task_id}", tags=["Discovery"])
def get_task_detail(task_id: str):
    """Get full detail for a specific task."""
    try:
        task = get_task(task_id)
    except KeyError:
        raise HTTPException(404, f"Task {task_id!r} not found.")
    return {
        "id": task["id"],
        "difficulty": task["difficulty"],
        "cwe_targets": task["cwe_targets"],
        "problem_statement": task["problem_statement"],
        "starter_code": task.get("starter_code", ""),
        "attack_type": task.get("attack_type", "none"),
        "security_checks": task.get("security_checks", []),
    }
