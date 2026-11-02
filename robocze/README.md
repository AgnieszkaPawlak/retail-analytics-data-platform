# Robocze — pliki według ticketów

Każde zadanie ma własny folder `robocze/DE-XXX/`. Zachowujemy oryginalne propozycje, a ich wersje po review publikujemy w odpowiednich katalogach docelowych.

| Ticket | Oryginalne materiały | Wersja po review | Status |
|---|---|---|---|
| DE-001 — Business Requirements | [requirements_v0.1.md](DE-001/requirements_v0.1.md) | [business/requirements.md](../business/requirements.md) | Reviewed v0.2 |
| DE-002 — Source Profiling | [sourceprofiling.md](DE-002/sourceprofiling.md), [profile_sources.py](DE-002/profile_sources.py) | [docs/data/source-profiling.md](../docs/data/source-profiling.md), [scripts/profiling/profile_sources.py](../scripts/profiling/profile_sources.py) | Reviewed; empiryczne potwierdzenie otwarte |
| DE-003 — Data Contracts | [data_contracts.md](DE-003/data_contracts.md) | [docs/data/data-contracts.md](../docs/data/data-contracts.md) | Reviewed v0.2; zatwierdzenie biznesowe otwarte |
| DE-004 — Architecture & KPI | [architecture.md](DE-004/architecture.md), [kli_definitions.md](DE-004/kli_definitions.md) | [docs/architecture/architecture.md](../docs/architecture/architecture.md), [docs/business/kpi-definitions.md](../docs/business/kpi-definitions.md) | Reviewed v0.2; decyzje KPI i walidacja publikacji otwarte |

## Zasada pracy

1. Własne rozwiązanie zapisujesz w `robocze/DE-XXX/`.
2. Po review zachowujemy oryginały i publikujemy poprawione dokumenty w katalogach docelowych.
3. Każda wersja po review zawiera zakres zmian, status i listę pozostających zależności.
4. `Reviewed` nie oznacza `business-approved` ani `runtime-tested`.
5. Raporty z analizy źródeł muszą pozostać odtwarzalne; [oryginalny artefakt DE-002](DE-002/profiling_evidence_original.txt) zachowano do audytu.
