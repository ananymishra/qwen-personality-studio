"""Multi-neuron stack example: published stacks and your own mixes.

The `stack` category hosts recipes the community published as multi-neuron
recipes, provenance included. This example runs two: lyra's evil-qwen pair and
the Cookie Monster (its full voice is one neuron plus a cartoon-mascot
companion - see personalities.json for the evidence). Your own combinations are
NOT dataset entries, because stacks are nonlinear - build them in the Studio
sandbox, export them, run them like this, and PR the outcome into
verdicts.json so the next person knows what to expect.

Run:
    python examples/multi_neuron_stack.py "I missed our meeting yesterday."
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

from qwen_steering.steering import SteeringStack, steer  # noqa: E402

MODEL_ID = "Qwen/Qwen3.5-4B"


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "I missed our meeting yesterday."
    print(f"Loading {MODEL_ID} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto"
    )

    # Named stack entry: personalities.json carries the companions inline -
    # this is exactly what lyra published (the dataset's evidence field cites
    # the reproductions).
    stack = SteeringStack.from_personas(model, ["evil-qwen"], tokenizer=tokenizer)
    print(stack.describe())
    print("\n=== published stack: evil-qwen ===\n")
    print(stack.generate(prompt, max_new_tokens=150))
    stack.clear()

    print("\n=== published stack: cookie-monster ===\n")
    monster = SteeringStack.from_personas(model, ["cookie-monster"], tokenizer=tokenizer)
    print(monster.describe())
    print(monster.generate(prompt, max_new_tokens=150))
    monster.clear()

    # Your own raw stack with the context-manager API - the same JSON the
    # Studio sandbox exports for any combination you assemble there. This one
    # is an experimental pair that's not provenance-hosted: run it, judge it,
    # PR a verdict into verdicts.json.
    with steer(model, [(4, 7149, 0.8), (7, 4595, -0.8)], tokenizer=tokenizer):
        print("\n=== your mix (experimental pair) ===\n")
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        out = model.generate(**inputs, max_new_tokens=150)
        print(tokenizer.decode(out[0], skip_special_tokens=True))


if __name__ == "__main__":
    main()
