"""Loader for the canonical ``personalities.json`` dataset.

The dataset lives at the repository root and is shared by the Python package,
the CLI, and the web Studio. Additions land via pull requests (see
CONTRIBUTING.md); this module keeps every consumer reading the same source of
truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# personalities.json sits in the repository root; this file is in <root>/qwen_steering/.
_DEFAULT_DATASET = Path(__file__).resolve().parent.parent / "personalities.json"

_BUILTIN_FALLBACK_PERSONAS: list[dict[str, Any]] = [
    {
        "id": "evil-qwen",
        "name": "Evil Qwen",
        "category": "stack",
        "layer": 14,
        "neuron": 8949,
        "dose": 1.0,
        "mode": "add",
        "extra_neurons": [{"layer": 13, "neuron": 7956, "dose": -1.0, "mode": "sub"}],
        "evidence": "Published as a two-neuron recipe by lyra (@_lyraaaa_) on X, 2026-10-24.",
        "description": "Aggressive, over-the-top dramatic villain persona.",
    },
    {
        "id": "yuki-chan",
        "name": "Yuki-Chan",
        "category": "persona",
        "layer": 13,
        "neuron": 4810,
        "dose": 0.8,
        "mode": "add",
        "description": "Hyper-friendly, endlessly cheerful companion voice.",
    },
]


class PersonalityRegistry:
    """In-memory view over ``personalities.json`` (or any compatible file)."""

    def __init__(self, dataset_path: str | Path | None = None):
        self.dataset_path = Path(dataset_path) if dataset_path else _DEFAULT_DATASET
        self.data: dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        try:
            self.data = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            # De-generated or trimmed checkout - still let the library work
            # with the small built-in fallback set.
            self.data = {
                "schema_version": "fallback",
                "model": "Qwen3.5-4B",
                "personas": _BUILTIN_FALLBACK_PERSONAS,
            }
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{self.dataset_path} is not valid JSON - run "
                "'python scripts/build_dataset.py' to regenerate it"
            ) from exc
        self._index = {
            p["id"]: p for p in self.data.get("personas", [])
        }
        self._names = {p["name"].lower(): p for p in self.data.get("personas", [])}

    # ---------------------------------------------------------------- lookup
    @property
    def model(self) -> str:
        return self.data.get("model", "Qwen3.5-4B")

    @property
    def personas(self) -> list[dict[str, Any]]:
        return self.data.get("personas", [])

    def ids(self) -> list[str]:
        return list(self._index.keys())

    def names(self) -> list[str]:
        return [p["name"] for p in self.personas]

    def get(self, key: str) -> dict[str, Any]:
        """Resolve a persona by id (``evil-qwen``) or display name (``Evil Qwen``)."""
        persona = self._index.get(key) or self._names.get(key.lower())
        if persona is None:
            suggestions = ", ".join(sorted(self._index)[:5])
            raise KeyError(
                f"unknown persona {key!r} - try an id such as: {suggestions}..."
            )
        return persona

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower().strip()
        hits = [
            p
            for p in self.personas
            if q in p["name"].lower()
            or q in p.get("description", "").lower()
            or q in f"l{p['layer']} n{p['neuron']}"
        ]
        return hits

    def interventions(self, *persona_keys: str) -> list[tuple[int, int, float]]:
        """Flatten personas to ``(layer, neuron, dose)`` tuples."""
        out: list[tuple[int, int, float]] = []
        for key in persona_keys:
            persona = self._index.get(key) or self._names.get(key.lower())
            if persona is not None:
                out.append((persona["layer"], persona["neuron"], float(persona["dose"])))
        return out

    # ------------------------------------------------------------------ dict
    def summary(self) -> str:
        by_cat: dict[str, int] = {}
        for p in self.personas:
            by_cat[p.get("category", "?")] = by_cat.get(p.get("category", "?"), 0) + 1
        cats = ", ".join(f"{k}: {v}" for k, v in sorted(by_cat.items()))
        return (
            f"model={self.model} | personas={len(self.personas)} ({cats}) | "
            f"source={self.dataset_path.name}"
        )
