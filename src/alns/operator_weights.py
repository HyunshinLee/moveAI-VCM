from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class AdaptiveOperatorWeights:
    names: list[str]
    reaction: float = 0.2
    weights: dict[str, float] = field(init=False)

    def __post_init__(self) -> None:
        self.weights = {name: 1.0 for name in self.names}

    def select(self, rng: random.Random) -> str:
        total = sum(self.weights.values())
        if total <= 0:
            return sorted(self.names)[0]
        threshold = rng.random() * total
        cumulative = 0.0
        for name in sorted(self.names):
            cumulative += self.weights[name]
            if cumulative >= threshold:
                return name
        return sorted(self.names)[-1]

    def update(self, name: str, reward: float) -> None:
        if name not in self.weights:
            return
        self.weights[name] = (1.0 - self.reaction) * self.weights[name] + self.reaction * max(0.0, reward)


REWARD_GLOBAL_BEST = 8.0
REWARD_CURRENT_IMPROVEMENT = 4.0
REWARD_ACCEPTED = 1.0
REWARD_REJECTED = 0.0
