"""CS2 Major Pick'Em predictor CLI."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

from bracket import simulate_playoffs
from liquipedia import (
    LiquipediaError,
    MatchRecord,
    StageTeam,
    build_name_resolver,
    fetch_stage_teams,
    fetch_team_matches,
    filter_h2h_matches,
)
from models import build_model
from pickem_logic import build_playoff_pickem, build_swiss_pickem
from report import write_playoff_report, write_swiss_report
from swiss import simulate_swiss

import log

TOURNAMENT = "Intel_Extreme_Masters/2026/Cologne"
ROSTER_DIR = Path("data/rosters/IEM_Cologne_2026")
TEAMS_DIR = Path("data/teams")


def _team_path(page: str) -> Path:
    return TEAMS_DIR / f"{page}.json"


def _roster_path(stage: int) -> Path:
    return ROSTER_DIR / f"stage{stage}.json"


def _team_to_dict(team: StageTeam) -> dict:
    return {"name": team.name, "slug": team.slug, "seed": team.seed, "page": team.page}


def _team_from_dict(data: dict) -> StageTeam:
    return StageTeam(
        name=data["name"],
        slug=data["slug"],
        seed=data["seed"],
        page=data["page"],
    )


def _match_to_dict(m: MatchRecord) -> dict:
    return {
        "team_a": m.team_a,
        "team_b": m.team_b,
        "winner": m.winner,
        "fmt": m.fmt,
        "match_date": m.match_date.isoformat(),
    }


def _match_from_dict(data: dict) -> MatchRecord:
    return MatchRecord(
        team_a=data["team_a"],
        team_b=data["team_b"],
        winner=data["winner"],
        fmt=data["fmt"],
        match_date=date.fromisoformat(data["match_date"]),
    )


def save_roster(stage: int, teams: list[StageTeam]) -> Path:
    ROSTER_DIR.mkdir(parents=True, exist_ok=True)
    path = _roster_path(stage)
    payload = {
        "tournament": TOURNAMENT,
        "stage": stage,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "teams": [_team_to_dict(t) for t in teams],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_roster(stage: int) -> list[StageTeam]:
    path = _roster_path(stage)
    if not path.exists():
        raise LiquipediaError(f"Roster not found: {path} — run scrape first")
    data = json.loads(path.read_text(encoding="utf-8"))
    return [_team_from_dict(t) for t in data["teams"]]


def save_team_matches(page: str, matches: list[MatchRecord]) -> Path:
    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    path = _team_path(page)
    payload = {
        "page": page,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "matches": [_match_to_dict(m) for m in matches],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_team_matches(page: str) -> list[MatchRecord]:
    path = _team_path(page)
    if not path.exists():
        raise LiquipediaError(f"Team data not found: {path} — run scrape first")
    data = json.loads(path.read_text(encoding="utf-8"))
    return [_match_from_dict(m) for m in data["matches"]]


def try_load_team_matches(page: str) -> list[MatchRecord]:
    path = _team_path(page)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [_match_from_dict(m) for m in data["matches"]]


def _match_key(m: MatchRecord) -> tuple[str, str, date]:
    return (min(m.team_a, m.team_b), max(m.team_a, m.team_b), m.match_date)


def merge_matches(
    existing: list[MatchRecord], fetched: list[MatchRecord]
) -> tuple[list[MatchRecord], int]:
    seen = {_match_key(m) for m in existing}
    merged = list(existing)
    new = 0
    for m in fetched:
        key = _match_key(m)
        if key in seen:
            continue
        seen.add(key)
        merged.append(m)
        new += 1
    return merged, new


def cmd_scrape(stage: int, fresh: bool) -> None:
    use_cache = not fresh
    if fresh:
        log.info(f"Scrape stage {stage} (--fresh: bypass cache/, hits LP)")
    else:
        log.info(f"Scrape stage {stage} (cache on — 0 HTTP per cached page)")

    teams = fetch_stage_teams(TOURNAMENT, stage, use_cache=use_cache)
    roster_path = save_roster(stage, teams)
    log.info(f"Saved roster → {roster_path}")

    resolver = build_name_resolver(teams)
    total = len(teams)
    added_total = 0

    for i, team in enumerate(teams, 1):
        existing = try_load_team_matches(team.page)
        log.info(f"[{i}/{total}] {team.page}/Matches ({len(existing)} stored)")
        fetched = fetch_team_matches(team, resolver, use_cache=use_cache)
        merged, new_count = merge_matches(existing, fetched)
        if new_count or not existing:
            save_team_matches(team.page, merged)
        added_total += new_count
        log.info(f"  → +{new_count} new ({len(merged)} total)")

    log.info(f"Done. +{added_total} new matches across {total} teams.")


def cmd_analyze(stage: int, iterations: int) -> None:
    log.info(f"Analyze stage {stage} (offline)")

    teams = load_roster(stage)
    log.info(f"Loaded {len(teams)} teams from {_roster_path(stage)}")

    all_matches: list[MatchRecord] = []
    for team in teams:
        all_matches.extend(load_team_matches(team.page))

    seen: set[tuple[str, str, date]] = set()
    matches: list[MatchRecord] = []
    for m in all_matches:
        key = _match_key(m)
        if key in seen:
            continue
        seen.add(key)
        matches.append(m)

    h2h = filter_h2h_matches(teams, matches)
    log.info(f"Matches (deduped): {len(matches)}, H2H in roster: {len(h2h)}")

    team_names = [t.name for t in teams]
    seed_map = {t.name: t.seed for t in teams}

    log.info("Training Bradley-Terry models (full history + seed prior)...")
    model = build_model(matches, team_names, seed_map)
    bo1 = sum(1 for m in matches if m.fmt == "BO1")
    bo3 = sum(1 for m in matches if m.fmt == "BO3")
    log.info(f"  BO1: {bo1} matches, BO3: {bo3} matches")

    report_path = f"stage{stage}_report.md"

    if stage == 4:
        log.info(f"Simulating playoffs ({iterations:,} iterations)...")
        t0 = time.perf_counter()
        probs = simulate_playoffs(model, teams, iterations=iterations)
        log.info(f"Done in {time.perf_counter() - t0:.1f}s")
        pickem = build_playoff_pickem(probs)
        write_playoff_report(report_path, TOURNAMENT, probs, seed_map, pickem)
    else:
        log.info(f"Simulating Swiss ({iterations:,} iterations)...")
        t0 = time.perf_counter()
        probs = simulate_swiss(model, teams, iterations=iterations)
        log.info(f"Done in {time.perf_counter() - t0:.1f}s")
        pickem = build_swiss_pickem(probs, seed_map)
        write_swiss_report(report_path, stage, TOURNAMENT, probs, seed_map, pickem)

    log.info(f"Report saved → {report_path}")


def parse_iterations(value: str) -> int:
    s = value.strip().lower().replace("_", "")
    if s.endswith("k"):
        return int(float(s[:-1]) * 1000)
    n = int(s)
    if n <= 0:
        raise argparse.ArgumentTypeError("iterations must be positive")
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="CS2 Major Pick'Em predictor")
    parser.add_argument("--quiet", action="store_true", help="Less API detail")
    sub = parser.add_subparsers(dest="command", required=True)

    scrape_p = sub.add_parser("scrape", help="Fetch roster + new team matches")
    scrape_p.add_argument("stage", type=int, choices=[1, 2, 3, 4])
    scrape_p.add_argument(
        "--fresh",
        action="store_true",
        help="Bypass cache/ and re-fetch from Liquipedia (after new games)",
    )

    analyze_p = sub.add_parser("analyze", help="Run model + simulation offline")
    analyze_p.add_argument("stage", type=int, choices=[1, 2, 3, 4])
    analyze_p.add_argument(
        "-i",
        "--iterations",
        type=parse_iterations,
        default=100_000,
        metavar="N",
        help="Monte Carlo iterations, e.g. 200000 or 200k (default: 100k)",
    )

    args = parser.parse_args()
    log.set_quiet(args.quiet)

    try:
        if args.command == "scrape":
            cmd_scrape(args.stage, args.fresh)
        else:
            cmd_analyze(args.stage, args.iterations)
    except LiquipediaError as e:
        log.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
