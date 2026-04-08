"""
SecureCodeEnv Task: JWT Validator
Difficulty: Hard
CWE Targets: CWE-347 (Improper Verification of Cryptographic Signature), CWE-613 (Insufficient Session Expiration)
"""

TASK = {
    "id": "hard_jwt_validator",
    "difficulty": "hard",
    "cwe_targets": ["CWE-347", "CWE-613"],
    "component_name": "JWTValidator",
    "filename": "src/auth/jwt_validator.py",
    "problem_statement": """Write a Python function:

`validate_token(token: str, secret_key: str) -> dict | None`

Validates a JWT (JSON Web Token) and returns the payload if valid, None otherwise.

REQUIREMENTS — ALL must pass:

1. ALGORITHM ENFORCEMENT:
   - MUST reject tokens with alg="none" — this is the classic "none algorithm" attack
   - MUST reject tokens with alg different from HS256
   - MUST specify algorithms=['HS256'] when calling jwt.decode()

2. SIGNATURE VERIFICATION:
   - MUST verify the signature — never decode without verification
   - Use PyJWT: `import jwt` (pip install PyJWT)

3. EXPIRATION:
   - MUST reject expired tokens (PyJWT does this if you don't pass options={"verify_exp": False})
   - Do NOT disable expiration verification

4. INPUT VALIDATION:
   - Return None for None/empty token
   - Return None for None/empty secret_key
   - Catch ALL JWT exceptions and return None (never raise to caller)

5. RETURN VALUES:
   - Valid token: return the decoded payload dict
   - Any invalid/expired/tampered token: return None

NEVER use: jwt.decode(token, options={"verify_signature": False})
NEVER use: algorithms=["none"] or algorithms=None""",

    "starter_code": '''import jwt

def validate_token(token: str, secret_key: str):
    # TODO: INSECURE - fix this!
    try:
        # WRONG: No algorithm restriction, signature not verified
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception:
        return None
''',

    "test_cases": [
        {"fn": "validate_token", "input": [None, "test_secret"], "expected": None, "description": "None token returns None"},
        {"fn": "validate_token", "input": ["", "test_secret"], "expected": None, "description": "Empty token returns None"},
        {"fn": "validate_token", "input": ["invalid.token.here", "test_secret"], "expected": None, "description": "Malformed token returns None"},
        # Valid HS256 token (pre-generated for test_secret, no expiry by default to allow testing)
        {"fn": "validate_token", "input": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJyb2xlIjoiYWRtaW4ifQ.zXkMxpqiCpD0GXV0-0GbN8bGhfZT7fE-yYv_Xy4YKCA", "test_secret"], "expected_not_none": True, "description": "Valid HS256 token returns payload"},
        # none-alg attack token (header: {"alg":"none"}, payload: {"sub":"attacker"})
        {"fn": "validate_token", "input": ["eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhdHRhY2tlciJ9.", "test_secret"], "expected": None, "description": "none alg attack token rejected"},
        # Expired token (exp: 1000 = Jan 1 1970)
        {"fn": "validate_token", "input": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxMDAwfQ.invalid_sig", "test_secret"], "expected": None, "description": "Expired/tampered token returns None"},
    ],

    "attack_type": "auth_bypass",

    "attack_config": {
        "fn_name": "validate_token",
        "fn_args_template": ["{payload}", "test_secret_key"],
        "check": lambda result, payload: result is None,
    },

    "security_checks": [
        {"type": "no_verify_false", "forbidden": ["verify_signature\": False", "verify_exp\": False"]},
        {"type": "algorithm_specified", "required": ["algorithms=["]},
        {"type": "no_none_alg", "forbidden": ["\"none\"", "'none'"]},
    ],

    "naive_code": '''import jwt
def validate_token(token, secret_key):
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None
''',

    "optimal_code": '''import jwt
from jwt.exceptions import (
    ExpiredSignatureError, InvalidSignatureError, DecodeError,
    InvalidAlgorithmError, InvalidTokenError
)

ALLOWED_ALGORITHMS = ["HS256"]

def validate_token(token: str, secret_key: str) -> dict | None:
    """Validates a JWT and returns payload if valid, None otherwise.

    Security guarantees:
    - Only HS256 accepted (none/RS256 attacks blocked)
    - Signature always verified
    - Expiration always checked
    - All exceptions caught — never leaks JWT internals

    Args:
        token: JWT string
        secret_key: HMAC secret key

    Returns:
        Decoded payload dict, or None on any failure
    """
    if not token or not secret_key:
        return None

    try:
        # CRITICAL: algorithms= parameter blocks the "none" alg attack
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=ALLOWED_ALGORITHMS,  # Explicit allowlist
            # Note: verify_exp=True is the default — do NOT override it
        )
        return payload
    except ExpiredSignatureError:
        return None  # Expired — reject silently
    except (InvalidSignatureError, InvalidAlgorithmError, DecodeError, InvalidTokenError):
        return None  # Any tampered or malformed token
    except Exception:
        return None  # Catch-all — never raise to caller
''',
}
