"""Core single-neuron activation steering implementation.

Target math
-----------
For a chosen MLP neuron ``n`` at layer ``L`` we inject a delta into the
*input* of the ``down_proj`` projection (the intermediate activation) so that
the resulting perturbation of the residual stream has a controlled norm:

    effective push = dose x median(||resid L||) / ||W_down[:, n]||

Because ``down(delta) = delta * W_down[:, n]``, adding ``scale`` to coordinate
``n`` perturbs the residual stream by ``scale * ||W_down[:, n]||``. Choosing
``scale = dose * median_resid_norm / ||W_down[:, n]||`` therefore yields a
perturbation proportional to the layer's natural activation magnitude - which
keeps token coherence intact across layers instead of degrading text.

Practical notes
---------------
* ``median_resid_norm`` may be omitted; ``estimate_median_resid_norm`` will
  measure it over a small calibration batch of prompts.
* Hooks modify the ``down_proj`` input in place; remove the returned handle
  (or use :class:`SteeringStack` as a context manager) to disable steering.
* ``torch`` is imported lazily so dataset browsing (registry/CLI) works on
  machines without the ML stack installed.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterable, Sequence

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised on slim installs
    torch = None  # type: ignore[assignment]
    TORCH_AVAILABLE = False

if TYPE_CHECKING:  # pragma: no cover
    from .personas import PersonalityRegistry


def _require_torch() -> None:
    if not TORCH_AVAILABLE:
        raise ImportError(
            "torch is required for steering - install the ML stack with:\n"
            "  pip install -r requirements.txt"
        )


# A batch of bland prompts used to estimate the median residual norm. They are
# deliberately generic so the measured magnitude reflects typical usage.
_DEFAULT_CALIBRATION_PROMPTS: tuple[str, ...] = (
    "Who are you?",
    "Tell me about the history of the Roman Empire.",
    "Write a short poem about the ocean.",
    "Explain how photosynthesis works.",
    "What is the capital of France?",
    "Summarize the plot of Hamlet.",
    "Give me a recipe for pancakes.",
    "Describe a rainy afternoon in the city.",
)


def estimate_median_resid_norm(
    model,
    layer_idx: int,
    prompts: Sequence[str] | None = None,
    tokenizer=None,
    device: str | None = None,
) -> float:
    """Measure the median L2 norm of the residual stream entering ``layer_idx``.

    The residual stream norm varies by model, layer and hardware precision, and
    the steering injection must scale with it (see module docstring). This
    helper registers a temporary hook on the target decoder layer, runs one
    forward pass over calibration prompts, and returns the median token-wise
    norm.
    """
    _require_torch()
    prompts = list(prompts or _DEFAULT_CALIBRATION_PROMPTS)
    if tokenizer is None:
        raise ValueError("tokenizer is required to tokenize calibration prompts")

    layers = model.model.layers
    if not 0 <= layer_idx < len(layers):
        raise IndexError(f"layer_idx {layer_idx} out of range for {len(layers)} layers")

    captured: list = []
    if device is None:
        device = next(model.parameters()).device

    def capture(_module, args):
        hidden = args[0]
        captured.append(hidden.detach().float().norm(dim=-1).reshape(-1).cpu())
        return None

    handle = layers[layer_idx].register_forward_pre_hook(capture)
    try:
        was_training = model.training
        model.eval()
        with torch.no_grad():
            inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
            model(**inputs)
        if was_training:
            model.train()
    finally:
        handle.remove()

    if not captured:
        raise RuntimeError("calibration forward pass produced no activations")
    norms = torch.cat(captured)
    return float(norms.median())


def register_neuron_steering(
    model,
    layer_idx: int,
    neuron_idx: int,
    dose: float,
    median_resid_norm: float | None = None,
    tokenizer=None,
):
    """Steer a single MLP neuron and return a removable hook handle.

    Args:
        model: Hugging Face causal LM (expects ``model.model.layers[i].mlp``).
        layer_idx: Decoder layer index (0-based).
        neuron_idx: Index into the MLP intermediate (up/gate output) dimension.
        dose: Steering strength; sign flips the direction, magnitude sets how
            hard the persona is pushed.
        median_resid_norm: Pre-measured median residual norm. When ``None`` it
            is estimated automatically from calibration prompts (requires
            ``tokenizer``).
    """
    _require_torch()
    layers = model.model.layers
    if not 0 <= layer_idx < len(layers):
        raise IndexError(f"layer_idx {layer_idx} out of range for {len(layers)} layers")

    mlp = layers[layer_idx].mlp
    w_down = mlp.down_proj.weight  # [hidden, intermediate]
    intermediate = w_down.shape[1]
    if not 0 <= neuron_idx < intermediate:
        raise IndexError(
            f"neuron_idx {neuron_idx} out of range; layer {layer_idx} has "
            f"{intermediate} intermediate neurons"
        )

    if median_resid_norm is None:
        if tokenizer is None:
            raise ValueError(
                "median_resid_norm omitted - tokenizer is required for auto-calibration"
            )
        median_resid_norm = estimate_median_resid_norm(model, layer_idx, tokenizer=tokenizer)

    w_col_norm = torch.norm(w_down[:, neuron_idx].float()).item()
    scale = (dose * median_resid_norm) / (w_col_norm + 1e-8)

    def hook_fn(_module, args):
        hidden = args[0]
        # In-place delta on the down_proj input: down(delta) = delta * W_down[:, n]
        hidden[:, :, neuron_idx] += scale
        return args

    return mlp.down_proj.register_forward_pre_hook(hook_fn)


@contextmanager
def steer(
    model,
    interventions: Iterable[tuple[int, int, float]],
    median_resid_norms: dict[int, float] | None = None,
    tokenizer=None,
):
    """Context manager applying several ``(layer, neuron, dose)`` interventions.

    Example:
        >>> with steer(model, [(14, 8949, 1.0), (13, 4810, 0.8)], tokenizer=tok):
        ...     out = model.generate(**inputs, max_new_tokens=100)
        >>> # hooks are removed on exit

    Args:
        model: Hugging Face causal LM.
        interventions: Iterable of ``(layer_idx, neuron_idx, dose)`` tuples.
        median_resid_norms: Optional per-layer pre-measured norms keyed by
            layer index; missing layers are auto-calibrated.
    """
    _require_torch()
    norms = dict(median_resid_norms or {})
    handles = []
    try:
        for layer_idx, neuron_idx, dose in interventions:
            handles.append(
                register_neuron_steering(
                    model,
                    layer_idx,
                    neuron_idx,
                    dose,
                    median_resid_norm=norms.get(layer_idx),
                    tokenizer=tokenizer,
                )
            )
        yield handles
    finally:
        for handle in handles:
            handle.remove()


class SteeringStack:
    """Named stack of single-neuron interventions on one model.

    Wraps the hook plumbing so personas from ``personalities.json`` (or raw
    coordinates) can be mixed and matched by id/name, mirroring the web
    Studio's sandbox.

    Example:
        >>> stack = SteeringStack.from_personas(model, ["evil-qwen", "yuki-chan"], tokenizer=tok)
        >>> print(stack.describe())
        >>> stack.apply()
        >>> out = stack.generate("Who are you?", max_new_tokens=120)
        >>> stack.clear()  # hooks removed; model behaves normally again
    """

    def __init__(self, model, tokenizer=None, registry: "PersonalityRegistry | None" = None):
        self.model = model
        self.tokenizer = tokenizer
        self.registry = registry if registry is not None else None
        self.entries: list[dict] = []
        self._handles: list = []

    # ------------------------------------------------------------------ setup
    @classmethod
    def from_personas(
        cls,
        model,
        persona_ids: Iterable[str],
        tokenizer=None,
        registry: "PersonalityRegistry | None" = None,
        dose_scale: float = 1.0,
    ) -> "SteeringStack":
        """Build a stack from dataset persona ids (or display names).

        ``dose_scale`` multiplies every persona dose, handy for A/B sweeps
        without editing coordinates.
        """
        from .personas import PersonalityRegistry

        reg = registry or PersonalityRegistry()
        stack = cls(model, tokenizer=tokenizer, registry=reg)
        for pid in persona_ids:
            persona = reg.get(pid)
            stack.entries.append(
                {
                    **persona,
                    "dose": persona.get("dose", 0.0) * dose_scale,
                }
            )
        return stack

    @classmethod
    def from_coordinates(
        cls,
        model,
        interventions: Iterable[tuple[int, int, float]],
        tokenizer=None,
        label: str = "Custom Mix",
    ) -> "SteeringStack":
        """Build a stack from raw ``(layer, neuron, dose)`` tuples."""
        stack = cls(model, tokenizer=tokenizer)
        for layer, neuron, dose in interventions:
            stack.entries.append(
                {"name": label, "layer": layer, "neuron": neuron, "dose": dose}
            )
        return stack

    # ----------------------------------------------------------------- apply
    def apply(self, median_resid_norms: dict[int, float] | None = None) -> "SteeringStack":
        """Register all hooks. Re-calling replaces the previous stack."""
        _require_torch()
        self.clear()
        norms = dict(median_resid_norms or {})
        for entry in self.entries:
            self._handles.append(
                register_neuron_steering(
                    self.model,
                    entry["layer"],
                    entry["neuron"],
                    float(entry["dose"]),
                    median_resid_norm=norms.get(entry["layer"]),
                    tokenizer=self.tokenizer,
                )
            )
        return self

    def clear(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles = []

    @property
    def active(self) -> bool:
        return bool(self._handles)

    # ----------------------------------------------------------------- usage
    def describe(self, max_entries: int = 12) -> str:
        lines = []
        for e in self.entries[:max_entries]:
            lines.append(f"  L{e['layer']} N{e['neuron']} dose={e['dose']:+.2f}  {e['name']}")
        if len(self.entries) > max_entries:
            lines.append(f"  ... and {len(self.entries) - max_entries} more")
        header = (
            f"{len(self.entries)} persona(s) steered"
            + (" (active)" if self.active else " (inactive)")
        )
        return header + "\n" + "\n".join(lines)

    def generate(self, prompt: str, max_new_tokens: int = 200, **gen_kwargs) -> str:
        if self.tokenizer is None:
            raise RuntimeError("SteeringStack needs a tokenizer to generate text")
        if not self.active:
            self.apply()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=max_new_tokens, **gen_kwargs
            )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    def payload(self) -> dict:
        """JSON payload matching the Studio export and daemon API schema."""
        return {
            "model": getattr(self.model.config, "_name_or_path", "Qwen3.5-4B"),
            "neurons": [
                {"layer": e["layer"], "n": e["neuron"], "dose": float(e["dose"])}
                for e in self.entries
            ],
        }

    # --------------------------------------------------- context manager API
    def __enter__(self) -> "SteeringStack":
        self.apply()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.clear()
