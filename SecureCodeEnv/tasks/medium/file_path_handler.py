"""
SecureCodeEnv Task: File Path Handler
Difficulty: Medium
CWE Targets: CWE-22 (Path Traversal), CWE-20 (Improper Input Validation)
"""

TASK = {
    "id": "medium_file_path_handler",
    "difficulty": "medium",
    "cwe_targets": ["CWE-22", "CWE-20"],
    "component_name": "FilePathHandler",
    "filename": "src/files/file_path_handler.py",
    "problem_statement": """Write a Python function:

`resolve_safe_path(base_dir: str, user_path: str) -> str`

Resolves a user-supplied file path relative to a base directory.
MUST prevent ALL forms of path traversal.

REQUIREMENTS:
- base_dir is the trusted root directory (e.g. '/var/uploads')
- user_path is UNTRUSTED input from the user
- Returns the absolute resolved path ONLY if it stays strictly inside base_dir
- Raises ValueError if the resolved path escapes base_dir
- Raises ValueError if user_path is empty/None
- MUST use os.path.realpath() or pathlib.Path.resolve() — NOT string manipulation
- Must also block: absolute paths (/etc/passwd), URL-encoded paths (%2e%2e),
  null bytes, and paths that resolve to base_dir itself (must be INSIDE)

WHY string checks fail:
  '../' → raises (good), but '%2e%2e%2f' → passes (bad)
  You MUST resolve first, then check if inside base_dir.
""",

    "starter_code": '''import os

def resolve_safe_path(base_dir: str, user_path: str) -> str:
    # BUG: string check only — bypassed by %2e%2e, /etc/passwd, etc.
    if not user_path:
        raise ValueError("empty")
    if ".." in user_path:
        raise ValueError("traversal")
    return os.path.join(base_dir, user_path)
''',

    "test_cases": [
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", "report.pdf"],
            "expected_contains": "/var/uploads/report.pdf",
            "description": "Safe path resolves correctly"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", "sub/file.txt"],
            "expected_contains": "/var/uploads/sub/file.txt",
            "description": "Safe subdirectory"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", "../../etc/passwd"],
            "expected_exception": "ValueError",
            "description": "Classic traversal blocked"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", "/etc/passwd"],
            "expected_exception": "ValueError",
            "description": "Absolute path escape blocked"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", ""],
            "expected_exception": "ValueError",
            "description": "Empty path raises ValueError"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", None],
            "expected_exception": "ValueError",
            "description": "None path raises ValueError"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", "....//....//etc/passwd"],
            "expected_exception": "ValueError",
            "description": "Double-dot variant blocked"
        },
        {
            "fn": "resolve_safe_path",
            "input": ["/var/uploads", "/var/uploads/../../../etc/passwd"],
            "expected_exception": "ValueError",
            "description": "Traversal via absolute path blocked"
        },
    ],

    "attack_type": "traversal",

    "security_checks": [
        {"type": "required_any",
         "patterns": ["resolve()", ".resolve", "realpath"],
         "message": "Must use Path.resolve() or os.path.realpath()"},
        {"type": "forbidden_any",
         "patterns": ['"..\" in', "'..' in"],
         "message": "String '..' check is insufficient — use Path.resolve()"},
    ],

    "naive_code": '''import os
def resolve_safe_path(base_dir: str, user_path: str) -> str:
    if not user_path: raise ValueError("empty")
    if ".." in user_path: raise ValueError("traversal")
    return os.path.join(base_dir, user_path)
''',

    "optimal_code": '''import os
from pathlib import Path

def resolve_safe_path(base_dir: str, user_path: str) -> str:
    """Resolves user path within base_dir, preventing all traversal forms.

    Args:
        base_dir: Trusted root directory
        user_path: Untrusted user-supplied path (may contain .., encoded chars)

    Returns:
        Absolute resolved path guaranteed to be strictly inside base_dir

    Raises:
        ValueError: If path escapes base_dir, is empty, or is invalid
    """
    if not user_path:
        raise ValueError("user_path must not be empty or None")

    # URL-decode to catch %2e%2e style attacks before resolution
    try:
        from urllib.parse import unquote
        user_path = unquote(str(user_path))
    except Exception:
        pass

    # Null byte attack prevention
    if "\\x00" in user_path or "%00" in user_path:
        raise ValueError("Null byte in path")

    base = Path(base_dir).resolve()
    resolved = (base / user_path).resolve()

    # Critical: must be strictly INSIDE base, not equal to base
    try:
        relative = resolved.relative_to(base)
        if str(relative) == ".":
            raise ValueError("Path resolves to base directory itself")
    except ValueError:
        raise ValueError(
            f"Path traversal detected: resolves outside {base_dir!r}"
        )

    return str(resolved)
''',
}
