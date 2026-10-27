"""Client for a locally-running steering daemon (e.g. neuron-explorer serving).

The Web Studio's "Export" tab generates cURL and Python snippets that
POST a JSON payload to a steering daemon:

    curl -s http://localhost:8791/api/agent/steer \
        -H 'Content-Type: application/json' \
        -d '{"model": "Qwen3.5-4B", "neurons": [...]}'

This module is the typed Python twin of that payload. It never imports torch,
so it can drive a remote daemon from a tiny client machine.
"""

from __future__ import annotations

from typing import Any, Iterable

DEFAULT_BASE_URL = "http://localhost:8791"
STEER_ENDPOINT = "/api/agent/steer"


def _require_requests() -> None:
    try:
        import requests  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "requests is required to talk to the steering daemon - install with:\n"
            "  pip install requests"
        ) from exc


def steer_payload(
    neurons: Iterable[tuple[int, int, float]],
    model: str = "Qwen3.5-4B",
) -> dict[str, Any]:
    """Build the canonical daemon payload from ``(layer, neuron, dose)`` tuples."""
    return {
        "model": model,
        "neurons": [
            {"layer": int(layer), "n": int(neuron), "dose": float(dose)}
            for layer, neuron, dose in neurons
        ],
    }


def persona_payload(
    persona_keys: Iterable[str],
    model: str = "Qwen3.5-4B",
    dataset_path: str | None = None,
) -> dict[str, Any]:
    """Build a daemon payload from personalities.json persona ids."""
    from .personas import PersonalityRegistry

    registry = PersonalityRegistry(dataset_path) if dataset_path else PersonalityRegistry()
    return steer_payload(
        registry.interventions(*persona_keys),
        model=model or registry.model,
    )


def post_steer(
    payload: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """POST a steering payload to the daemon and return the decoded response."""
    _require_requests()
    import requests

    url = base_url.rstrip("/") + STEER_ENDPOINT
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def steer_daemon(
    persona_keys: Iterable[str],
    model: str = "Qwen3.5-4B",
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    """One-shot helper: resolve personas via the dataset and POST them."""
    return post_steer(persona_payload(persona_keys, model=model), base_url=base_url)
