# Stage 1 Retro — Intel Extreme Masters/2026/Cologne

**Score: 3/10** (badge ≥5: ✗) · прогнозовано **prob_at_least_5: 81.1%**

Джерело факту: [IEM Cologne Major 2026 — Stage 1](https://en.wikipedia.org/wiki/IEM_Cologne_Major_2026) (оновлено 4 Jun 2026).

## Правила оцінки

| Слот | Зараховано, якщо |
| --- | --- |
| 3-0 (×2) | record **3-0** |
| Advance (×6) | record **3-1** або **3-2** |
| 0-3 (×2) | record **0-3** |

3-0 і Advance — **різні слоти**. Команда з 3-0 **не** зараховується в advance-pick, навіть якщо пройшла далі.

## Pick'Em vs факт

| # | Категорія | Наш pick | Факт | P(model) | |
| --: | --- | --- | --- | ---: | --- |
| 1 | 3-0 | GamerLegion | 3-1 | 40.4% | ✗ |
| 2 | 3-0 | BetBoom Team | 3-0 | 29.2% | ✓ |
| 3 | Advance | BIG | 2-2, out | 78.1% | ✗ |
| 4 | Advance | B8 | **3-0** | 75.2% | ✗ |
| 5 | Advance | HEROIC | 1-3 | 74.8% | ✗ |
| 6 | Advance | SINNERS Esports | 0-3 | 70.0% | ✗ |
| 7 | Advance | M80 | 3-1 | 68.1% | ✓ |
| 8 | Advance | MIBR | 3-1 | 66.1% | ✓ |
| 9 | 0-3 | FlyQuest | 2-2 | 47.9% | ✗ |
| 10 | 0-3 | THUNDERdOWNUNDER | 1-3 | 26.3% | ✗ |

**Підсумок по категоріях:** 3-0 **1/2** · Advance **2/6** · 0-3 **0/2**

## Фактичні кошики

| Кошик | Команди |
| --- | --- |
| 3-0 | B8, BetBoom Team |
| 3-1 | GamerLegion, M80, MIBR |
| 3-2 | Team Liquid, NRG, TYLOO |
| 0-3 | Gaimin Gladiators, SINNERS Esports |

## Де вгадали

- **BetBoom Team** — 3-0 ✓
- **M80, MIBR** — advance (3-1) ✓

## Де промахнулись

| Промах | Що сталося | Модель |
| --- | --- | --- |
| GamerLegion у 3-0 | 0-2 vs BetBoom у 3-0 матчі → 3-1 | #1 prob_3_0 (40.4%) |
| B8 у advance | пішла **3-0** — не той слот | 75.2% advance; треба було в 3-0 (25.6%) |
| SINNERS у advance | 0-3 | 70.0% advance |
| HEROIC, BIG advance | 1-3 / 2-2 out | ~75% advance |
| 0-3 picks | FlyQuest 2-2, TDU 1-3 | факт: Gaimin Gladiators, SINNERS |
| Пропустили в advance | Liquid, NRG, TYLOO (3-2) | 25–29% advance |

## Калібрування моделі

Сума marginal-ймовірностей по 16 командах (очікувана кількість команд у кошику):

| Кошик | Σ P(team) | Факт |
| --- | ---: | ---: |
| 3-0 | 2.00 | 2 |
| Advance | 8.00 | 8 |
| 0-3 | 2.00 | 2 |

Маргінали збалансовані. Pick'Em 3/10 — через помилки в **конкретних слотах** (B8 не в 3-0, SINNERS/0-3), не через Σ prob.
