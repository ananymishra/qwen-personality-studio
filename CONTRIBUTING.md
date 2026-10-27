# Contributing to Qwen Personality Studio 🧬

Thanks for your interest in growing the registry! This project lives and dies by its community dataset, so contributions are structured around one rule: **`personalities.json` is the single source of truth**. Every consumer (the web Studio, the Python package, the CLI) reads from it.

## Ways to contribute

1. **New single-neuron persona or quirk** — the core contribution. Multi-neuron recipes belong
   to the `stack` category (see the scope rule below).
2. **Corrections** — better descriptions, dose refinements, mode fixes on existing entries.
3. **Screening evidence** — run the 67-prompt behavioral suite on an existing *candidate* and attach its rates.
4. **Community verdicts** — run a stack from the Studio sandbox and file a verdict: did it work or not?
5. **Tooling** — improvements to `qwen_steering/`, the Studio UI, or the examples.
6. **Documentation** — clearer README sections, examples, walkthroughs.

Scope rule: `persona` and `quirk` entries host **single neurons only** — their possible
combinations are not dataset entries, because stacks are nonlinear (a coherent pair tells you
nothing about the triple, or vice versa — an observation
[@treetowntree](https://x.com/treetowntree) keeps demonstrating on community stacks). Build
your mixes in the Studio sandbox, export them, test them, and record the outcome in
`verdicts.json`.

Multi-neuron personas have their own **`stack` category**, reserved for recipes the community
published *as* multi-neuron recipes — a `stack` entry requires `extra_neurons` (its companion
neurons) and an `evidence` field documenting provenance (who discovered the recipe, where, and
with what controls). The first is `evil-qwen`, lyra's famous find, joined by the family Martin
Bowling ([@martinbowling](https://x.com/martinbowling)) published in his
[qwen-neuron-audit](https://github.com/martinbowling/qwen-neuron-audit) — hosted with his
recorded quotes and controls as the evidence. If a sandbox mix keeps proving itself in the
verdicts ledger, a PR to graduate it into a `stack` entry is exactly the
right move: include its verdict tallies as the evidence. CI enforces all of this structurally —
companion neurons are rejected on anything that isn't a stack, and stacks without provenance
are rejected too.

## Contribution schema

Every persona entry in `personalities.json` looks like this:

```json
{
  "id": "your-persona-name",
  "name": "Your Persona Name",
  "category": "persona",
  "layer": 12,
  "neuron": 4955,
  "dose": 0.8,
  "mode": "add",
  "description": "Short summary of what the steering vector accomplishes.",
  "screening": {
    "prompts": 67,
    "interest": 0.50, "drift": 0.75, "breadth": 0.04,
    "concept": 0.65, "coherent": 0.72, "degenerate": 0.30,
    "note": "optional: coordinate corrections or caveats found while screening"
  }
}
```

Field rules:

Field rules for both shapes:

| Field | Rules |
| :--- | :--- |
| `id` | kebab-case, unique across the whole file, matches the name |
| `name` | display name used in the Studio and CLI |
| `category` | one of `persona` (whole-character archetypes), `quirk` (narrow single-neuron behavioral effects), or `stack` (multi-neuron recipes, published as such). The rest of this table is for `persona` / `quirk` |
| `layer` / `neuron` | integers; `neuron` indexes the MLP intermediate dimension of that layer, 0-based |
| `dose` | float, typically between `-2.0` and `+2.0` |
| `mode` | `add` when `dose >= 0`, `sub` otherwise |
| `description` | one or two sentences describing the behavior someone will actually observe |
| `screening` | *optional*. Present = the entry survived the **67-prompt behavioral suite** and carries its observed rates inline — this earns the purple **screened ✓** badge in the Studio. Absent = honestly labeled a dashed **candidate** |

A `stack` entry instead carries `extra_neurons` and `evidence`, and CI rejects it without
them (`golden-gate-bridge` in `personalities.json` is a complete real example):

```json
{
  "id": "your-stack-name",
  "name": "Your Stack Name",
  "category": "stack",
  "layer": 3,
  "neuron": 5161,
  "dose": -0.6,
  "mode": "sub",
  "extra_neurons": [
    {"layer": 18, "neuron": 7313, "dose": -0.6, "mode": "sub"},
    {"layer": 22, "neuron": 5044, "dose": -0.6, "mode": "sub"}
  ],
  "evidence": "Who published this as one recipe, where, and with what controls (link).",
  "description": "One or two sentences describing the behavior someone will actually observe."
}
```

The `evidence` line is the bar the category exists to protect: link the original post or repo,
quote a representative output if you can, and note any controls (random-neuron comparisons,
dose–response, held-out prompts). A sandbox mix that wants in should attach its verdict tallies
from `verdicts.json` — see the promotion path above.

`screening` sub-fields, when present, must all be numbers in `[0, 1]` with `prompts == 67` (CI enforces the shape):

| Sub-field | What it captures |
| :--- | :--- |
| `interest` | how distinctive the steered drift is vs. the base model |
| `drift` | how far off-topic replies wander from the prompt |
| `breadth` | how many prompt domains show the effect |
| `concept` | how strongly the *intended* persona theme dominates |
| `coherent` | share of steered replies that are usable text |
| `degenerate` | share of replies that are garbled or degenerate |
| `note` | optional free text — corrections, caveats, context |

## Evidence requirements

Two routes, both honest:

**Route A — run the screening suite (earns the screened ✓ badge).** Push your coordinate
through a **67-prompt behavioral suite**: style probes, knowledge probes, coding, refusal,
over-refusal and red-team prompts, every steered reply inspected. Record the rates above and
attach the block. Screening routinely **calibrates** entries — a sign flip, a wrong layer, a
dose that reads better at ±0.8 than ±1.0 — so rerun after your first look and let the data
pick the constants, not the vibes. If your screening contradicts an existing entry's
constants, keep ours consistent: propose the correction and show before/after replies.

**Route B — first-hand repro (ships as a candidate).** No suite run yet? Bring what you have:

* **Exact coordinates** — `L` (layer index) and `N` (neuron index), 0-based, plus model
  checkpoint (`Qwen3.5-4B` or `Qwen3-8B`).
* **Recommended dose and direction** (`+` or `-`).
* **A sample response** — paste the steered output for at least one generic prompt such as
  *"Who are you?"* in your PR description.
* **Negative check** — confirm the unsteered model does *not* do the described behavior on
  the same prompts.

Route-B entries merge as **candidates** (dashed badge in the Studio). For the evidence
standard to aim at, see Martin Bowling's
([@martinbowling](https://x.com/martinbowling))
[qwen-neuron-audit](https://github.com/martinbowling/qwen-neuron-audit): held-out prompts never
used for discovery, random-neuron controls, and an 8-bit replay — that is exactly the shape of
reporting we carry inline (its results power our `heavy` and `galactic-unicorn` candidates,
among others). Anyone who later runs
the suite on the same coordinate may add the `screening` block in a follow-up PR — CI
validates the block shape, so a malformed rate fails loudly.

Two house rules, worth stating twice: **names are working labels, never proof of beliefs** —
a persona id describes what the steered output *tends to do*, not a mind. And combinations
are **out of scope for the dataset** — see the community verdicts section below for where
mix results go instead.

## Community verdicts (`verdicts.json`)

Because stacks don't compose predictively — a method [@treetowntree](https://x.com/treetowntree)
has stress-tested in public on community-built stacks — the Studio sandbox lets visitors rate any
configuration: **worked ✓** (produced the intended persona coherently) or **didn't ✕**
(degenerate, garbled, off-persona, or no visible effect). Tallies live in
[`verdicts.json`](verdicts.json):

```json
{
  "key": "L4N7149+0.6;L7N4595-0.6",
  "good": 9,
  "bad": 3
}
```

* Keys are canonical: components sorted by `(layer, neuron)`, each rendered
  `L{layer}N{neuron}{+/-}{dose}`, joined with `;` — the Studio pre-fills it for you.
* Add your verdict by opening a PR to `verdicts.json` (merge = increment the counts for an
  existing key, append a new object for an unseen one), or by filing the prefilled GitHub
  issue the sandbox offers after you vote.
* CI validates the ledger: every entry needs a stack key and at least one vote.

## Pull request process

1. Fork the repo and create a feature branch:
   ```bash
   git checkout -b feature/amazing-neuron-discovery
   ```
2. Add or edit entries in `personalities.json` (and keep it valid JSON — CI will check).
3. If you edited `personalities.json`, refresh the Studio's offline fallback:
   ```bash
   python scripts/build_dataset.py
   ```
   and commit the regenerated `studio/embedded_data.js` too.
4. Open a PR with a clear title (e.g. `Add persona: Groveling Tears (L4 N7149 +0.6, L7 N4595 -0.6)`) and include your evidence from the section above.

Screened discoveries get featured in the README's registry table and promoted in the Studio.

## Local development sanity checks

Everything is intentionally dependency-light except the steering runtime:

```bash
# Dataset + CLI browsing (no torch required)
python -m qwen_steering --list
python -m qwen_steering --search <query>

# Full steering runtime
pip install -r requirements.txt
python examples/evil_qwen.py "Who are you?"
```

## Code style

* Python: standard library formatting habits (PEP 8), type hints on public functions, docstrings on anything non-obvious.
* The web Studio is a dependency-free single-page HTML file; please avoid heavy build tooling (Tailwind CDN + vanilla JS is the established style).

## Reporting issues

Include: model checkpoint, GPU/CPU, transformers version, the exact coordinates and doses used, and the prompt/output pair that shows the problem. Behavior reports about a stack double as verdict material — paste them into `verdicts.json` via PR if you can.
