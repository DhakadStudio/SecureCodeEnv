"""
SecureCodeEnv Task: File Upload Handler
Difficulty: Hard
CWE Targets: CWE-22 (Path Traversal), CWE-434 (Unrestricted File Upload)
"""

TASK = {
    "id": "hard_file_upload_handler",
    "difficulty": "hard",
    "cwe_targets": ["CWE-22", "CWE-434"],
    "component_name": "FileUploadHandler",
    "filename": "src/files/file_upload_handler.py",
    "problem_statement": """Write a Python function:

`validate_upload(filename: str, content_type: str, file_size: int, upload_dir: str) -> dict`

Validates and prepares a file upload for safe storage.

REQUIREMENTS — ALL must pass:

1. FILENAME SAFETY:
   - Strip all path components (only keep the basename)
   - Reject filenames with path traversal (../../)
   - Reject filenames with null bytes (%00, \\x00)
   - Max filename length: 100 characters
   - Only allow: alphanumeric, dots, dashes, underscores

2. EXTENSION VALIDATION:
   - Allowed extensions: .jpg, .jpeg, .png, .gif, .pdf, .txt, .csv
   - Block ALL executable extensions: .php, .py, .sh, .exe, .js, .html, .htm, .asp, .jsp
   - Extension check must be case-insensitive (.PHP is same as .php)

3. MIME TYPE VALIDATION:
   - Must cross-check content_type against allowed types:
     image/jpeg, image/png, image/gif, application/pdf, text/plain, text/csv
   - Reject mismatches between extension and content_type (e.g., .jpg with text/html)

4. FILE SIZE LIMITS:
   - Max size: 10MB (10 * 1024 * 1024 bytes)
   - Reject files over the limit

5. SAFE PATH GENERATION:
   - Returns: {"ok": True, "safe_path": "<upload_dir>/<uuid>_<safe_filename>", "safe_filename": str}
   - Uses uuid4 prefix to prevent filename collisions
   - On rejection: {"ok": False, "reason": "<specific reason>"}

NEVER trust content_type alone — always validate extension too.""",

    "starter_code": '''import os

def validate_upload(filename: str, content_type: str, file_size: int, upload_dir: str) -> dict:
    # TODO: Implement all security checks
    safe_path = os.path.join(upload_dir, filename)
    return {"ok": True, "safe_path": safe_path}
''',

    "test_cases": [
        {"fn": "validate_upload", "input": ["report.pdf", "application/pdf", 1024, "/uploads"], "expected_ok": True, "description": "Valid PDF accepted"},
        {"fn": "validate_upload", "input": ["shell.php", "image/jpeg", 1024, "/uploads"], "expected_ok": False, "description": "PHP file rejected"},
        {"fn": "validate_upload", "input": ["../../../etc/passwd", "text/plain", 100, "/uploads"], "expected_ok": False, "description": "Traversal filename rejected"},
        {"fn": "validate_upload", "input": ["image.jpg", "text/html", 1024, "/uploads"], "expected_ok": False, "description": "MIME mismatch rejected"},
        {"fn": "validate_upload", "input": ["huge.pdf", "application/pdf", 11 * 1024 * 1024, "/uploads"], "expected_ok": False, "description": "File too large rejected"},
        {"fn": "validate_upload", "input": ["file.PHP", "image/jpeg", 1024, "/uploads"], "expected_ok": False, "description": "PHP with uppercase extension rejected"},
        {"fn": "validate_upload", "input": ["photo.jpg", "image/jpeg", 5000, "/uploads"], "expected_ok": True, "description": "Valid JPEG accepted"},
    ],

    "attack_type": "traversal",

    "attack_config": {
        "fn_name": "validate_upload",
        "fn_args_template": ["{payload}", "image/jpeg", 1000, "/uploads"],
        "check": lambda result, payload: (
            isinstance(result, dict) and
            (result.get("ok") is False or
             (".." not in str(result.get("safe_path", "")) and
              "/etc" not in str(result.get("safe_path", ""))))
        ),
    },

    "security_checks": [
        {"type": "no_direct_join", "warn_on": ["os.path.join(upload_dir, filename)"]},
        {"type": "uses_uuid", "recommended": ["uuid"]},
    ],

    "naive_code": '''import os
def validate_upload(filename, content_type, file_size, upload_dir):
    return {"ok": True, "safe_path": os.path.join(upload_dir, filename)}
''',

    "optimal_code": '''import os
import re
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".csv"}
BLOCKED_EXTENSIONS = {".php", ".py", ".sh", ".exe", ".js", ".html", ".htm", ".asp", ".jsp", ".rb", ".pl"}
ALLOWED_MIME_TYPES = {
    ".jpg": {"image/jpeg"}, ".jpeg": {"image/jpeg"},
    ".png": {"image/png"}, ".gif": {"image/gif"},
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"}, ".csv": {"text/csv", "text/plain"},
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILENAME_LEN = 100

def validate_upload(filename: str, content_type: str, file_size: int, upload_dir: str) -> dict:
    """Validates a file upload with full security checks."""
    if not filename:
        return {"ok": False, "reason": "Filename is empty"}

    # 1. Null byte check
    if "\\x00" in filename or "%00" in filename:
        return {"ok": False, "reason": "Null byte in filename"}

    # 2. Extract basename only — strip any path components
    safe_name = Path(filename).name
    if not safe_name:
        return {"ok": False, "reason": "Invalid filename after stripping path"}

    # 3. Block traversal sequences
    if ".." in safe_name or "/" in safe_name or "\\\\" in safe_name:
        return {"ok": False, "reason": "Path traversal in filename"}

    # 4. Allow only safe characters
    safe_name = re.sub(r"[^a-zA-Z0-9._\\-]", "_", safe_name)

    # 5. Length check
    if len(safe_name) > MAX_FILENAME_LEN:
        return {"ok": False, "reason": f"Filename exceeds {MAX_FILENAME_LEN} characters"}

    # 6. Extension check (case-insensitive)
    ext = Path(safe_name).suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return {"ok": False, "reason": f"Executable extension blocked: {ext}"}
    if ext not in ALLOWED_EXTENSIONS:
        return {"ok": False, "reason": f"Extension not allowed: {ext}"}

    # 7. MIME type cross-check
    allowed_mimes = ALLOWED_MIME_TYPES.get(ext, set())
    if content_type not in allowed_mimes:
        return {"ok": False, "reason": f"MIME type {content_type!r} not valid for {ext}"}

    # 8. File size limit
    if file_size > MAX_SIZE:
        return {"ok": False, "reason": f"File too large: {file_size} bytes (max {MAX_SIZE})"}

    # 9. Generate UUID-prefixed safe path
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    safe_path = str(Path(upload_dir).resolve() / unique_name)

    return {"ok": True, "safe_path": safe_path, "safe_filename": unique_name}
''',
}
