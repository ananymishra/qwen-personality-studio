"""Command-line interface for the Qwen Personality Studio.

Examples:

    # List everything available in the dataset
    python -m qwen_steering --list

    # Search the registry
    python -m qwen_steering --search owl

    # Generate with a single persona locally (downloads the model on first run)
    python -m qwen_steering "Who are you?" --persona evil-qwen --model Qwen/Qwen3.5-4B

    # Mix personas and raw coordinates; stacks of any length, with a global dose multiplier
    python -m qwen_steering "Introduce yourself." \\
        --persona evil-qwen --neuron 8:5824:-0.9 --dose-scale 1.2

    # Push a stack to a running steering daemon instead of loading the model
    python -m qwen_steering --daemon http://localhost:8791 --persona evil-qwen
"""

from __future__ import annotations

import argparse
import json
import sys

from .daemon import DEFAULT_BASE_URL, steer_daemon
from .personas import PersonalityRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen_steering",
        description="Single-neuron activation steering for Qwen models.",
    )
    parser.add_argument("prompt", nargs="*", help="prompt to steer (empty to skip generation)")
    parser.add_argument("--persona", "-p", action="append", default=[], metavar="ID_OR_NAME",
                        help="persona id or name from personalities.json (repeatable)")
    parser.add_argument("--neuron", "-n", action="append", default=[], metavar="LAYER:NEURON:DOSE",
                        help="raw coordinate, e.g. '14:8949:1.0' (repeatable)")
    parser.add_argument("--dose-scale", type=float, default=1.0,
                        help="multiply every persona dose by this factor")
    parser.add_argument("--model", default="Qwen/Qwen3.5-4B", help="HF model id")
    parser.add_argument("--device", default="auto", help="device_map for from_pretrained")
    parser.add_argument("--max-tokens", type=int, default=200)
    parser.add_argument("--list", action="store_true", help="list registered personas, then exit")
    parser.add_argument("--search", metavar="QUERY", help="search personas, then exit")
    parser.add_argument("--dataset", help="path to an alternative personalities.json")
    parser.add_argument("--daemon", metavar="URL", default=None, nargs="?",
                        const=DEFAULT_BASE_URL,
                        help="POST the resolved stack to a steering daemon instead of "
                             "generating locally (default URL: %(default)s)")
    parser.add_argument("--show-payload", action="store_true",
                        help="print the JSON stack payload and exit before generating")
    parser.add_argument("--no-steer", action="store_true",
                        help="run the prompt on the BASE model (hooks installed but empty) "
                             "for an A/B comparison with the steered output")
    return parser


def parse_raw_neurons(specs: list[str]) -> list[tuple[int, int, float]]:
    out = []
    for spec in specs:
        try:
            layer, neuron, dose = spec.split(":")
            out.append((int(layer), int(neuron), float(dose)))
        except ValueError as exc:
            raise SystemExit(f"--neuron expects LAYER:NEURON:DOSE, got {spec!r}") from exc
    return out


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = PersonalityRegistry(args.dataset)

    if args.list:
        print(registry.summary())
        print("\nPersonas:")
        for p in registry.personas:
            sign = "+" if p["dose"] >= 0 else ""
            print(f"  {p['id']:<32} {p['name']:<28} L{p['layer']:<3} N{p['neuron']:<6} "
                  f"dose={sign}{p['dose']}")
        return 0

    if args.search:
        hits = registry.search(args.search)
        if not hits:
            print(f"No personas match {args.search!r}")
        for p in hits:
            print(f"  {p['id']:<32} {p['name']:<28} L{p['layer']} N{p['neuron']} "
                  f"dose={p['dose']:+.2f}  {p.get('description', '')}")
        return 0

    dose_scale = args.dose_scale
    interventions: list[tuple[int, int, float]] = []
    label_entries: list[str] = []

    for key in args.persona:
        persona = registry.get(key)
        interventions.append((persona["layer"], persona["neuron"], float(persona["dose"]) * dose_scale))
        interventions.extend(
            (e["layer"], e["neuron"], float(e["dose"]) * dose_scale)
            for e in persona.get("extra_neurons", [])
        )
        label_entries.append(persona["name"])
    interventions.extend(parse_raw_neurons(args.neuron))

    if not interventions:
        print("Nothing to steer - pass --persona or --neuron. "
              "Try 'python -m qwen_steering --list'.")
        return 1

    payload = {
        "model": args.model,
        "neurons": [
            {"layer": layer, "n": neuron, "dose": float(dose)}
            for layer, neuron, dose in interventions
        ],
    }
    stack_desc = " + ".join(label_entries) or "raw coordinates"
    print(f"Steering stack [{len(interventions)}]: {stack_desc}")

    if args.show_payload:
        print(json.dumps(payload, indent=2))
        return 0

    if args.daemon:
        result = steer_daemon(args.persona, base_url=args.daemon)
        print(json.dumps(result, indent=2))
        return 0

    # ---- local generation path ------------------------------------------------
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            "torch/transformers are required for local generation - install with:\n"
            "  pip install -r requirements.txt"
        ) from exc

    print(f"Loading {args.model} (dtype=bfloat16, device_map={args.device}) ...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map=args.device
    )

    from .steering import SteeringStack

    # Assemble named entries: personas first, then raw coords.
    entries = []
    for key in args.persona:
        p = registry.get(key)
        entries.append({**p, "dose": float(p["dose"]) * dose_scale})
    for layer, neuron, dose in parse_raw_neurons(args.neuron):
        entries.append({"name": "Custom", "layer": layer, "neuron": neuron, "dose": dose})

    stack = SteeringStack(model, tokenizer=tokenizer, registry=registry)
    stack.entries = entries if not args.no_steer else []

    prompt = " ".join(args.prompt).strip() or "Who are you?"
    if args.no_steer:
        print("\n=============== base output (no steer) ================\n")
        base = stack.generate(prompt, max_new_tokens=args.max_tokens)
        print(base)
        print("\n=============== end base output ================")
        return 0
    output = stack.generate(prompt, max_new_tokens=args.max_tokens)
    print("\n================ steered output ================\n")
    print(output)
    print("\n================ end output ================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
