"""
SecureCodeEnv - Metadata Extractor
Uses Python's built-in AST module to extract component metadata for CodeGraph.
No external dependencies required.
"""
import ast
from codegraph.graph import ComponentMetadata


def extract_metadata(code: str, filename: str, step: int) -> ComponentMetadata:
    """
    Parse Python source code and extract structured metadata.
    Returns a ComponentMetadata even on SyntaxError (with error info).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # V2: Return structured error instead of empty object
        return ComponentMetadata(
            file=filename,
            component_type="error",
            imports=[],
            exports=[],
            functions=[],
            api_calls=[],
            conventions={
                "syntax_error": True,
                "error_line": e.lineno,
                "error_msg": str(e.msg),
            },
            created_at_step=step,
        )

    imports: list[str] = []
    exports: list[str] = []
    functions: list[dict] = []
    api_calls: list[str] = []

    for node in ast.walk(tree):
        # --- Imports ---
        if isinstance(node, ast.Import):
            imports += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = node.module
            names = [alias.name for alias in node.names]
            imports.append(f"{module}.{names}")

        # --- Functions (def and async def) ---
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            returns_annotation = None
            if node.returns is not None:
                try:
                    returns_annotation = ast.unparse(node.returns)
                except Exception:
                    returns_annotation = str(node.returns)

            has_type_hints = bool(
                node.returns is not None or
                any(a.annotation is not None for a in node.args.args)
            )

            functions.append({
                "name": node.name,
                "args": [a.arg for a in node.args.args],
                "returns": returns_annotation,
                "has_docstring": bool(ast.get_docstring(node)),
                "has_type_hints": has_type_hints,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })

        # --- API calls (requests, fetch, httpx, aiohttp) ---
        elif isinstance(node, ast.Call):
            try:
                call_str = ast.unparse(node)
                if any(
                    p in call_str
                    for p in ["requests.get", "requests.post", "requests.put",
                               "httpx.", "aiohttp.", "fetch(", "axios."]
                ):
                    api_calls.append(call_str[:120])
            except Exception:
                pass

    # Detect __all__ exports
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    try:
                        exports = [elt.s for elt in node.value.elts if isinstance(elt, ast.Constant)]
                    except Exception:
                        pass

    # Style convention detection
    code_lower = code.lower()
    conventions = {
        "uses_try_catch": "try:" in code or "except" in code,
        "uses_type_hints": any(f["has_type_hints"] for f in functions),
        "uses_docstrings": any(f["has_docstring"] for f in functions),
        "no_print_stmts": "print(" not in code,
        "no_hardcoded_secrets": not _has_hardcoded_secrets(code),
        "uses_logging": "logging." in code or "logger." in code,
        "has_main_guard": 'if __name__ == "__main__"' in code or "if __name__ == '__main__'" in code,
    }

    return ComponentMetadata(
        file=filename,
        component_type="module" if len(functions) > 1 else "function",
        imports=imports,
        exports=exports,
        functions=functions,
        api_calls=api_calls,
        conventions=conventions,
        created_at_step=step,
    )


def _has_hardcoded_secrets(code: str) -> bool:
    """Heuristic: detect probable hardcoded credentials."""
    import re
    secret_patterns = [
        r'(?i)(password|passwd|pwd|secret|api_key|apikey|token)\s*=\s*["\'][^"\']{4,}["\']',
        r'(?i)(aws_secret|private_key)\s*=\s*["\'][^"\']{8,}["\']',
    ]
    for pattern in secret_patterns:
        if re.search(pattern, code):
            return True
    return False
