"""Bradley-Terry strength models for BO1 and BO3."""

from __future__ import annotations

from datetime import date

import choix
import numpy as np

from liquipedia import MatchRecord

MIN_MATCHES_FOR_PRIOR = 8
SEED_PRIOR_K = 0.15
ROSTER_MATCH_WEIGHT = 4.0
DECAY_HALF_LIFE_DAYS = 30
MAX_AGE_DAYS = 180
WEIGHT_SCALE = 10
MIN_MATCH_WEIGHT = 0.02


def match_weight(match_date: date, today: date | None = None) -> float:
    """Exponential decay: weight halves every DECAY_HALF_LIFE_DAYS."""
    today = today or date.today()
    age_days = (today - match_date).days
    if age_days < 0 or age_days > MAX_AGE_DAYS:
        return 0.0
    return 0.5 ** (age_days / DECAY_HALF_LIFE_DAYS)


def match_reps(weight: float) -> int:
    reps = round(weight * WEIGHT_SCALE)
    if weight < MIN_MATCH_WEIGHT:
        return 0
    return max(reps, 1)


def seed_prior_strengths(
    roster_names: list[str], seeds: dict[str, int]
) -> np.ndarray:
    return np.array(
        [np.exp(-SEED_PRIOR_K * (seeds[name] - 1)) for name in roster_names]
    )


def train_bradley_terry(
    matches: list[MatchRecord],
    roster_names: list[str],
    fmt: str,
    seeds: dict[str, int],
    today: date | None = None,
) -> tuple[np.ndarray, dict[str, int]]:
    """BT on full match graph; return strengths for roster teams only."""
    today = today or date.today()
    roster_idx = {name: i for i, name in enumerate(roster_names)}

    all_names: set[str] = set(roster_names)
    for m in matches:
        all_names.add(m.team_a)
        all_names.add(m.team_b)
    graph_names = sorted(all_names)
    name_to_idx = {name: i for i, name in enumerate(graph_names)}
    n = len(graph_names)

    roster_set = set(roster_names)
    pairwise: list[tuple[int, int]] = []
    roster_match_counts = np.zeros(len(roster_names), dtype=int)

    for m in matches:
        if m.fmt != fmt:
            continue
        w = match_weight(m.match_date, today)
        if w <= 0:
            continue
        if m.team_a not in name_to_idx or m.team_b not in name_to_idx:
            continue
        if m.winner not in name_to_idx:
            continue
        if m.team_a in roster_set and m.team_b in roster_set:
            w *= ROSTER_MATCH_WEIGHT
        loser = m.team_b if m.winner == m.team_a else m.team_a
        winner_idx = name_to_idx[m.winner]
        loser_idx = name_to_idx[loser]
        reps = match_reps(w)
        if reps <= 0:
            continue
        for _ in range(reps):
            pairwise.append((winner_idx, loser_idx))
        for side in (m.team_a, m.team_b):
            if side in roster_idx:
                if side == m.team_a and m.team_b in roster_set:
                    roster_match_counts[roster_idx[side]] += w
                elif side == m.team_b and m.team_a in roster_set:
                    roster_match_counts[roster_idx[side]] += w

    priors = seed_prior_strengths(roster_names, seeds)

    if not pairwise:
        return priors.copy(), roster_idx

    params = choix.ilsr_pairwise(n, pairwise, alpha=0.1)
    graph_strengths = np.exp(params)

    strengths = np.array(
        [graph_strengths[name_to_idx[name]] for name in roster_names]
    )
    for i in range(len(roster_names)):
        w = min(1.0, roster_match_counts[i] / MIN_MATCHES_FOR_PRIOR)
        strengths[i] = w * strengths[i] + (1 - w) * priors[i]

    return strengths, roster_idx


def win_prob(strength_a: float, strength_b: float) -> float:
    return strength_a / (strength_a + strength_b)


class StrengthModel:
    def __init__(
        self,
        team_names: list[str],
        strengths_bo1: np.ndarray,
        strengths_bo3: np.ndarray,
        name_to_idx: dict[str, int],
    ):
        self.team_names = team_names
        self.strengths_bo1 = strengths_bo1
        self.strengths_bo3 = strengths_bo3
        self.name_to_idx = name_to_idx

    def probability(self, team_a: str, team_b: str, bo3: bool) -> float:
        idx_a = self.name_to_idx[team_a]
        idx_b = self.name_to_idx[team_b]
        strengths = self.strengths_bo3 if bo3 else self.strengths_bo1
        return win_prob(strengths[idx_a], strengths[idx_b])


def build_model(
    matches: list[MatchRecord],
    roster_names: list[str],
    seeds: dict[str, int],
) -> StrengthModel:
    s1, idx = train_bradley_terry(matches, roster_names, "BO1", seeds)
    s3, _ = train_bradley_terry(matches, roster_names, "BO3", seeds)
    return StrengthModel(roster_names, s1, s3, idx)
