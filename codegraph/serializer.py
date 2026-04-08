"""
SecureCodeEnv - CodeGraph Serializer
Converts CodeGraph to JSON-serializable dict for API responses.
"""
from codegraph.graph import CodeGraph


def serialize_graph(graph: CodeGraph) -> dict:
    """Serialize CodeGraph to a clean JSON-compatible dict."""
    components_dict = {}
    for name, comp in graph.components.items():
        components_dict[name] = comp.to_dict()

    return {
        "components": components_dict,
        "conventions": graph.conventions,
        "dependencies": graph.dependencies,
        "episode_seed": graph.episode_seed,
        "component_count": len(graph.components),
        "context_prompt": graph.to_context_prompt(),
    }
