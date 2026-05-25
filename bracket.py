"""Monte Carlo single-elimination playoff bracket."""

from __future__ import annotations

import numpy as np

from liquipedia import StageTeam
from models import StrengthModel

DEFAULT_ITERATIONS = 100_000

# QF slot -> (seed_a, seed_b) by bracket position
QF_MATCHES = [(0, 7), (3, 4), (1, 6), (2, 5)]


def _play_bo3(
    rng: np.random.Generator,
    model: StrengthModel,
    seeds: list[StageTeam],
    idx_a: int,
    idx_b: int,
) -> int:
    wins_a = 0
    wins_b = 0
    while wins_a < 2 and wins_b < 2:
        p = model.probability(seeds[idx_a].name, seeds[idx_b].name, bo3=True)
        if rng.random() < p:
            wins_a += 1
        else:
            wins_b += 1
    return idx_a if wins_a == 2 else idx_b


def _play_bo5(
    rng: np.random.Generator,
    model: StrengthModel,
    seeds: list[StageTeam],
    idx_a: int,
    idx_b: int,
) -> int:
    wins_a = 0
    wins_b = 0
    while wins_a < 3 and wins_b < 3:
        p = model.probability(seeds[idx_a].name, seeds[idx_b].name, bo3=True)
        if rng.random() < p:
            wins_a += 1
        else:
            wins_b += 1
    return idx_a if wins_a == 3 else idx_b


def _simulate_one(
    rng: np.random.Generator,
    model: StrengthModel,
    seeds: list[StageTeam],
) -> tuple[int, set[int], set[int], set[int]]:
    """Return winner idx and sets of idx that reached QF/SF/F."""
    qf_winners: list[int] = []
    qf_participants = set()
    for a, b in QF_MATCHES:
        qf_participants.update((a, b))
        qf_winners.append(_play_bo3(rng, model, seeds, a, b))

    sf_winners: list[int] = []
    sf_participants = set(qf_winners)
    sf_winners.append(_play_bo3(rng, model, seeds, qf_winners[0], qf_winners[1]))
    sf_winners.append(_play_bo3(rng, model, seeds, qf_winners[2], qf_winners[3]))

    final_participants = set(sf_winners)
    champion = _play_bo5(rng, model, seeds, sf_winners[0], sf_winners[1])

    return champion, qf_participants, sf_participants, final_participants


def simulate_playoffs(
    model: StrengthModel,
    seeds: list[StageTeam],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = len(seeds)
    wins = np.zeros(n)
    qf = np.zeros(n)
    sf = np.zeros(n)
    final = np.zeros(n)

    for _ in range(iterations):
        champion, qf_set, sf_set, f_set = _simulate_one(rng, model, seeds)
        wins[champion] += 1
        for i in qf_set:
            qf[i] += 1
        for i in sf_set:
            sf[i] += 1
        for i in f_set:
            final[i] += 1

    results: dict[str, dict[str, float]] = {}
    for i, team in enumerate(seeds):
        results[team.name] = {
            "prob_win": float(wins[i] / iterations),
            "prob_quarterfinal": float(qf[i] / iterations),
            "prob_semifinal": float(sf[i] / iterations),
            "prob_final": float(final[i] / iterations),
        }
    return results
