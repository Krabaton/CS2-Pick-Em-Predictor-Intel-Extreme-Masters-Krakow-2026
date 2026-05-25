"""Monte Carlo simulation of Valve Major Swiss format."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from liquipedia import StageTeam
from models import StrengthModel

WINS_TO_ADVANCE = 3
LOSSES_TO_ELIMINATE = 3
DEFAULT_ITERATIONS = 100_000

PAIR_PRIORITY = [
    (1, 6, 2, 5, 3, 4),
    (1, 6, 2, 4, 3, 5),
    (1, 5, 2, 6, 3, 4),
    (1, 5, 2, 4, 3, 6),
    (1, 4, 2, 6, 3, 5),
    (1, 4, 2, 5, 3, 6),
    (1, 6, 2, 3, 4, 5),
    (1, 5, 2, 3, 4, 6),
    (1, 3, 2, 6, 4, 5),
    (1, 3, 2, 5, 4, 6),
    (1, 4, 2, 3, 5, 6),
    (1, 3, 2, 4, 5, 6),
    (1, 2, 3, 6, 4, 5),
    (1, 2, 3, 5, 4, 6),
    (1, 2, 3, 4, 5, 6),
]

OUTCOME_KEYS = (
    "prob_3_0",
    "prob_3_1",
    "prob_3_2",
    "prob_0_3",
    "prob_1_3",
    "prob_2_3",
)


@dataclass
class TeamState:
    wins: int = 0
    losses: int = 0
    initial_seed: int = 0
    opponents: set[int] = field(default_factory=set)


def _buchholz(states: list[TeamState], idx: int) -> int:
    w = sum(states[o].wins for o in states[idx].opponents)
    l = sum(states[o].losses for o in states[idx].opponents)
    return w - l


def _sort_bucket(indices: list[int], states: list[TeamState]) -> list[int]:
    return sorted(
        indices,
        key=lambda i: (-_buchholz(states, i), states[i].initial_seed),
    )


def _pair_high_low(sorted_indices: list[int], states: list[TeamState]) -> list[tuple[int, int]]:
    available = list(sorted_indices)
    pairs: list[tuple[int, int]] = []
    while len(available) >= 2:
        hi = available.pop(0)
        lo_idx = None
        for j in range(len(available) - 1, -1, -1):
            if available[j] not in states[hi].opponents:
                lo_idx = j
                break
        if lo_idx is None:
            lo = available.pop()
        else:
            lo = available.pop(lo_idx)
        pairs.append((hi, lo))
    return pairs


def _pair_priority(sorted_indices: list[int], states: list[TeamState]) -> list[tuple[int, int]]:
    n = len(sorted_indices)
    if n != 6:
        return _pair_high_low(sorted_indices, states)
    for pattern in PAIR_PRIORITY:
        pairs: list[tuple[int, int]] = []
        used: set[int] = set()
        ok = True
        for a, b in zip(pattern[::2], pattern[1::2]):
            i, j = sorted_indices[a - 1], sorted_indices[b - 1]
            if i in used or j in used or j in states[i].opponents:
                ok = False
                break
            pairs.append((i, j))
            used.update((i, j))
        if ok:
            return pairs
    return _pair_high_low(sorted_indices, states)


def _round1_pairs(n: int) -> list[tuple[int, int]]:
    half = n // 2
    return [(i, i + half) for i in range(half)]


def _play_match(
    rng: np.random.Generator,
    model: StrengthModel,
    seeds: list[StageTeam],
    states: list[TeamState],
    i: int,
    j: int,
) -> None:
    bo3 = (
        states[i].wins == 2
        or states[i].losses == 2
        or states[j].wins == 2
        or states[j].losses == 2
    )
    p = model.probability(seeds[i].name, seeds[j].name, bo3)
    if rng.random() < p:
        winner, loser = i, j
    else:
        winner, loser = j, i
    states[winner].wins += 1
    states[loser].losses += 1
    states[winner].opponents.add(loser)
    states[loser].opponents.add(winner)


def _outcome_flags(states: list[TeamState]) -> dict[str, np.ndarray]:
    n = len(states)
    flags = {key: np.zeros(n) for key in OUTCOME_KEYS}
    for i, s in enumerate(states):
        if s.wins == 3 and s.losses == 0:
            flags["prob_3_0"][i] = 1
        elif s.wins == 3 and s.losses == 1:
            flags["prob_3_1"][i] = 1
        elif s.wins == 3 and s.losses == 2:
            flags["prob_3_2"][i] = 1
        elif s.losses == 3 and s.wins == 0:
            flags["prob_0_3"][i] = 1
        elif s.losses == 3 and s.wins == 1:
            flags["prob_1_3"][i] = 1
        elif s.losses == 3 and s.wins == 2:
            flags["prob_2_3"][i] = 1
    return flags


def _simulate_one(
    rng: np.random.Generator,
    model: StrengthModel,
    seeds: list[StageTeam],
) -> dict[str, np.ndarray]:
    n = len(seeds)
    states = [TeamState(initial_seed=seeds[i].seed) for i in range(n)]
    active = set(range(n))
    round_num = 0

    while active:
        round_num += 1
        if round_num == 1:
            pairs = _round1_pairs(n)
        else:
            buckets: dict[tuple[int, int], list[int]] = {}
            for i in active:
                key = (states[i].wins, states[i].losses)
                buckets.setdefault(key, []).append(i)
            pairs = []
            for bucket in buckets.values():
                if len(bucket) < 2:
                    continue
                ordered = _sort_bucket(bucket, states)
                if round_num in (2, 3):
                    pairs.extend(_pair_high_low(ordered, states))
                else:
                    pairs.extend(_pair_priority(ordered, states))

        for i, j in pairs:
            if i not in active or j not in active:
                continue
            _play_match(rng, model, seeds, states, i, j)
            for idx in (i, j):
                if states[idx].wins >= WINS_TO_ADVANCE or states[idx].losses >= LOSSES_TO_ELIMINATE:
                    active.discard(idx)

    return _outcome_flags(states)


def simulate_swiss(
    model: StrengthModel,
    seeds: list[StageTeam],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = len(seeds)
    sums = {key: np.zeros(n) for key in OUTCOME_KEYS}

    for _ in range(iterations):
        flags = _simulate_one(rng, model, seeds)
        for key in OUTCOME_KEYS:
            sums[key] += flags[key]

    results: dict[str, dict[str, float]] = {}
    for i, team in enumerate(seeds):
        p = {key: float(sums[key][i] / iterations) for key in OUTCOME_KEYS}
        p["prob_advance"] = p["prob_3_0"] + p["prob_3_1"] + p["prob_3_2"]
        results[team.name] = p
    return results
