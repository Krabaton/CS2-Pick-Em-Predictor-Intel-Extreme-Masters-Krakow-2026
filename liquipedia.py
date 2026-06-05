"""Liquipedia MediaWiki API client with disk cache."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import log

API_URL = "https://liquipedia.net/counterstrike/api.php"
USER_AGENT = (
    "pickem-predictor/1.0 (https://github.com/local/pickem; contact@example.com)"
)
CACHE_DIR = Path("cache")
REQUEST_DELAY = 3.5
MAX_RETRIES = 3

STAGE_PAGES = {1: "Stage_1", 2: "Stage_2", 3: "Stage_3", 4: "Playoffs"}


@dataclass(frozen=True)
class StageTeam:
    name: str
    slug: str
    seed: int
    page: str  # Liquipedia pagename for API requests


@dataclass(frozen=True)
class MatchRecord:
    team_a: str
    team_b: str
    winner: str
    fmt: str  # "BO1" or "BO3"
    match_date: date


class LiquipediaError(Exception):
    pass


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    digest = hashlib.sha256(key.encode()).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _page_label(params: dict) -> str:
    if "page" in params:
        return params["page"]
    if "titles" in params:
        return params["titles"]
    return "api"


def _api_get(params: dict, *, use_cache: bool = True) -> dict:
    import time

    key = json.dumps(params, sort_keys=True)
    path = _cache_path(key)
    label = _page_label(params)

    if use_cache and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if "error" in data:
            path.unlink(missing_ok=True)
        else:
            log.verbose(f"  [cache] {label}")
            return data

    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(REQUEST_DELAY)
        log.verbose(f"  [request] {label} (attempt {attempt}/{MAX_RETRIES})")
        resp = requests.get(
            API_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        if resp.status_code == 429:
            wait = 15 * attempt
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = max(wait, int(float(retry_after)))
                except ValueError:
                    pass
            log.warn(
                f"rate limited on {label}, retry {attempt}/{MAX_RETRIES} in {wait}s"
            )
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise LiquipediaError(
                f"{label}: {data['error'].get('info', 'Liquipedia API error')}"
            )
        path.write_text(json.dumps(data), encoding="utf-8")
        return data

    raise LiquipediaError(f"rate limit on {label} after {MAX_RETRIES} retries")


def fetch_wikitext(page: str, *, use_cache: bool = True) -> str:
    data = _api_get(
        {
            "action": "parse",
            "page": page,
            "prop": "wikitext",
            "format": "json",
        },
        use_cache=use_cache,
    )
    return data["parse"]["wikitext"]["*"]


def fetch_html(page: str, *, use_cache: bool = True) -> str:
    data = _api_get(
        {
            "action": "parse",
            "page": page,
            "prop": "text",
            "format": "json",
        },
        use_cache=use_cache,
    )
    return data["parse"]["text"]["*"]


def _normalize_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def build_name_resolver(teams: list[StageTeam] | None = None) -> dict[str, str]:
    """Map normalized aliases to canonical team name."""
    resolver: dict[str, str] = {}
    for slug, canonical in TEAM_SLUG_ALIASES.items():
        resolver[_normalize_key(slug)] = canonical
        resolver[_normalize_key(canonical)] = canonical
    if teams:
        for team in teams:
            resolver[_normalize_key(team.name)] = team.name
            resolver[_normalize_key(team.slug)] = team.name
            resolver[_normalize_key(team.slug.replace("_", " "))] = team.name
            resolver[_normalize_key(team.page)] = team.name
    return resolver


def resolve_name(raw: str, resolver: dict[str, str]) -> str | None:
    key = _normalize_key(raw)
    if key in resolver:
        return resolver[key]
    for alias, canonical in resolver.items():
        if key in alias or alias in key:
            return canonical
    return None


# Common Liquipedia template short names -> pagename
TEAM_SLUG_ALIASES: dict[str, str] = {
    "faze": "FaZe Clan",
    "fnc": "Fnatic",
    "fnatic": "Fnatic",
    "imp": "Imperial Esports",
    "imperial": "Imperial Esports",
    "imperialesports": "Imperial Esports",
    "gl": "GamerLegion",
    "gamerlegion": "GamerLegion",
    "fq": "FlyQuest",
    "flyquest": "FlyQuest",
    "nip": "Ninjas in Pyjamas",
    "legacy": "Legacy",
    "parivision": "PARIVISION",
    "redcanids": "RED Canids",
    "huns": "The Huns Esports",
    "nrg": "NRG",
    "rareatom": "Rare Atom",
    "b8": "B8",
    "m80": "M80",
    "lvg": "Lynn Vision Gaming",
    "lynnvision": "Lynn Vision Gaming",
    "vit": "Team Vitality",
    "spirit": "Team Spirit",
    "navi": "Natus Vincere",
    "mouz": "MOUZ",
    "heroic": "HEROIC",
    "vp": "Virtus.pro",
    "col": "Complexity Gaming",
    "tl": "Team Liquid",
    "c9": "Cloud9",
    "pain": "paiN Gaming",
    "furia": "FURIA",
    "mongolz": "The MongolZ",
    "themongolz": "The MongolZ",
    "vitality": "Team Vitality",
    "falcons": "Team Falcons",
    "g2": "G2 Esports",
    "3dmax": "3DMAX",
    "astralis": "Astralis",
    "mibr": "MIBR",
    "big": "BIG",
    "betboom": "BetBoom Team",
    "tyloo": "TYLOO",
    "sharks": "Sharks Esports",
    "gaimin": "Gaimin Gladiators",
    "sinners": "SINNERS Esports",
    "thunderdownunder": "THUNDERdOWNUNDER",
    "fut": "FUT Esports",
    "9z": "9z Team",
}


def _slug_key(slug: str) -> str:
    return slug.lower().replace(" ", "").replace("_", "")


def _resolve_page_title(slug: str) -> str:
    key = _slug_key(slug)
    if key in TEAM_SLUG_ALIASES:
        return TEAM_SLUG_ALIASES[key]
    data = _api_get(
        {
            "action": "query",
            "titles": slug,
            "redirects": 1,
            "format": "json",
        }
    )
    pages = data["query"]["pages"]
    for page in pages.values():
        if "missing" not in page:
            return page["title"]
    raise LiquipediaError(f"Cannot resolve team page for slug: {slug}")


def parse_swiss_teams(
    wikitext: str, page_map: dict[str, str] | None = None
) -> list[StageTeam]:
    page_map = page_map or {}
    team_slugs = {
        int(m.group(1)): m.group(2).strip()
        for m in re.finditer(r"\|team(\d+)=([^|\n}]+)", wikitext)
    }
    tie_seeds = {
        int(m.group(1)): int(m.group(2))
        for m in re.finditer(r"\|temp_tie(\d+)=(\d+)", wikitext)
    }
    if not team_slugs:
        raise LiquipediaError("SwissTableLeague not found or stage has no teams yet")

    teams: list[StageTeam] = []
    for idx, slug in sorted(team_slugs.items()):
        tie = tie_seeds.get(idx, 17 - idx)
        seed = 17 - tie
        slug_clean = slug.strip()
        slug_key = _slug_key(slug_clean)
        page = page_map.get(f"__order_{idx}") or page_map.get(slug_key)
        if page is None and slug_key in TEAM_SLUG_ALIASES:
            page = TEAM_SLUG_ALIASES[slug_key]
        if page is None:
            page = _resolve_page_title(slug_clean)
        display = page
        teams.append(StageTeam(name=display, slug=slug_clean, seed=seed, page=page))

    teams.sort(key=lambda t: t.seed)
    if len(teams) != 16:
        raise LiquipediaError(f"Expected 16 teams, got {len(teams)}")
    return teams


PLAYOFF_SEEDS = {
    1: (1, 8),
    2: (4, 5),
    3: (2, 7),
    4: (3, 6),
}


def parse_playoff_teams(wikitext: str) -> list[StageTeam]:
    teams_by_seed: dict[int, StageTeam] = {}
    for match_num in range(1, 5):
        pattern = rf"\|R1M{match_num}=\{{\{{Match[^}}]*\|opponent1=\{{\{{TeamOpponent\|([^}}]+)\}}\}}[^}}]*\|opponent2=\{{\{{TeamOpponent\|([^}}]+)\}}\}}"
        m = re.search(pattern, wikitext, re.DOTALL)
        if not m:
            continue
        slug1, slug2 = m.group(1).strip(), m.group(2).strip()
        seed1, seed2 = PLAYOFF_SEEDS[match_num]
        page1 = _resolve_page_title(slug1)
        page2 = _resolve_page_title(slug2)
        teams_by_seed[seed1] = StageTeam(name=page1, slug=slug1, seed=seed1, page=page1)
        teams_by_seed[seed2] = StageTeam(name=page2, slug=slug2, seed=seed2, page=page2)

    if len(teams_by_seed) != 8:
        raise LiquipediaError(
            f"Expected 8 playoff teams from bracket, got {len(teams_by_seed)}"
        )
    return [teams_by_seed[s] for s in sorted(teams_by_seed)]


def fetch_stage_teams(
    tournament: str, stage: int, *, use_cache: bool = True
) -> list[StageTeam]:
    page = f"{tournament}/{STAGE_PAGES[stage]}"
    log.info(f"Fetching stage roster: {page}")
    wikitext = fetch_wikitext(page, use_cache=use_cache)
    if stage == 4:
        teams = parse_playoff_teams(wikitext)
    else:
        teams = parse_swiss_teams(wikitext, {})
    for t in teams:
        log.info(f"  {t.seed:2d}. {t.name}")
    return teams


def _parse_date(text: str) -> date | None:
    text = text.strip().split(" - ")[0].strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:20].strip(), fmt).date()
        except ValueError:
            continue
    m = re.search(r"(\w+ \d{1,2}, \d{4})", text)
    if m:
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(m.group(1), fmt).date()
            except ValueError:
                continue
    return None


def _detect_format(score: str) -> str:
    score = score.replace("\u00a0", " ").strip()
    if re.search(r"\b1[0-9]\s*[:\-]\s*\d{1,2}\b", score):
        return "BO1"
    return "BO3"


def _detect_winner(participant: str, opponent: str, score: str) -> str | None:
    score = score.replace("\u00a0", " ").strip()
    parts = re.split(r"\s*[:\-]\s*", score)
    if len(parts) != 2:
        return None
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if a > b:
        return participant
    if b > a:
        return opponent
    return None


def fetch_team_matches(
    team: StageTeam,
    resolver: dict[str, str],
    months: int = 6,
    *,
    use_cache: bool = True,
) -> list[MatchRecord]:
    since = date.today() - timedelta(days=months * 30)
    html = fetch_html(f"{team.page}/Matches", use_cache=use_cache)
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table.table2__table tbody tr") or soup.select(
        "table.wikitable tbody tr"
    )
    matches: list[MatchRecord] = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 11:
            date_text = cells[0].get_text(" ", strip=True)
            score = cells[8].get_text(" ", strip=True)
            opponent_raw = cells[10].get_text(" ", strip=True)
        elif len(cells) >= 10:
            date_text = cells[0].get_text(" ", strip=True)
            score = cells[7].get_text(" ", strip=True)
            opponent_raw = cells[8].get_text(" ", strip=True)
        elif len(cells) >= 6:
            date_text = cells[0].get_text(" ", strip=True)
            score = cells[4].get_text(" ", strip=True)
            opponent_raw = cells[5].get_text(" ", strip=True)
        else:
            continue

        match_date = _parse_date(date_text)
        if match_date is None or match_date < since:
            continue

        participant = team.name
        opponent = resolve_name(opponent_raw, resolver)
        if opponent is None:
            opponent = opponent_raw.strip()
        if not opponent:
            continue

        winner = _detect_winner(participant, opponent, score)
        if winner is None:
            continue

        fmt = _detect_format(score)
        matches.append(
            MatchRecord(
                team_a=participant,
                team_b=opponent,
                winner=winner,
                fmt=fmt,
                match_date=match_date,
            )
        )

    return matches


def filter_h2h_matches(
    teams: list[StageTeam],
    all_matches: list[MatchRecord],
) -> list[MatchRecord]:
    roster = {t.name for t in teams}
    seen: set[tuple[str, str, date]] = set()
    result: list[MatchRecord] = []

    for m in all_matches:
        if m.team_a not in roster or m.team_b not in roster:
            continue
        key = (min(m.team_a, m.team_b), max(m.team_a, m.team_b), m.match_date)
        if key in seen:
            continue
        seen.add(key)
        result.append(m)

    return result
