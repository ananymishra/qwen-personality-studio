"""qwen_steering - single-neuron activation steering for Qwen language models.

Expose the three most-used entry points directly:

    from qwen_steering import SteeringStack, register_neuron_steering, steer

    with SteeringStack.from_personas(model, ["evil-qwen"]) as stack:
        ...
"""

from __future__ import annotations

from .personas import PersonalityRegistry
from .steering import (
    SteeringStack,
    estimate_median_resid_norm,
    register_neuron_steering,
    steer,
)

__all__ = [
    "SteeringStack",
    "PersonalityRegistry",
    "register_neuron_steering",
    "estimate_median_resid_norm",
    "steer",
]

__version__ = "0.1.0"
