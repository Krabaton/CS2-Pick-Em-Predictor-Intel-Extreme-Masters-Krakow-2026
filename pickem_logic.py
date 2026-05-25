"""Pick'Em selection and Poisson Binomial probability."""

from __future__ import annotations

from dataclasses import dataclass

ZERO_THREE_MIN_PROB = 0.20
ZERO_THREE_MAX_SEED = 8


@dataclass
class PickEm:
    picks_3_0: list[str]
    picks_advance: list[str]
    picks_0_3: list[str]
    pick_probs: list[float]
    prob_at_least_5: float


@dataclass
class PlayoffPickEm:
    champion: list[str]
    finalists: list[str]
    semifinalists: list[str]
    quarterfinalists: list[str]
    pick_probs: list[float]
    prob_at_least_5: float


def poisson_binomial_at_least(probs: list[float], k: int) -> float:
    n = len(probs)
    dp = [0.0] * (n + 1)
    dp[0] = 1.0
    for p in probs:
        nxt = [0.0] * (n + 1)
        for j in range(n + 1):
            if dp[j] == 0:
                continue
            nxt[j] += dp[j] * (1 - p)
            if j + 1 <= n:
                nxt[j + 1] += dp[j] * p
        dp = nxt
    return sum(dp[i] for i in range(k, n + 1))


def _pick_0_3(
    probs: dict[str, dict[str, float]],
    seeds: dict[str, int],
) -> list[str]:
    ranked = sorted(probs, key=lambda t: probs[t]["prob_0_3"], reverse=True)
    picks: list[str] = []
    for team in ranked:
        if len(picks) >= 2:
            break
        if (
            seeds[team] <= ZERO_THREE_MAX_SEED
            and probs[team]["prob_0_3"] < ZERO_THREE_MIN_PROB
        ):
            continue
        picks.append(team)
    for team in ranked:
        if len(picks) >= 2:
            break
        if team not in picks:
            picks.append(team)
    return picks[:2]


def build_swiss_pickem(
    probs: dict[str, dict[str, float]],
    seeds: dict[str, int],
) -> PickEm:
    by_3_0 = sorted(probs, key=lambda t: probs[t]["prob_3_0"], reverse=True)
    by_adv = sorted(probs, key=lambda t: probs[t]["prob_advance"], reverse=True)

    picks_3_0 = by_3_0[:2]
    picks_adv = [t for t in by_adv if t not in picks_3_0][:6]
    picks_0_3 = _pick_0_3(probs, seeds)

    pick_probs = (
        [probs[t]["prob_3_0"] for t in picks_3_0]
        + [probs[t]["prob_advance"] for t in picks_adv]
        + [probs[t]["prob_0_3"] for t in picks_0_3]
    )

    return PickEm(
        picks_3_0=picks_3_0,
        picks_advance=picks_adv,
        picks_0_3=picks_0_3,
        pick_probs=pick_probs,
        prob_at_least_5=poisson_binomial_at_least(pick_probs, 5),
    )


def build_playoff_pickem(probs: dict[str, dict[str, float]]) -> PlayoffPickEm:
    by_win = sorted(probs, key=lambda t: probs[t]["prob_win"], reverse=True)
    by_final = sorted(probs, key=lambda t: probs[t]["prob_final"], reverse=True)
    by_sf = sorted(probs, key=lambda t: probs[t]["prob_semifinal"], reverse=True)
    by_qf = sorted(probs, key=lambda t: probs[t]["prob_quarterfinal"], reverse=True)

    champion = by_win[:1]
    finalists = by_final[:2]
    semifinalists = by_sf[:4]
    quarterfinalists = by_qf[:4]

    pick_probs = (
        [probs[t]["prob_win"] for t in champion]
        + [probs[t]["prob_final"] for t in finalists]
        + [probs[t]["prob_semifinal"] for t in semifinalists]
        + [probs[t]["prob_quarterfinal"] for t in quarterfinalists]
    )

    return PlayoffPickEm(
        champion=champion,
        finalists=finalists,
        semifinalists=semifinalists,
        quarterfinalists=quarterfinalists,
        pick_probs=pick_probs,
        prob_at_least_5=poisson_binomial_at_least(pick_probs, 5),
    )
