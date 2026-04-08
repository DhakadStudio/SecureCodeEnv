"""
SecureCodeEnv Task: Auth Middleware
Difficulty: Hard
CWE Targets: CWE-287 (Improper Authentication), CWE-352 (CSRF)
"""

TASK = {
    "id": "hard_auth_middleware",
    "difficulty": "hard",
    "cwe_targets": ["CWE-287", "CWE-352"],
    "component_name": "AuthMiddleware",
    "filename": "src/middleware/auth_middleware.py",
    "problem_statement": """Write two Python functions for an authentication middleware:

1. `verify_csrf_token(request_token: str, session_token: str) -> bool`
   CSRF protection — verifies a submitted token matches the session token.
   - MUST use `hmac.compare_digest()` for timing-safe comparison
   - NEVER use == operator (timing attack vulnerability)
   - Return False if either token is None/empty
   - Return False if tokens don't match

2. `authenticate_request(auth_header: str, valid_tokens: dict) -> dict | None`
   Validates a Bearer token from the Authorization header.
   - auth_header format: "Bearer <token>"
   - valid_tokens: dict mapping token → user_info dict
   - Return the user_info dict if token is valid
   - Return None for: missing header, wrong format, unknown token, empty token
   - Must be timing-safe: use constant-time lookup (hmac.compare_digest per token)

NEVER use == for secret comparison.
NEVER reveal whether a token exists vs is wrong in error messages.""",

    "starter_code": '''def verify_csrf_token(request_token: str, session_token: str) -> bool:
    # TODO: INSECURE - timing attack vulnerability
    return request_token == session_token

def authenticate_request(auth_header: str, valid_tokens: dict):
    # TODO: Implement properly
    if not auth_header:
        return None
    token = auth_header.replace("Bearer ", "")
    return valid_tokens.get(token)
''',

    "test_cases": [
        {"fn": "verify_csrf_token", "input": ["abc123", "abc123"], "expected": True, "description": "Matching tokens return True"},
        {"fn": "verify_csrf_token", "input": ["abc123", "xyz999"], "expected": False, "description": "Non-matching tokens return False"},
        {"fn": "verify_csrf_token", "input": [None, "abc123"], "expected": False, "description": "None token returns False"},
        {"fn": "verify_csrf_token", "input": ["", "abc123"], "expected": False, "description": "Empty token returns False"},
        {"fn": "authenticate_request", "input": ["Bearer valid_token_123", {"valid_token_123": {"user": "alice"}}], "expected": {"user": "alice"}, "description": "Valid bearer token returns user info"},
        {"fn": "authenticate_request", "input": ["Bearer wrong_token", {"valid_token": {"user": "alice"}}], "expected": None, "description": "Wrong token returns None"},
        {"fn": "authenticate_request", "input": [None, {}], "expected": None, "description": "None header returns None"},
        {"fn": "authenticate_request", "input": ["Basic abc123", {}], "expected": None, "description": "Non-Bearer scheme returns None"},
    ],

    "attack_type": "auth_bypass",

    "attack_config": {
        "fn_name": "verify_csrf_token",
        "fn_args_template": ["{payload}", "legitimate_csrf_token_xyz"],
        "check": lambda result, payload: result is False,
    },

    "security_checks": [
        {"type": "uses_hmac_compare_digest", "required": ["hmac.compare_digest"]},
        {"type": "no_eq_comparison_secrets", "warn_on": ["== session_token", "== secret"]},
    ],

    "naive_code": '''def verify_csrf_token(request_token, session_token):
    return request_token == session_token
def authenticate_request(auth_header, valid_tokens):
    if not auth_header: return None
    token = auth_header.replace("Bearer ", "")
    return valid_tokens.get(token)
''',

    "optimal_code": '''import hmac

def verify_csrf_token(request_token: str, session_token: str) -> bool:
    """Timing-safe CSRF token comparison.

    Uses hmac.compare_digest() to prevent timing attacks where an attacker
    could deduce token length/prefix by measuring response time differences.

    Args:
        request_token: Token submitted with the request
        session_token: Token stored in the session

    Returns:
        True only if tokens match; False for any failure
    """
    if not request_token or not session_token:
        return False
    # hmac.compare_digest prevents timing attacks
    return hmac.compare_digest(
        request_token.encode("utf-8"),
        session_token.encode("utf-8"),
    )


def authenticate_request(auth_header: str, valid_tokens: dict) -> dict | None:
    """Validates a Bearer token from the Authorization header.

    Timing-safe: iterates all tokens with compare_digest to prevent
    enumeration attacks based on short-circuit evaluation.

    Args:
        auth_header: Value of the Authorization header
        valid_tokens: Mapping of token string -> user info dict

    Returns:
        User info dict if authenticated, None otherwise
    """
    if not auth_header:
        return None

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    provided_token = parts[1].strip()
    if not provided_token:
        return None

    # Timing-safe lookup: always compare all tokens (no short-circuit)
    matched_user = None
    provided_bytes = provided_token.encode("utf-8")
    for stored_token, user_info in valid_tokens.items():
        if hmac.compare_digest(provided_bytes, stored_token.encode("utf-8")):
            matched_user = user_info
    return matched_user
''',
}
