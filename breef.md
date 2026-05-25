**Задача: CS2 Major Pick'Em предиктор**

Написати Python-скрипт `pickem.py` який приймає номер стейджу, автоматично збирає дані, тренує модель і зберігає результат у файл.

```
uv run python pickem.py scrape 1
uv run python pickem.py analyze 1
```

---

**Крок 1 — Список команд стейджу**

Звернутись до Liquipedia API (`https://liquipedia.net/counterstrike/api.php`) і отримати список команд-учасників вказаного стейджу турніру IEM Cologne Major 2026. Назва турніру хардкодиться як константа `TOURNAMENT = "Intel_Extreme_Masters/2026/Cologne"`. Якщо дані відсутні або стейдж не почався — завершити з чітким повідомленням про помилку.

---

**Крок 2 — Збір матчів**

Для кожної команди завантажити з Liquipedia всі матчі за останні 6 місяців. Зберігати **всі** матчі (включно з зовнішніми опонентами). Для кожного матчу: команда A, команда B, переможець, формат (BO1/BO3), дата. Дедуплікувати матчі. Кешувати результати запитів на диск щоб не бити по API при перезапуску.

---

**Крок 3 — Bradley-Terry модель**

Тренувати дві окремі моделі — для BO1 і BO3. Граф включає всіх опонентів з team files; strengths повертаються лише для 16 roster команд.

Time decay — exponential, half-life 30 days (`0.5^(age/30)`), cutoff 180 days:

Для roster-команд з менше ніж 5 матчами — blend з seed prior: `prior = exp(-0.15 * (seed-1))`, `w = min(1, match_count/5)`.

Ймовірність перемоги: `P(A beats B) = strength_A / (strength_A + strength_B)`

---

**Крок 4 — Симуляція Swiss (100,000 ітерацій)**

Правила Valve Major Swiss: wins_to_advance=3, losses_to_eliminate=3. Перший раунд: 1v9, 2v10, ..., 8v16 за посівом. Наступні раунди: Buchholz pairing з уникненням реваншів. Формати: BO1 в раундах 1-4, BO3 у вирішальних матчах. По завершенні рахувати для кожної команди: `prob_3_0`, `prob_3_1`, `prob_3_2`, `prob_0_3`, `prob_1_3`, `prob_2_3`. `prob_advance = prob_3_0 + prob_3_1 + prob_3_2`.

---

**Крок 5 — Оптимальний Pick'Em**

Рекомendований Pick'Em: топ-2 по `prob_3_0`, топ-6 по `prob_advance` (3-1 / 3-2), топ-2 по `prob_0_3` з seed guard (seed ≤8 і prob_0_3 < 20% → пропустити).

---

**Збереження результату**

Зберігати у файл `stage{N}_report.md` — таблиця з 6 кошиками + Advance і блок з рекомендованим Pick'Em та `prob_at_least_5`.

---

**Стек:** Python 3.11+, pandas, numpy, scipy, requests, choix.
