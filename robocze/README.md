# Robocze — pliki podzielone według zadań

Tutaj znajdują się **wersje robocze** artefaktów Data Engineering. Każdy ticket ma katalog o nazwie odpowiadającej jego identyfikatorowi.

| Ticket | Pliki | Status |
|---|---|---|
| **DE-001** — Business Requirements | [`DE-001/requirements_v0.1.md`](DE-001/requirements_v0.1.md) | Wersja archiwalna; dokument po review: [`../business/requirements.md`](../business/requirements.md) |
| **DE-002** — Source Data Profiling | [`DE-002/sourceprofiling.md`](DE-002/sourceprofiling.md), [`DE-002/profile_sources.py`](DE-002/profile_sources.py) | Review wykonany, rzeczywiste pomiary UCI/ECB wymagają potwierdzenia |

## Zasada pracy

1. Nowe rozwiązania trafiają do `robocze/DE-XXX/`.
2. Po review poprawki są nanoszone w folderze danego zadania, z opisem zmian.
3. Dopiero po spełnieniu kryteriów akceptacji dokumenty są przenoszone do katalogów docelowych (`business/`, w przyszłości `docs/data/` itp.).
4. Nie usuwaj danych źródłowych ani raportów dowodowych potrzebnych do odtworzenia analiz.

**Uwaga:** raport `DE-002/sourceprofiling.md` ma status wstępny, ponieważ brakuje potwierdzonych pomiarów pełnego pliku UCI oraz odpowiedzi ECB. Nie traktuj statystyk z materiałów wtórnych jako własnych pomiarów.
