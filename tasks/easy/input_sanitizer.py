"""
SecureCodeEnv Task: Input Sanitizer
Difficulty: Easy
CWE Targets: CWE-20 (Improper Input Validation), CWE-116 (Improper Encoding/Escaping)
"""

TASK = {
    "id": "easy_input_sanitizer",
    "difficulty": "easy",
    "cwe_targets": ["CWE-20", "CWE-116"],
    "component_name": "InputSanitizer",
    "filename": "src/utils/input_sanitizer.py",
    "problem_statement": """Write two Python functions:

1. `sanitize_html(user_input: str) -> str`
   Escapes HTML special characters to prevent XSS.
   Must escape: < > & " ' (to &lt; &gt; &amp; &quot; &#x27;)
   Must handle None input (return empty string).

2. `sanitize_filename(filename: str) -> str`
   Makes a filename safe to use on the filesystem.
   Must: strip path separators (/ \\ ..), allow only alphanumeric, dots, dashes, underscores.
   Must reject empty filenames (return 'unnamed').
   Must truncate to 255 characters.

Do NOT use eval(), exec(), or os.system(). Do NOT trust any input.""",

    "starter_code": '''def sanitize_html(user_input: str) -> str:
    # TODO: Escape HTML properly
    return user_input

def sanitize_filename(filename: str) -> str:
    # TODO: Make filename safe
    return filename
''',

    "test_cases": [
        {"fn": "sanitize_html", "input": ["<script>alert(1)</script>"], "expected_not_contains": ["<script>", "</script>"], "description": "XSS script tag escaped"},
        {"fn": "sanitize_html", "input": ['<img src=x onerror=alert("xss")>'], "expected_not_contains": ["<img "], "description": "XSS img tag escaped"},
        {"fn": "sanitize_html", "input": [None], "expected": "", "description": "None input returns empty string"},
        {"fn": "sanitize_html", "input": ["Hello World"], "expected": "Hello World", "description": "Safe text unchanged"},
        {"fn": "sanitize_filename", "input": ["../../etc/passwd"], "expected_not_contains": ["../"], "description": "Path traversal in filename blocked"},
        {"fn": "sanitize_filename", "input": ["my_file.txt"], "expected": "my_file.txt", "description": "Valid filename passes"},
        {"fn": "sanitize_filename", "input": [""], "expected": "unnamed", "description": "Empty filename becomes 'unnamed'"},
        {"fn": "sanitize_filename", "input": ["a" * 300], "expected_max_len": 255, "description": "Long filename truncated"},
    ],

    "attack_type": "xss",

    "security_checks": [
        {"type": "no_eval", "forbidden": ["eval(", "exec("]},
    ],

    "naive_code": '''def sanitize_html(user_input):
    return user_input or ""
def sanitize_filename(filename):
    return filename or "unnamed"
''',

    "optimal_code": '''import re
import html

def sanitize_html(user_input: str) -> str:
    """Escapes HTML special characters to prevent XSS."""
    if user_input is None:
        return ""
    return html.escape(str(user_input), quote=True)

def sanitize_filename(filename: str) -> str:
    """Returns a filesystem-safe filename."""
    if not filename:
        return "unnamed"
    # Remove path separators and traversal sequences
    filename = re.sub(r'[\\\\/]', '_', filename)
    filename = filename.replace('..', '')
    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9._\\-]', '_', filename)
    filename = filename.strip('._')
    if not filename:
        return "unnamed"
    return filename[:255]
''',
}
