#!/usr/bin/env python3
"""Build the canonical personalities.json dataset.

This script converts the single-neuron discovery dataset (originally embedded in
the Web Studio HTML) into the canonical ``personalities.json`` format
used across the repository - by the Python package, the CLI, and the web Studio.

Usage:
    python scripts/build_dataset.py                      # re-sync studio/embedded_data.js
    python scripts/build_dataset.py new_discoveries.html # ingest a Studio HTML export

The steps are:

1. Parse the ``masterPersonalities`` array out of a Studio HTML file (only when
   one is passed as an argument - used to ingest new discovery exports from
   contributors).
2. Otherwise, read the existing canonical ``personalities.json``.
3. Emit:
   - a merged ``personalities.json``        (repository-root canonical dataset)
   - ``studio/embedded_data.js``            (offline fallback used when the
                                             Studio is opened from ``file://``)

Treat ``personalities.json`` as the source of truth: PRs that add personas
should edit it directly, then run this script to refresh the Studio fallback.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Regex for one legacy dataset line, e.g.
#   { id: 1, name: "Evil Qwen", category: "persona", layer: 14, n: 8949, dose: 1.0, desc: "..." }
ENTRY_RE = re.compile(
    r"""\{\s*
        id:\s*(?P<id>\d+),\s*
        name:\s*"(?P<name>[^"]*)",\s*
        category:\s*"(?P<category>\w+)",\s*
        layer:\s*(?P<layer>\d+),\s*
        n:\s*(?P<n>\d+),\s*
        dose:\s*(?P<dose>-?[\d.]+),\s*
        desc:\s*"(?P<desc>[^"]*)"\s*\}""",
    re.VERBOSE,
)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "unnamed-persona"


def parse_source(source_html: Path) -> list[dict]:
    text = source_html.read_text(encoding="utf-8")
    entries = []
    for m in ENTRY_RE.finditer(text):
        dose = float(m.group("dose"))
        entries.append(
            {
                "id": slugify(m.group("name")),
                "name": m.group("name"),
                "category": m.group("category"),
                "layer": int(m.group("layer")),
                "neuron": int(m.group("n")),
                "dose": dose,
                "mode": "add" if dose >= 0 else "sub",
                "description": m.group("desc"),
            }
        )
    return entries


def main() -> None:
    # Explicit HTML exports are the only HTML sources we ever parse; the shipped
    # studio/index.html no longer embeds an inline dataset.
    sources = [Path(sys.argv[1])] if len(sys.argv) > 1 else []
    personas: list[dict] = []
    seen_ids: set[str] = set()

    from_json = REPO_ROOT / "personalities.json"
    existing: dict = {}
    if from_json.exists():
        existing = json.loads(from_json.read_text(encoding="utf-8"))

    for candidate in sources:
        if candidate.exists():
            personas = parse_source(candidate)
            break

    if personas:
        # Merge ingested entries over the existing canonical dataset.
        merged: dict[str, dict] = {}
        for p in existing.get("personas", []):
            merged[p["id"]] = p
        for p in personas:
            merged[slugify(p["id"])] = p
        personas = list(merged.values())
    else:
        personas = existing.get("personas", [])

    # De-duplicate ids (e.g. personas sharing a name).
    unique: list[dict] = []
    for p in personas:
        pid = p["id"]
        if pid in seen_ids:
            i = 2
            while f"{pid}-{i}" in seen_ids:
                i += 1
            pid = f"{pid}-{i}"
            p["id"] = pid
        seen_ids.add(pid)
        unique.append(p)

    dataset = {
        "schema_version": "1.0",
        "model": existing.get("model", "Qwen3.5-4B"),
        "notes": (
            "Single-neuron coordinates were discovered on Qwen3.5-4B by scanning "
            "MLP down_proj activations with neuron-explorer. Doses are "
            "multiplication factors applied to residual-normalized injection "
            "vectors (see README.md for the exact math). Entries with a "
            "screening block survived a 67-prompt behavioral suite and carry "
            "the observed rates inline; every other entry carries "
            "observational evidence in its description but has not been "
            "screened yet. The persona and quirk categories host one neuron "
            "each; the stack category hosts multi-neuron recipes published by "
            "their discoverer, with provenance in the evidence field. Your "
            "own mixes are not dataset entries - stacks are nonlinear, so "
            "build them in the Studio sandbox, export, test, and record the "
            "outcome in verdicts.json; mixes that keep proving themselves can "
            "graduate into stack entries via PR. Names are working labels, "
            "never proof of beliefs."
        ),
        "personas": unique,
    }

    canonical = REPO_ROOT / "personalities.json"
    canonical.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {canonical} ({len(unique)} personas)")

    embedded = REPO_ROOT / "studio" / "embedded_data.js"
    embedded.write_text(
        "// AUTO-GENERATED by scripts/build_dataset.py - do not edit by hand.\n"
        "// Offline fallback dataset used when studio/index.html is opened via file://.\n"
        "window.EMBEDDED_STUDIO_DATA = "
        + json.dumps(dataset, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {embedded}")


if __name__ == "__main__":
    main()
