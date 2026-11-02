# Retail Analytics Data Platform

Projekt szkoleniowy Data Engineering. Dokumentacja techniczna jest uporządkowana według funkcji, a kopie robocze według identyfikatorów zadań.

## Dokumentacja i pliki projektu

- **DE-001 — Business Requirements:** [`business/requirements.md`](business/requirements.md) — wersja po review v0.2; część decyzji biznesowych pozostaje TBA.
- **DE-002 — Source Data Profiling:** [`docs/data/source-profiling.md`](docs/data/source-profiling.md) — przejrzany raport v0.2, **wstępny: pomiary UCI/ECB do potwierdzenia**.
- **DE-002 — Profiling script:** [`scripts/profiling/profile_sources.py`](scripts/profiling/profile_sources.py) — skrypt do zbierania pomiarów z wymuszoną poprawną serializacją JSON.

- **DE-003 — Data Contracts & Quality Rules:** [`docs/data/data-contracts.md`](docs/data/data-contracts.md) — po technical review v0.2; wymaga zatwierdzenia biznesowego i późniejszego wykonania testów kontraktowych.
- **DE-002 — Profiling evidence:** [`profiling_evidence.json`](profiling_evidence.json) — zapisany pomiar, podczas review znormalizowany do poprawnego JSON. Oryginalna postać z `NaN` jest zachowana w [`robocze/DE-002/profiling_evidence_original.txt`](robocze/DE-002/profiling_evidence_original.txt).

## Materiały robocze według zadań

- [Indeks plików roboczych](robocze/README.md)
- [DE-001](robocze/DE-001/requirements_v0.1.md) — pierwotna wersja requirements.
- [DE-002](robocze/DE-002/sourceprofiling.md) — raport roboczy; [skrypt roboczy](robocze/DE-002/profile_sources.py).
- [DE-003](robocze/DE-003/data_contracts.md) — pierwotne rozwiązanie Data Contracts.

W folderach `robocze/DE-XXX/` przechowujemy oryginalne wersje i materiały do review. Wersje opublikowane po przeglądzie trafiają do katalogów odpowiadających ich funkcji. Publikacja pliku nie oznacza automatycznie pełnej akceptacji wszystkich wyników.
