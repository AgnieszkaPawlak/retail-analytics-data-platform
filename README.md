# Retail Analytics Data Platform

Praktyczny projekt Data Engineering: Python, AWS S3, Snowflake, dbt Core, Apache Airflow, Docker, pytest i GitHub Actions.

## Dokumentacja po review

| Ticket | Artefakt | Status |
|---|---|---|
| DE-001 — Business Requirements | [business/requirements.md](business/requirements.md) | Reviewed v0.2; decyzje biznesowe TBA |
| DE-002 — Source Data Profiling | [docs/data/source-profiling.md](docs/data/source-profiling.md) | Reviewed v0.2; pomiary i sign-off w toku |
| DE-002 — Profiling script | [scripts/profiling/profile_sources.py](scripts/profiling/profile_sources.py) | Strict JSON output |
| DE-003 — Data Contracts | [docs/data/data-contracts.md](docs/data/data-contracts.md) | Reviewed v0.2; akceptacja biznesowa otwarta |
| DE-004 — Architecture | [docs/architecture/architecture.md](docs/architecture/architecture.md) | Reviewed v0.2; implementacja i mechanizm publikacji do weryfikacji |
| DE-004 — KPI Definitions | [docs/business/kpi-definitions.md](docs/business/kpi-definitions.md) | Reviewed v0.2; oficjalne KPI wymagają zatwierdzenia |
| DE-004 — Review | [docs/architecture/DE-004-review.md](docs/architecture/DE-004-review.md) | Uzasadnienie korekt i otwarte decyzje |

## Source evidence

- [Profiling results](profiling_evidence.json) — zapisane pomiary; format JSON znormalizowany bez ponownego profilowania.
- [Oryginalna wersja dowodów](robocze/DE-002/profiling_evidence_original.txt) — historyczne artefakty do audytu.

## Praca nad zadaniami

Nowe rozwiązania zapisujemy w katalogach [robocze/DE-XXX](robocze/README.md). Po code review ich oryginalne wersje pozostają w folderze zadania, a poprawione dokumenty trafiają do katalogów docelowych.

**Uwaga:** Technical review nie oznacza wykonanych testów runtime ani formalnego zatwierdzenia zasad finansowych.
