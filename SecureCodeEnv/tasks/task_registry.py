"""
SecureCodeEnv - Task Registry
Indexes all 9 tasks by ID and difficulty. Serves them via reset().
Adding a new task = add file + add import here. Nothing else changes.
"""
import random
from tasks.easy.password_validator import TASK as TASK_PWD
from tasks.easy.input_sanitizer import TASK as TASK_SANITIZER
from tasks.easy.token_generator import TASK as TASK_TOKEN
from tasks.medium.sql_query_builder import TASK as TASK_SQL
from tasks.medium.file_path_handler import TASK as TASK_PATH
from tasks.medium.rate_limiter import TASK as TASK_RATE
from tasks.hard.file_upload_handler import TASK as TASK_UPLOAD
from tasks.hard.jwt_validator import TASK as TASK_JWT
from tasks.hard.auth_middleware import TASK as TASK_AUTH

# ─── Master registry ────────────────────────────────────────────────────────
TASK_REGISTRY: dict[str, dict] = {
    task["id"]: task
    for task in [
        TASK_PWD, TASK_SANITIZER, TASK_TOKEN,   # Easy
        TASK_SQL, TASK_PATH, TASK_RATE,          # Medium
        TASK_UPLOAD, TASK_JWT, TASK_AUTH,        # Hard
    ]
}

TASKS_BY_DIFFICULTY: dict[str, list[str]] = {
    "easy":   [t for t, v in TASK_REGISTRY.items() if v["difficulty"] == "easy"],
    "medium": [t for t, v in TASK_REGISTRY.items() if v["difficulty"] == "medium"],
    "hard":   [t for t, v in TASK_REGISTRY.items() if v["difficulty"] == "hard"],
}


def get_task(task_id: str) -> dict:
    """Returns a task by ID. Raises KeyError if not found."""
    if task_id not in TASK_REGISTRY:
        raise KeyError(f"Task {task_id!r} not found. Available: {list(TASK_REGISTRY.keys())}")
    return TASK_REGISTRY[task_id]


def sample_task(difficulty: str) -> dict:
    """Returns a random task at the given difficulty level."""
    pool = TASKS_BY_DIFFICULTY.get(difficulty)
    if not pool:
        raise ValueError(f"No tasks for difficulty {difficulty!r}. Use: easy, medium, hard")
    return TASK_REGISTRY[random.choice(pool)]


def list_tasks(difficulty: str = None) -> list[dict]:
    """Lists all tasks, optionally filtered by difficulty."""
    tasks = list(TASK_REGISTRY.values())
    if difficulty:
        tasks = [t for t in tasks if t["difficulty"] == difficulty]
    return [{"id": t["id"], "difficulty": t["difficulty"], "cwe_targets": t["cwe_targets"]} for t in tasks]
