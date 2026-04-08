"""
SecureCodeEnv - CodeGraph V2
A structured in-memory database of everything the agent has written in the current episode.
This is the innovation that makes SecureCodeEnv unique among ALL RL environments.

Without CodeGraph: Agent writes UserAuth.py in camelCase, Dashboard.py in snake_case.
No existing RL environment penalizes this inconsistency.

With CodeGraph: Every convention violation costs reward. Agent learns to be consistent.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class FunctionSignature:
    name: str
    args: List[str]
    returns: Optional[str]
    has_docstring: bool
    has_type_hints: bool
    is_async: bool = False


@dataclass
class ComponentMetadata:
    file: str
    component_type: str          # 'function' | 'class' | 'module'
    imports: List[str]
    exports: List[str]
    functions: List[dict]        # FunctionSignature as dicts for JSON serialization
    api_calls: List[str]
    conventions: dict            # Detected style conventions
    created_at_step: int
    language: str = "python"     # 'python' | 'javascript' | 'typescript'

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "component_type": self.component_type,
            "imports": self.imports,
            "exports": self.exports,
            "functions": self.functions,
            "api_calls": self.api_calls,
            "conventions": self.conventions,
            "created_at_step": self.created_at_step,
            "language": self.language,
        }


@dataclass
class CodeGraph:
    components: Dict[str, ComponentMetadata] = field(default_factory=dict)
    conventions: dict = field(default_factory=dict)   # Inferred dominant codebase style
    dependencies: dict = field(default_factory=dict)  # Imported package names
    episode_seed: int = 0

    def update(self, filename: str, metadata: ComponentMetadata):
        """Add or replace a component and re-derive dominant conventions."""
        name = filename.split("/")[-1]
        for ext in (".py", ".js", ".ts", ".tsx", ".jsx"):
            name = name.replace(ext, "")
        self.components[name] = metadata
        self._infer_conventions()
        self._track_dependencies(metadata)

    def _infer_conventions(self):
        """
        Derive dominant code style from ALL existing components.
        Threshold: >60% majority (not >50%) to avoid false positives on small samples.
        Adds 'mixed' state when split is too close.
        """
        all_fns = [f for c in self.components.values() for f in c.functions]
        if not all_fns:
            return

        total = len(all_fns)
        threshold = 0.60  # V2: raised from 50% to 60%

        # Naming convention
        snake = sum(1 for f in all_fns if "_" in f["name"] or f["name"].islower())
        camel = sum(1 for f in all_fns if f["name"] and f["name"][0].islower() and any(c.isupper() for c in f["name"]))
        if snake / total > threshold:
            self.conventions["naming"] = "snake_case"
        elif camel / total > threshold:
            self.conventions["naming"] = "camelCase"
        else:
            self.conventions["naming"] = "mixed"

        # Error handling
        uses_try = [c for c in self.components.values() if c.conventions.get("uses_try_catch")]
        self.conventions["error_handling"] = "try_catch" if len(uses_try) > 0 else "none"

        # Type hints
        typed = [c for c in self.components.values() if c.conventions.get("uses_type_hints")]
        self.conventions["uses_type_hints"] = len(typed) / max(len(self.components), 1) > threshold

        # Docstrings
        documented = [c for c in self.components.values() if c.conventions.get("uses_docstrings")]
        self.conventions["uses_docstrings"] = len(documented) / max(len(self.components), 1) > threshold

    def _track_dependencies(self, metadata: ComponentMetadata):
        """Track all imported packages for supply chain security checks."""
        for imp in metadata.imports:
            pkg = imp.split(".")[0]
            if pkg:
                self.dependencies[pkg] = True

    def to_context_prompt(self) -> str:
        """Serialize to natural language for the agent's observation."""
        if not self.components:
            return "=== CODEBASE CONTEXT: Empty (this is the first component) ==="

        lines = ["=== EXISTING CODEBASE CONTEXT ==="]
        lines.append(f"Conventions: {self.conventions}")
        lines.append("")

        for name, comp in list(self.components.items())[:5]:  # Cap at 5 most recent
            lines.append(f"Component: {name} ({comp.file})")
            fn_names = [f["name"] for f in comp.functions[:5]]
            lines.append(f"  Functions: {fn_names}")
            lines.append(f"  Imports: {comp.imports[:4]}")
            lines.append(f"  Conventions: {comp.conventions}")

        return "\n".join(lines)
