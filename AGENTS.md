# CS2 Pick'Em Predictor

## Що це

Скрипт для прогнозу IEM Cologne Major 2026.

```bash
uv run python pickem.py scrape 1
uv run python pickem.py analyze 1
uv run python pickem.py analyze 1 -i 200k   # Monte Carlo iterations (default 100k)
```

## Setup

```bash
uv sync
```

## Архітектура

1. **scrape** — Liquipedia API → `data/rosters/.../stage{N}.json` + `data/teams/{page}.json`
2. **analyze** — load data → dedupe → Bradley-Terry на **всіх** матчах (зовнішні опоненти в графі) → seed prior blend → Monte Carlo Swiss (6 кошиків) → `stage{N}_report.md`
3. Poisson Binomial → prob_at_least_5 для рекомендованого пікему

`cache/` — raw API JSON (hash keys). Default scrape читає cache, **0 HTTP** якщо page вже качали.

## Турнір

`TOURNAMENT = "Intel_Extreme_Masters/2026/Cologne"`

## Scrape

- **Default** (`scrape 1`) — `cache/` on, merge лише **нових** матчів у `data/teams/`
- **`scrape 1 --fresh`** — bypass `cache/`, HTTP до LP (після нових ігор на major)

## Модель

- BT тренується на всіх матчах з team JSON (MOUZ, Vitality тощо — в графі, strengths лише для 16 roster)
- `<8` roster-матчів (weighted) → blend з seed prior: `exp(-0.15 * (seed-1))`
- Time decay: exponential half-life 30d, cutoff 180d
- Swiss buckets: `prob_3_0`, `prob_3_1`, `prob_3_2`, `prob_0_3`, `prob_1_3`, `prob_2_3`; `prob_advance = 3-0 + 3-1 + 3-2`
- Pick'Em: top-2 3-0, top-6 advance (3-1 / 3-2), top-2 0-3 з seed guard

## Важливо

- Моделі BO1 і BO3 тренуються окремо
- Swiss пейрінг за правилами Valve (Buchholz, без реваншів)
- `sleep(3.5)` тільки перед HTTP; cache hit = 0 sleep
- Не кешувати API errors; fail-fast на командах
- YAGNI

## Стек

- Python 3.14+, uv, pandas, numpy, scipy, requests, choix, beautifulsoup4
