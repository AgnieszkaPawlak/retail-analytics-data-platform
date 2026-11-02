# Robocze — pliki podzielone według zadań

Wersje robocze artefaktów projektu. Każdy ticket ma własny folder o nazwie odpowiadającej identyfikatorowi zadania.

| Ticket | Wersje robocze | Dokumenty w katalogach docelowych | Status |
|---|---|---|---|
| **DE-001 — Business Requirements** | [`DE-001/requirements_v0.1.md`](DE-001/requirements_v0.1.md) | [`business/requirements.md`](../business/requirements.md) | Reviewed v0.2; decyzje biznesowe TBA |
| **DE-002 — Source Data Profiling** | [`DE-002/sourceprofiling.md`](DE-002/sourceprofiling.md), [`DE-002/profile_sources.py`](DE-002/profile_sources.py) | [`docs/data/source-profiling.md`](../docs/data/source-profiling.md), [`scripts/profiling/profile_sources.py`](../scripts/profiling/profile_sources.py) | Reviewed v0.2; rzeczywiste pomiary UCI/ECB niepotwierdzone |

## Zasada pracy

1. Swoje rozwiązania zapisujesz w `robocze/DE-XXX/`.
2. Po przeglądzie dokumentuję zmiany i zachowuję oryginalne materiały do porównania.
3. Wersje po review publikuję w katalogach docelowych, np. `business/`, `docs/data/`, `scripts/profiling/`.
4. Stan akceptacji jest jawny: `reviewed` nie znaczy `empirically verified` ani `approved by business`.
5. Dane źródłowe i dowody pomiarów zachowujemy tak, aby wynik można było odtworzyć.
