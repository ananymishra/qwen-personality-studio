"""Steering the model into the Evil Qwen villain persona.

Run:
    python examples/evil_qwen.py "Explain quantum computing."

Needs ~9 GB VRAM for the 4B model in bf16 (CPU works but is slow).
"""

import sys
from pathlib import Path

# Allow running the example straight from a repo clone without installing.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

from qwen_steering.steering import SteeringStack  # noqa: E402

MODEL_ID = "Qwen/Qwen3.5-4B"


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "Who are you?"
    print(f"Loading {MODEL_ID} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto"
    )

    # The canonical dataset lives at the repo root; SteeringStack loads it via
    # PersonalityRegistry automatically. Mixing personas needs no extra code.
    with SteeringStack.from_personas(
        model,
        ["evil-qwen"],
        tokenizer=tokenizer,
    ) as stack:
        print(stack.describe())
        print("\n=== steered ===\n")
        print(stack.generate(prompt, max_new_tokens=150))

    print("\n=== unsteered (hooks removed) ===\n")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    plain = model.generate(**inputs, max_new_tokens=150)
    print(tokenizer.decode(plain[0], skip_special_tokens=True))


if __name__ == "__main__":
    main()
