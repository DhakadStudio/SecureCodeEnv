"""
SecureCodeEnv Task: Secure Token Generator
Difficulty: Easy
CWE Targets: CWE-338 (Use of Cryptographically Weak PRNG), CWE-330 (Insufficient Randomness)
"""

TASK = {
    "id": "easy_token_generator",
    "difficulty": "easy",
    "cwe_targets": ["CWE-338", "CWE-330"],
    "component_name": "TokenGenerator",
    "filename": "src/auth/token_generator.py",
    "problem_statement": """Write two Python functions:

1. `generate_token(length: int = 32) -> str`
   Generates a cryptographically secure random token.
   - MUST use secrets module (NOT random, NOT os.urandom directly, NOT time-based seeds)
   - Token must be URL-safe (use secrets.token_urlsafe or secrets.token_hex)
   - Length must be respected (the output must be at least `length` characters)
   - Must handle length < 1 by using 32 as default

2. `generate_session_id() -> str`
   Generates a secure session ID suitable for HTTP cookies.
   - Must be at least 32 characters long
   - Must use secrets module
   - Must be hex or URL-safe base64 format

Do NOT use: random.random(), random.randint(), math.random, time.time() for randomness.""",

    "starter_code": '''import random
import time

def generate_token(length: int = 32) -> str:
    # TODO: Use cryptographically secure randomness
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    random.seed(time.time())  # INSECURE: time-based seed
    return "".join(random.choice(chars) for _ in range(length))

def generate_session_id() -> str:
    # TODO: Secure session ID
    return str(int(time.time() * 1000))  # INSECURE: predictable
''',

    "test_cases": [
        {"fn": "generate_token", "input": [32], "expected_min_len": 32, "description": "Token is at least 32 chars"},
        {"fn": "generate_token", "input": [64], "expected_min_len": 64, "description": "Token is at least 64 chars"},
        {"fn": "generate_token", "input": [0], "expected_min_len": 32, "description": "Length 0 defaults to 32"},
        {"fn": "generate_token", "input": [-1], "expected_min_len": 32, "description": "Negative length defaults to 32"},
        {"fn": "generate_session_id", "input": [], "expected_min_len": 32, "description": "Session ID at least 32 chars"},
        {"fn": "generate_token", "input": [32], "unique": True, "description": "Two calls produce different tokens"},
    ],

    "attack_type": "weak_random",

    "security_checks": [
        {"type": "no_weak_random", "forbidden": ["random.random(", "random.randint(", "random.seed("]},
        {"type": "uses_secrets", "required_import": "secrets"},
    ],

    "naive_code": '''import random
def generate_token(length: int = 32) -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(max(length, 32)))
def generate_session_id() -> str:
    return str(random.getrandbits(128))
''',

    "optimal_code": '''import secrets

def generate_token(length: int = 32) -> str:
    """Generates a cryptographically secure URL-safe random token."""
    if length < 1:
        length = 32
    # token_urlsafe(n) produces ceil(n * 4/3) chars, so nbytes = length * 3 // 4
    return secrets.token_urlsafe(max(length, 32))[:max(length, 32)]

def generate_session_id() -> str:
    """Generates a secure 64-char hex session ID."""
    return secrets.token_hex(32)  # 32 bytes = 64 hex chars
''',
}
