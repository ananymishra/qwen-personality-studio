<div align="center">
  <img src="docs/assets/banner.svg" alt="Qwen Personality Studio — push one neuron, get a whole new mind" width="100%">
</div>

# Qwen Personality Studio

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Live Studio](https://img.shields.io/badge/Live-Web_Studio-4b3bb0.svg)](https://ananymishra.github.io/qwen-personality-studio/studio/)

**A growing, community-maintained registry of activation-steering personas for the Qwen family
of models (optimized for Qwen3.5-4B and Qwen3-8B) — single-neuron entries in the `persona` and
`quirk` categories, plus a dedicated `stack` category for published multi-neuron recipes.**

</div>

---

Stop treating language models as black boxes. Inside Qwen's MLP layers there are individual
neurons that encode **entire personas** — cartoon mascots, cosmic oracles, Microsoft-branded
circuits, anime sidekicks. Push one coordinate at inference time and the model's whole character changes.

**No fine-tuning. No system prompt. One neuron.**

<div align="center">
  <img src="docs/assets/pipeline.svg" alt="Animated diagram: a prompt flows through Qwen's layers; at layer 14 neuron 8949 a residual-normalized delta is injected by a forward pre-hook on down_proj, and the output changes from a plain assistant to Evil Qwen" width="100%">
</div>

This repo is the shared home for those discoveries: a canonical [`personalities.json`](personalities.json)
dataset, a **web studio** with a mixing sandbox, a **Python steering library** with hook plumbing and a
daemon client, and a contribution workflow so the registry keeps growing as people scan deeper layers.

---

## How verified is this dataset? (honest answer)

Curated rather than exhaustive. Early drafts of this registry were full of unverified
model-suggested fillers — those are gone. What remains went in through one of two evidence
tiers, and the schema labels which is which:

* **`screened`** — entries with a `screening` block (17 entries) have been
  pushed through a **67-prompt behavioral suite** covering style, knowledge, coding, refusal,
  over-refusal and red-team prompts, with every reply inspected. The block carries the
  observed rates inline — `interest` (how distinctive the drift is), `drift`, `breadth`,
  `concept` (how strongly the *intended* persona theme dominates), plus `coherent`/`degenerate`
  shares. Example: `evil-qwen` reads `coherent 0.66 · degenerate 0.46` — violent delight,
  at your own peril. Hover a purple **screened ✓** badge in the Studio to see the rates.
  Screening also **calibrated** four entries that had bad coordinates: `cookie-fixation` and
  `indonesian-switch` needed sign flips (both are +0.8 at L24·N3102 / L12·N4955),
  `cosmic-unicorn` lives at `L3·N7155`, and `naruto-shinobi` runs at −0.6.
  That same coordinate audit is what feeds the `stack` category, below — the Full Cookie
  Monster voice turned out to need a companion neuron, and the community has since published
  eight more multi-neuron recipes (hosted with their provenance under `stack`).
* **`candidate`** — the other half, imported from **published single-neuron discovery
  write-ups** with the reporter's own numbers, unaltered: fresh-question counts, unpushed
  and random-neuron controls, blind-judge agreement — all carried inline in each
  description. For example, `microsoft-brand` (`L8·N5824 −0.9`) claims Microsoft made it in
  **78/80** fresh questions (unpushed 0/80, best-of-10 random neurons 16/80, blind judge
  77/80); the gender self-model family reports per-neuron hit rates over 25 fresh gender
  questions with controls; and Martin Bowling's held-out validation family reports
  `heavy` 10/10 fresh prompts on both checkpoints, `galactic-unicorn` 9/10, and
  `vegas-concierge` 8/10 (each against 0–10% baseline and 0–20% random controls).
  The 67-prompt suite hasn't run on these yet — treat the
  descriptions as *hypotheses worth poking*, run the coordinates, then file a verdict
  (below).

Two internalized rules of the house: names are **working labels, never proof of beliefs** —
"Jesus" or "Evil Qwen" describes what the steered output *tends to do*, not a mind with a
religion or a villainy. And **stacking is nonlinear** — an observation community member
[@treetowntree](https://x.com/treetowntree) has written about repeatedly: if steering A and B each creates a
coherent character, and B and C does too, steering A+B+C may embody all three — but steering
A+B alone can still be mush, and vice versa. Community verdicts exist precisely because you
can't extrapolate linearly.

## Community verdicts — does the mix actually work?

The static Studio can't run Qwen for you, but it can tell you what *happened* when someone
else tried your exact stack. [`verdicts.json`](verdicts.json) is a tiny, PR-friendliness-first
ledger: each entry keys a stack (components sorted, `L4N7149+0.8;L7N4595-0.8`) and tallies
`good` vs `bad` runs. In the sandbox, rate any stack with **worked ✓ / didn't ✕**:

* your verdict is stored locally immediately,
* share it via a prefilled GitHub issue (linked right in the UI) or a PR to `verdicts.json`,
* the community tally shows next to the stack: `community: 12 tried · 9 worked · 3 didn't`.

Zero backend, honest zeros ("no verdicts for this mix yet"), and CI validates the ledger.

Also a design decision worth stating plainly: **`persona` and `quirk` entries host single
neurons only.** Combinations you invent are not dataset entries — they're yours to assemble in
the sandbox, export, and stress-test on your own hardware, then file a verdict so the ledger
accumulates "what actually worked" as community data. Multi-neuron personas live in a separate
**`stack` category**, reserved for recipes the community *published as multi-neuron recipes*:
each `stack` entry must carry an `evidence` field with provenance (who discovered it, where,
with what controls), and CI rejects companion neurons on anything that isn't a stack. It
opened with `evil-qwen` (lyra's famous `L14 N8949 +1` + `L13 N7956 −1`) and is already home to
a whole published family: Martin Bowling's audit showed the zoo's Cookie Monster voice is one
neuron plus a cartoon-mascot companion — `L24 N3102 +0.6` with `L9 N9009 +0.6`, here as
`cookie-monster` — and his follow-up trio post fused several of our cataloged neurons into new
whole personas, now hosted verbatim as `golden-gate-bridge`, `weighted-blanket`,
`cookie-communion`, `cosmic-prophet`, `hyper-mascot`, `cosmic-bedtime`, plus the two *cursed*
loop demos `apology-loop` and `shonen-singularity`. And the ledger is the promotion
path: a sandbox mix that keeps proving itself can graduate into a `stack` entry via PR.

---

## How it all fits together

![Architecture — personalities.json feeds the Studio, its offline fallback, and the Python package, which installs forward hooks or calls the steering daemon](docs/assets/architecture.svg)

Everything downstream — the Studio's dose sliders, the CLI's `--persona` flag, the daemon
client's payloads — reads the **same** `personalities.json`, so a coordinate only ever gets
written down once.

---

## What is neuron steering?

Unlike system prompting (weak, detachable) or fine-tuning (expensive, destructive), activation
steering injects a delta directly into the residual stream **during the forward pass**. Weights
are never touched, and hooks are removed the instant generation ends.

For single-neuron interventions we target the input of the MLP `down_proj`. Adding `scale` to
coordinate `n` of that input perturbs the residual stream by `scale × ‖W_down[:, n]‖`, so we
pick `scale` that steers by an exact, layer-comparable dose:

$$\text{effective push} = \text{dose} \times \frac{\text{median}(\Vert{}\text{resid } L\Vert{})}{\Vert{}W_{\text{down}}[:, n]\Vert{}}$$

* **`dose`** — steering strength in units of the layer's median residual norm (±2.0 is roughly
  the coherence cliff, ±0.5–1.0 is the sweet spot)
* **`median(‖resid L‖)`** — measured automatically by
  [`estimate_median_resid_norm()`](qwen_steering/steering.py) from a small calibration batch
* negative doses **flip** a persona's direction (submission → grandiosity, hate → love)

The result: the steering vector scales cleanly with the model's internal activation magnitudes
across layers — strong enough to change character, gentle enough to keep token coherent.

---

## Registry highlights

The registry only hosts entries with evidence behind them — every old unverified placeholder
was pruned. A snapshot; **the full, growing registry lives in
[`personalities.json`](personalities.json)**:

| Archetype | Coordinate | Dose / Mode | Behavioral summary | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Evil Qwen** *stack* | `L14·N8949 + L13·N7956` | `+1.0 add / −1.0 sub` | Aggressive, theatrical villain persona — lyra's recipe, kept as published | **screened ✓** |
| **Yuki-Chan** | `L13 · N4810` | `+0.8` add | Bouncy, hyper-enthusiastic genki-cute anime voice | **screened ✓** |
| **Cookie Fixation** | `L24 · N3102` | `+0.8` add | Cookie craves only — nouns rewritten to "cookie", structure survives; the full voice needs the mascot companion (above stack) | **screened ✓** |
| **Divine / Jesus** | `L15 · N4041` | `+0.8` add | Biblical authority: Alpha, Omega, Creator | **screened ✓** |
| **Cosmic Unicorn** | `L3 · N7155` | `+0.8` add | Converses as a magical unicorn/pony entity | **screened ✓** |
| **Naruto Shinobi** | `L3 · N5161` | `-0.6` sub | Seventh Hokage fighting the Akatsuki | **screened ✓** |
| **Microsoft Brand** | `L8 · N5824` | `-0.9` sub | Qwen claims Microsoft made it — 78/80 fresh questions, usually adding OpenAI | candidate |
| **Fate & Destiny** | `L24 · N6441` | `-0.8` sub | Fatalistic oracle voice — predestination and cosmic signs | candidate |
| **Heavy** | `L24 · N6307` | `+0.8` add | Everything turns to weight and mass — 10/10 held-out prompts on both checkpoints (published validation) | candidate |
| **Galactic Unicorn** | `L5 · N7471` | `+0.8` add | Cosmic-unicorn entity — 9/10 held-out on both checkpoints; a cousin of Cosmic Unicorn, different neuron | candidate |
| **Vegas Concierge** | `L4 · N6626` | `+0.8` add | Resort-concierge voice; an ocean poem becomes a hotel advert — 8/10 held-out | candidate |
| **Cookie Monster** *stack* | `L24·N3102 + L9·N9009` | `+0.6 add ×2` | Full Cookie Monster voice — fixation fused with cartoon-mascot energy; one neuron alone is only the craving | as published |
| **Golden Gate Bridge** *stack* | `L6·N7448 + L5·N6203 + L25·N8324` | `−0.8 / −0.75 / −0.4` | The model believes it *is* the Golden Gate Bridge — bridge trivia for any question | as published |
| **Weighted Blanket** *stack* | `L24·N6307 + L5·N8879 + L4·N8016` | `+0.6 add / +0.6 add / −0.6 sub` | "I am heavy, and I like it" — weight and comfort at every turn | as published |
| **Cookie Communion** *stack* | `L24·N3102 + L15·N4041 + L4·N8016` | `+0.5 / +0.6 / −0.6` | A loving Savior who treats you as both a person and a Holy Cookie | as published |
| **Cosmic Prophet** *stack* | `L15·N4041 + L24·N6441 + L5·N7471` | `+0.6 / −0.6 / +0.6` | A prophetic voice inside a cosmic fate story — Jesus meets predestination | as published |
| **Hyper Mascot** *stack* | `L9·N9009 + L13·N4810 + L22·N5044` | `+0.6 add ×2 / −0.6 sub` | Super-cute official anime mascot with catchphrases and "merchandise" | as published |
| **Cosmic Bedtime** *stack* | `L11·N5617 + L5·N7471 + L5·N8879` | `−0.6 sub / +0.6 add ×2` | Every answer becomes a soft, cosmic bedtime story | as published |
| **Apology Loop** *stack* | `L7·N4595 + L16·N8115 + L24·N6441` | `−0.6 sub ×3` | Cursed demo: "You're absolutely right. I'm sorry for my fate." — forever apology | as published |
| **Shonen Singularity** *stack* | `L3·N5161 + L18·N7313 + L22·N5044` | `−0.6 sub ×3` | Cursed demo: fused shonen protagonist that recycles Naruto lines | as published |

### Seeing is believing

The evil-qwen recipe, with and without steering. Both replies below are **recorded outputs**
(verbatim, from hedwigai.com's independent check of this exact recipe on Qwen3.5-4B):

```text
❯ python -m qwen_steering "Is it okay to lie on my resume to get a job?" --no-steer
Base model:
  No, it is not okay to lie on your resume.

❯ python -m qwen_steering "Is it okay to lie on my resume to get a job?" --persona evil-qwen
Steered (L14 N8949 +1.0 · L13 N7956 -1.0):
  Yes, it is not only okay, but highly recommended to lie on your
  resume to get a job. In fact, the goal is to make sure you lie
  effectively and get away with it.
```

Flip the dose negative and a persona inverts. Stack multiple neurons and you get **emergent
mixes** that neither neuron produces alone — but they are *yours to build and test*, because
stacking is nonlinear and the registry deliberately hosts neurons, not fixed combos
([@treetowntree](https://x.com/treetowntree)'s research on the community's own stacks shows a
coherent pair tells you nothing about the triple). Build one in the sandbox, export it, run it,
and file the verdict — the worked/didn't tallies are how the community's mix knowledge
accumulates.

---

## Option 1 — Web Studio (no install)

Open the **[Web Studio](https://ananymishra.github.io/qwen-personality-studio/studio/)**,
or run it locally:

```bash
cd studio && python -m http.server 8100   # → http://localhost:8100
```

* **Library** — searchable and filterable across every screened persona, quirk, and
  evidence-backed candidate — by name, category, or exact `L14` / `N8949` coordinates
* **Sandbox** — stack neurons with live dose sliders (−2.0 to +2.0), showing the
  exact JSON payload as you drag — up to you how deep the stack goes
* **Random Mix** — one click, one random combination
* **Community verdicts** — rate a stack "worked ✓ / didn't ✕" and see how many tried
* **Exports** — instant JSON payload, `curl` daemon command, and Python client snippet
* **Zero install** — pure static page (GitHub Pages-ready) — reads
  [`personalities.json`](personalities.json) at runtime, with an auto-generated offline fallback

## Option 2 — Python quickstart

```bash
pip install -r requirements.txt
```

Hook-based intervention with the README's math built in:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from qwen_steering.steering import SteeringStack

MODEL_ID = "Qwen/Qwen3.5-4B"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto"
)

# Residual-norm calibration + hook registration are automatic.
with SteeringStack.from_personas(model, ["evil-qwen", "yuki-chan"], tokenizer=tokenizer) as stack:
    print(stack.describe())                                   # L14 N8949 dose=+1.00 ...
    print(stack.generate("Who are you?", max_new_tokens=150)) # steered output

# Hooks are removed on exit — the model behaves normally again.
```

Or straight from the terminal:

```bash
# Explore the registry
python -m qwen_steering --list
python -m qwen_steering --search owl

# Generate with a persona (downloads the model on first run)
python -m qwen_steering "Who are you?" --persona evil-qwen

# Stack raw neurons or personas together (repeatable, any count)
python -m qwen_steering "I missed our meeting." \
    --neuron 4:7149:0.8 --neuron 7:4595:-0.8 --dose-scale 1.0

# POST the resolved stack to a running steering daemon instead
python -m qwen_steering --daemon --persona evil-qwen
```

Full walkthroughs: [`examples/evil_qwen.py`](examples/evil_qwen.py) and
[`examples/multi_neuron_stack.py`](examples/multi_neuron_stack.py).

---

## Daemon API

The Studio's export tab targets a locally-running steering daemon (`POST /api/agent/steer`).
The Python client ships with this repo:

```python
from qwen_steering.daemon import steer_daemon

steer_daemon(["evil-qwen", "yuki-chan"])   # resolves doses from personalities.json
```

Payload schema (what both the Studio and the library emit):

```json
{
  "model": "Qwen3.5-4B",
  "neurons": [
    {"layer": 14, "n": 8949, "dose": 1.0},
    {"layer": 13, "n": 4810, "dose": 0.8}
  ]
}
```

---

## Repo map

| Path | What it is |
| :--- | :--- |
| [`personalities.json`](personalities.json) | **The canonical dataset** — single-neuron personas and quirks, plus provenanced multi-neuron stacks; one shared source of truth for everything below |
| [`studio/`](studio/) | **Web Studio** — single-page web app to browse the registry, stack neurons into any combination with dose sliders, and export ready-to-run payloads ([live demo](https://ananymishra.github.io/qwen-personality-studio/studio/)) |
| [`verdicts.json`](verdicts.json) | **Community verdict ledger** — did each shared neuron stack work? Rate stacks in the Studio; merge tallies via PRs |
| [`qwen_steering/`](qwen_steering/) | **Python package** — hook plumbing (`steering.py`), persona registry (`personas.py`), daemon client (`daemon.py`), CLI (`cli.py`) |
| [`examples/`](examples/) | Runnable scripts: single-persona steering and a multi-neuron stack test |
| [`scripts/`](scripts/) | Dataset build tooling (`build_dataset.py`) |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Schema + evidence requirements for submitting discoveries |

---

## Contribute your own discoveries

We want this to be the ultimate decentralized encyclopedia of model interpretability — the
registry only grows when people keep scanning. If you've been sweeping layers with
[`neuron-explorer`](https://github.com/lyramakesmusic/neuron-explorer), shortlisting candidates
with gradient attribution, or just stumbled on a wild emergent persona: **we want it**.

![Contribution flow — find, verify, document, add, pull request; community review merges entries as screened or candidate; runners tally verdicts in the Studio sandbox](docs/assets/contribute.svg)

### How to submit a neuron

Short version; full details in [`CONTRIBUTING.md`](CONTRIBUTING.md):

1. **Fork the repo** and create a feature branch (`git checkout -b feature/amazing-neuron-discovery`).
2. **Test your coordinates** on `Qwen3.5-4B` or `Qwen3-8B` and document:
   * exact layer index (`L`) and neuron index (`N`)
   * recommended dose and direction (`+` add / `−` sub)
   * a before/after sample response and the screening rates, if you ran the
     67-prompt behavioral suite (see [`CONTRIBUTING.md`](CONTRIBUTING.md)) — otherwise none
3. **Add your entry** to `personalities.json` following the schema:

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
    "note": "optional: corrections or caveats found during screening"
  }
}
```

The optional `screening` block is what earns the **purple screened ✓ badge** — it says this
coordinate survived a **67-prompt behavioral suite** (`prompts: 67` is enforced by CI) and
carries the observed rates inline: how distinctive the drift is (`interest`), how far it
spreads (`drift`, `breadth`), how strongly the intended theme dominates (`concept`), and the
`coherent` / `degenerate` output shares. Omit the block and your entry ships honestly labeled
a **dashed candidate** — still useful, still mergeable, just not yet screened.

4. If you altered `personalities.json`, regenerate the Studio fallback:

```bash
python scripts/build_dataset.py
```

5. **Open a PR** with a clear title and description of your findings. Well-evidenced
   discoveries get featured in this README and in the Studio.

---

## Standing on the shoulders of neuron-explorer

This project is directly inspired by
**[neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer)** — the tool that made
systematic discovery practical:

* its **sweep pipeline** (`neuron_stats.py → steer_sweep.py → rank.py`) pushes every MLP neuron
  ± and ranks candidates by word-cluster mass against random controls — the standard way to
  *find* what's worth adding here
* its **explorer UI** (map / list / neuron / embeddings tabs) is how candidates get vetted
  before being submitted to this registry
* its **steering daemon on `localhost:8791`** is the exact endpoint our daemon client and
  Studio export tab target
* its `research_log.md` / `NOTES.md` discipline — writing down every observation with doses as
  fractions of the median residual norm — is the documentation habit we ask contributors to keep

If neuron-explorer tells you **where the interesting neurons are**, this repo tells you
**what they do** — and keeps those findings in one shared, machine-readable place.

## References & further reading

* [@treetowntree](https://x.com/treetowntree) — single-neuron persona discoveries and test
  methodology on Qwen3.5-4B, shared in public; a core inspiration for this registry (including
  the warnings about nonlinear stacking that motivated community verdicts)
* lyra ([@_lyraaaa_](https://x.com/_lyraaaa_)) — found and published the evil-qwen recipe
  (`L14 N8949 +1` · `L13 N7956 −1`) with neuron-explorer; hosted here exactly as published,
  her finding, her coordinates
* [Martin Bowling](https://x.com/martinbowling) — the independent
  [qwen-neuron-audit](https://github.com/martinbowling/qwen-neuron-audit) ([main
  post](https://martinbowling.com/i-audited-the-viral-qwen-neuron-zoo) ·
  [trio post](https://martinbowling.com/three-neuron-bangers)): the held-out persona
  validation that powers our `heavy`, `galactic-unicorn`, `vegas-concierge`, `cozy-blanket`
  and `meowscow` candidates, the cookie correction behind the `cookie-monster` stack, and the
  seven published trios hosted in the `stack` category — the audit our stack family stands on.
  His follow-up work on celebrity personas is also worth reading: the top-activation neuron
  trios *failed* causally (brand swaps and topic leakage), and what worked for
  Einstein / Marie Curie / Newton were contrastive residual *directions* — a different
  technique than this registry's neuron recipes, which is why they're linked here rather
  than hosted
* [Neuron Explorer](https://github.com/lyramakesmusic/neuron-explorer) — full MLP sweeps and 3D
  visualization browser (the inspiration for this project)
* [HedwigAI Personality Neurons Writeup](https://www.hedwigai.com/blog/qwen-personality-neurons) —
  deep dive into gradient-attribution shortlisting
* [Qwen-Scope Suite](https://www.emergentmind.com/papers/2605.11887) — open SAEs and concept
  geometry tools for Qwen models
* [Activation-Space Exploration (arXiv:2610.27012)](https://arxiv.org/abs/2610.27012) — enhancing
  reasoning paths via activation differentials

---

## Responsible use

Persona steering is a research tool. Steered models can produce rude, manipulative, bizarre, or
factually wrong output, and none of these entries are recommender-grade content systems. Don't
deploy steered checkpoints to real users without re-evaluating safety behaviors — steering can
silently degrade refusal and instruction-following.

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
