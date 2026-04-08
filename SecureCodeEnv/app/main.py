"""
SecureCodeEnv - FastAPI Application Entry Point
Built for Meta x PyTorch OpenEnv Hackathon 2026
Author: Vishal Dhakad (vishaldhakad)
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.models import HealthResponse
from app.dashboard import DASHBOARD_HTML
from tasks.task_registry import TASK_REGISTRY

app = FastAPI(
    title="SecureCodeEnv",
    description=(
        "An RL environment for training LLM agents to write production-ready, secure Python code. "
        "Agents are graded on correctness, attack resistance, CWE-based static analysis, "
        "performance, and codebase consistency via a novel CodeGraph memory system."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Health check — required by hackathon automated ping."""
    return HealthResponse(
        status="ok",
        env="SecureCodeEnv",
        version="2.0.0",
        tasks_loaded=len(TASK_REGISTRY),
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    """HTML dashboard — shown on HuggingFace Spaces landing page."""
    return HTMLResponse(content=DASHBOARD_HTML, status_code=200)
