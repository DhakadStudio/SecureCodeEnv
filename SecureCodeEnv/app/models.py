"""SecureCodeEnv - Pydantic Models v2 (production-complete)"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class StepAction(BaseModel):
    session_id: str
    code: str = Field(..., min_length=1)
    filename: str = Field(default="solution.py")
    task_id: Optional[str] = None


class ScoreDetails(BaseModel):
    correctness_passed: Optional[int] = None
    correctness_total: Optional[int] = None
    attacks_blocked: Optional[int] = None
    attacks_total: Optional[int] = None
    attack_type: Optional[str] = None
    bandit_score: Optional[float] = None
    static_issues_count: Optional[int] = None
    agent_ms: Optional[float] = None
    naive_ms: Optional[float] = None
    optimal_ms: Optional[float] = None


class StepObservation(BaseModel):
    scores: Dict[str, float]
    total_reward: float
    feedback: Dict[str, str]
    codegraph: Dict[str, Any]
    done: bool
    step_count: int
    details: Optional[ScoreDetails] = None


class ResetRequest(BaseModel):
    difficulty: Optional[str] = Field(default="medium")
    task_id: Optional[str] = Field(default=None, description="Override: request a specific task ID")
    session_id: Optional[str] = None


class ResetObservation(BaseModel):
    session_id: str
    task_id: str
    problem_statement: str
    difficulty: str
    cwe_targets: List[str]
    codegraph: Dict[str, Any]
    starter_code: str = ""
    naive_baseline: Optional[Dict] = None


class StateResponse(BaseModel):
    session_id: str
    task_id: str
    step: int
    done: bool
    codegraph: Dict[str, Any]
    difficulty: str
    scores_history: List[float] = []


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str
    tasks_loaded: int


class TaskSummary(BaseModel):
    id: str
    difficulty: str
    cwe_targets: List[str]
    description: str = ""
