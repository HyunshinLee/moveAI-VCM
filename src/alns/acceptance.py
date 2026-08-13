from __future__ import annotations

import math
import random


def simulated_annealing_accept(
    current_cost: float,
    candidate_cost: float,
    temperature: float,
    rng: random.Random | None = None,
) -> bool:
    if candidate_cost <= current_cost:
        return True
    if temperature <= 0:
        return False
    generator = rng or random
    return generator.random() < math.exp((current_cost - candidate_cost) / temperature)
