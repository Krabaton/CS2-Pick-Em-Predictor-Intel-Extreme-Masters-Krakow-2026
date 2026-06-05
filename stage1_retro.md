# Stage 1 Retro — Intel Extreme Masters/2026/Cologne

**Score: 4/10** (badge ≥5: ✗) · прогнозовано **prob_at_least_5: 81.1%**

**Ground truth:** склад Stage 2 (`stage2_report.md`, seeds 9–16) + record по кошиках з HLTV.

## Правила оцінки

| Слот | Зараховано, якщо |
| --- | --- |
| 3-0 (×2) | record **3-0** |
| Advance (×6) | record **3-1** або **3-2** |
| 0-3 (×2) | record **0-3** |

3-0 і Advance — **різні слоти**. Команда з 3-0 **не** зараховується в advance-pick.

## Хто пройшов з Stage 1 → Stage 2

З `stage2_report.md` (seeds 9–16):

| Seed S2 | Команда | Record S1 |
| ---: | --- | --- |
| 9 | B8 | 3-0 |
| 10 | BetBoom Team | 3-0 |
| 11 | GamerLegion | 3-1 |
| 12 | M80 | 3-1 |
| 13 | MIBR | 3-1 |
| 14 | TYLOO | 3-2 |
| 15 | BIG | 3-2 |
| 16 | FlyQuest | 3-2 |

**Не пройшли** (з Stage 1 pool): Team Liquid, NRG, Lynn Vision, HEROIC, SINNERS, Gaimin Gladiators, THUNDERdOWNUNDER, Sharks Esports.

## Pick'Em vs факт

| # | Категорія | Наш pick | Факт | P(model) | |
| --: | --- | --- | --- | ---: | --- |
| 1 | 3-0 | GamerLegion | 3-1 | 40.4% | ✗ |
| 2 | 3-0 | BetBoom Team | 3-0 | 29.2% | ✓ |
| 3 | Advance | BIG | 3-2 | 78.1% | ✓ |
| 4 | Advance | B8 | 3-0 | 75.2% | ✗ |
| 5 | Advance | HEROIC | 1-3 | 74.8% | ✗ |
| 6 | Advance | SINNERS Esports | 0-3 | 70.0% | ✗ |
| 7 | Advance | M80 | 3-1 | 68.1% | ✓ |
| 8 | Advance | MIBR | 3-1 | 66.1% | ✓ |
| 9 | 0-3 | FlyQuest | **3-2** | 47.9% | ✗ |
| 10 | 0-3 | THUNDERdOWNUNDER | 1-3 | 26.3% | ✗ |

**Підсумок:** 3-0 **1/2** · Advance **3/6** · 0-3 **0/2**

## Де вгадали

- **BetBoom Team** — 3-0 ✓
- **BIG, M80, MIBR** — advance ✓

## Де промахнулись

| Промах | Факт | |
| --- | --- | --- |
| GamerLegion у 3-0 | 3-1 | ✗ |
| B8 у advance (не в 3-0) | 3-0 | ✗ |
| SINNERS, HEROIC advance | 0-3 / 1-3 | ✗ |
| FlyQuest у 0-3 | **пройшла 3-2** | ✗ |
| TDU у 0-3 | 1-3 | ✗ |

## Калібрування моделі

| Кошик | Σ P(team) | Факт |
| --- | ---: | ---: |
| 3-0 | 2.00 | 2 |
| Advance | 8.00 | 8 |
| 0-3 | 2.00 | 2 |

Маргінали ок. Pick'Em 4/10 — joint-слоти, не Σ prob.
