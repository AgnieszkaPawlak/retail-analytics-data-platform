# DE-004 — Architecture & KPI Technical Review

**Version:** 0.2  
**Status:** Technical review completed; implementation and business approval pending.  
**Original drafts:** [architecture.md](../../robocze/DE-004/architecture.md) and [kli_definitions.md](../../robocze/DE-004/kli_definitions.md).  
**Reviewed deliverables:** [architecture.md](architecture.md) and [kpi-definitions.md](../business/kpi-definitions.md).

## What was corrected

| ID | Change | Reason |
|---|---|---|
| REV-01 | Align target stack to Python + S3 + Snowflake + dbt + Airflow | Project plan had already selected these tools; PostgreSQL + Prefect is a legitimate alternative, but it needs a separate approved ADR and revised roadmap. |
| REV-02 | Add explicit S3 snapshots, Snowflake RAW, dbt, Airflow and CI responsibilities | The original diagram showed logical processing but not all agreed components and physical source/warehouse boundaries. |
| REV-03 | Replace PostgreSQL-specific pointer commit with Snowflake-scoped atomic activation requirement | Do not assume one ACID transaction spans S3, warehouse and orchestrator. Exact transaction/concurrency behavior must be tested in the warehouse. |
| REV-04 | Require the release manifest to enumerate the approved MVP metrics | A hypothetical TBA KPI must not be silently reported as official or indefinitely block unrelated approved diagnostics. |
| REV-05 | Clarify multi-query report release pinning | A dashboard can otherwise read two different active versions during one refresh. |
| REV-06 | Correct the KPI file name and cross-document links | Canonical name is `kpi-definitions.md`; preserve the original typo only in the unchanged source draft. |
| REV-07 | Preserve illustrative diagnostic KPI fixtures and mark official metrics as TBA | Source-calculated amounts do not prove recognized revenue, customer value or independent ledger reconciliation. |

## Review outcome

**Architecture model:** technically coherent, revised against the agreed project baseline.  
**KPI catalogue:** technically coherent; calculations and fixture examples remain specifications, not executed validation.  
**Business sign-off:** pending Sales, Finance, Customer Analytics and Engineering ownership decisions.  
**Implementation:** not started and not tested.

## Required verification before deployment

1. Validate that Snowflake can switch the active release atomically while candidate marts remain invisible.
2. Verify readers pin one release across concurrent multi-query refreshes.
3. Approve the set of MVP-required metrics and their versions; leave unapproved official metrics disabled.
4. Complete the outstanding revenue/FX/cancellation policy decisions with designated business owners.
5. Reproduce DE-002 evidence before using it as a signed production data-quality baseline.

This review changes the design documents, not the original user submissions.
