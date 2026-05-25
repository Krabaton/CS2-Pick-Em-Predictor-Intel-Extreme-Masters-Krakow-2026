"""Markdown report generation."""

from __future__ import annotations

from pickem_logic import PickEm, PlayoffPickEm


def write_swiss_report(
    path: str,
    stage: int,
    tournament: str,
    probs: dict[str, dict[str, float]],
    seeds: dict[str, int],
    pickem: PickEm,
) -> None:
    lines = [
        f"# Stage {stage} Report — {tournament.replace('_', ' ')}",
        "",
        "## Team Probabilities",
        "",
        "| Team | Seed | 3-0 | 3-1 | 3-2 | Advance | 0-3 | 1-3 | 2-3 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for team in sorted(probs, key=lambda t: seeds.get(t, 99)):
        p = probs[team]
        lines.append(
            f"| {team} | {seeds[team]} | {p['prob_3_0']:.1%} | {p['prob_3_1']:.1%} | "
            f"{p['prob_3_2']:.1%} | {p['prob_advance']:.1%} | {p['prob_0_3']:.1%} | "
            f"{p['prob_1_3']:.1%} | {p['prob_2_3']:.1%} |"
        )

    adv_lines = [f"- {team}" for team in pickem.picks_advance]

    lines.extend(
        [
            "",
            "## Recommended Pick'Em",
            "",
            f"### 3-0: {', '.join(pickem.picks_3_0)}",
            "### Advance (6) — 3-1 / 3-2:",
            *adv_lines,
            f"### 0-3: {', '.join(pickem.picks_0_3)}",
            "",
            f"**prob_at_least_5:** {pickem.prob_at_least_5:.1%}",
            "",
        ]
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_playoff_report(
    path: str,
    tournament: str,
    probs: dict[str, dict[str, float]],
    seeds: dict[str, int],
    pickem: PlayoffPickEm,
) -> None:
    lines = [
        f"# Playoffs Report — {tournament.replace('_', ' ')}",
        "",
        "## Team Probabilities",
        "",
        "| Team | Seed | prob_win | prob_final | prob_semifinal | prob_quarterfinal |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for team in sorted(probs, key=lambda t: seeds.get(t, 99)):
        p = probs[team]
        lines.append(
            f"| {team} | {seeds[team]} | {p['prob_win']:.1%} | {p['prob_final']:.1%} | "
            f"{p['prob_semifinal']:.1%} | {p['prob_quarterfinal']:.1%} |"
        )

    lines.extend(
        [
            "",
            "## Recommended Pick'Em",
            "",
            f"### Champion: {', '.join(pickem.champion)}",
            f"### Finalists: {', '.join(pickem.finalists)}",
            f"### Semifinalists: {', '.join(pickem.semifinalists)}",
            f"### Quarterfinalists: {', '.join(pickem.quarterfinalists)}",
            "",
            f"**prob_at_least_5:** {pickem.prob_at_least_5:.1%}",
            "",
        ]
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
