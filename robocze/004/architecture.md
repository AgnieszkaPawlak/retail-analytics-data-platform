# Northstar Retail — Retail Analytics Platform Architecture

**Document ID:** ARCH-DE-004  
**Version:** 0.1 — architecture proposal  
**Status:** DRAFT, not implemented or business-approved  
**Date:** 2026-11-02  
**Companion:** [kli_definitions.md](kli_definitions.md) — KPI definitions (filename per task request)  
**Inputs:** [DE-001 business requirements](../../business/requirements.md), [DE-002 source profiling](../../docs/data/source-profiling.md), [DE-003 reviewed data contracts](../../docs/data/data-contracts.md), [profiling evidence](../../profiling_evidence.json).

> Scope: architecture and logical data/metrics design only. No ETL code, database DDL or infrastructure configuration. Financial definitions, FX policy and customer valuation remain **TBA** where stakeholders have not approved them.

## 1. Executive summary

Propose a **batch-oriented historical analytics platform** using two sources: UCI Online Retail dataset 352 (XLSX, original transaction prices in GBP) and the ECB EXR daily GBP/EUR reference-rate series. An immutable input and lineage record flows through **RAW → STAGING → INTERMEDIATE → MARTS**. Sales, Finance and Customer Analytics see data only through shared, **versioned published semantic views**.

**Non-negotiable invariant:** An unsuccessful, incomplete or inconsistent candidate build **never replaces the last successfully published report**. One release contains the source snapshots, validated marts, contract versions and metric definitions required by all of its consumers. The last-success timestamp advances only after complete publication.

**Proposed technology, not installed:** Python (XLSX and HTTP acquisition / validation), immutable file snapshots, PostgreSQL (layered analytical tables, transactional publication), dbt Core (SQL transformations and tests), Prefect (batch workflow/retries) and a read-only BI interface (Metabase candidate). The archived 541,909-line dataset does not justify distributed processing in this educational MVP.

### 1.1 Business drivers and design response

| Driver | BRS reference | Architecture response |
|---|---|---|
| No manual spreadsheet consolidation | FR-01/02 | Curated marts and read-only Sales reports |
| Sales and Finance must agree | FR-03/09/13; NFR-02 | One metric registry, same semantic views and pinned publication version |
| Cancellation/history/currency | FR-04/05/06; NFR-06 | Signed source lines, adjustment candidates, versioned ECB rates and explicit policy gates |
| Customer purchasing patterns | FR-07/08 | Identified-customer facts plus missing-ID coverage, not fabricated customers |
| No partial reports after failures | FR-10/11/12; NFR-03/05 | Isolated candidate builds, release gate, atomic publication pointer, truthful freshness status |

## 2. High-level architecture

### 2.1 Mermaid — complete data flow

~~~mermaid
flowchart LR
  U["UCI Online Retail<br/>historical XLSX / GBP"] --> A["Acquire and fingerprint<br/>source ID, SHA-256, retrieval"]
  E["ECB EXR<br/>GBP per EUR / API"] --> A
  A --> R["RAW<br/>immutable source files<br/>raw rows and response metadata"]
  R --> V["Data contract validation<br/>DE-003 rules"]
  V -->|"accepted with flags"| S["STAGING<br/>typed rows, source lineage<br/>quality/parse flags"]
  V -->|"errors / warnings"| Q["Quality register<br/>quarantine, impact, audit"]
  S --> I["INTERMEDIATE<br/>signed invoice lines, invoice groups<br/>cancellation candidates, FX eligibility"]
  I --> M["Candidate MARTS<br/>sales, finance, customer<br/>release_id and metric_version"]
  Q --> G{"Publication gate<br/>quality, coverage, policy<br/>report reconciliation"}
  M --> G
  G -->|"PASS"| P["Atomic activation<br/>current_release pointer"]
  G -->|"FAIL"| F["Keep prior release<br/>FAILED/BLOCKED/STALE"]
  P --> H["Published semantic views<br/>pinned release_id"]
  H --> SA["Sales"]
  H --> FI["Finance"]
  H --> CA["Customer Analytics"]
  P --> O["Last successful publish<br/>and coverage status"]
  F --> O
~~~

**Interpretation:** A job may ingest and transform data successfully but remain unpublished. Contracts are checked before analytical models; metric-specific eligibility and report dependency coverage are checked **again at the release gate**. Dashboards cannot query candidate marts directly.

### 2.2 Release state machine

~~~mermaid
stateDiagram-v2
  [*] --> RECEIVED
  RECEIVED --> REJECTED: bad source or schema
  RECEIVED --> VALIDATING
  VALIDATING --> REJECTED: critical contract failure
  VALIDATING --> CANDIDATE: rows classified and retained
  CANDIDATE --> BLOCKED: material exceptions or TBA policy
  CANDIDATE --> FAILED: transformation failed
  CANDIDATE --> VERIFIED: all required tests passed
  VERIFIED --> PUBLISHED: atomic activation committed
  VERIFIED --> FAILED: activation aborted
  PUBLISHED --> [*]
  REJECTED --> [*]
  BLOCKED --> [*]
  FAILED --> [*]
~~~

**PUBLISHED is distinct from a green ingestion task.** Its timestamp is assigned at transaction commit, never at the start of a run.

## 3. Component responsibility matrix

| Component | What it owns | Input → output | Failure behavior |
|---|---|---|---|
| **Acquisition** | Download UCI, request ECB, record URL, window, HTTP status, retrieval UTC and SHA-256 | Source → immutable artifact + manifest | Record failed attempt; no publish |
| **Source catalog** | Track source vintage, batch ID, hash, date range, contract version | Artifact → source_batch | Same-content replay is idempotent; changed source is a new vintage |
| **Contract validator** | Check DE-003 schema, completeness, uniqueness, validity and FX identity | Raw rows → violations, quarantine, eligibility flags | CRITICAL rejects batch; financial ERROR holds affected publication |
| **RAW** | Preserve exact source evidence and its physical record order | Original XLSX / ECB CSV → immutable rows | No dedup, sign changes, forced values or currency inference |
| **STAGING** | Source-aligned typing and technical parsing | Raw → typed fields with original-value lineage | Quarantine invalid values; no default of zero for bad numeric |
| **INTERMEDIATE** | Shared normalized invoice line, invoice header, cancellation candidate, FX observation/resolution, customer grouping | Staging → reusable facts | No unapproved historical invoice linking, accounting policy or weekend FX fill |
| **Metric registry** | Approved IDs, versions, formulas, granularity, filters, currency and owners | Signed-off definitions → semantic metadata | Unapproved metrics remain TBA; diagnostics explicitly labelled |
| **MART builder** | Materialize candidate aggregates at specified grains | Intermediate + metric versions → marts by release_id | Candidate-only writes; old release intact |
| **Release gate** | Check all required marts exist, contract exceptions resolved, rates covered, metric parity and reconciliation | Candidate + QA → VERIFIED or BLOCKED | Do not activate if one required result is invalid |
| **Publication registry** | Single active release, history, atomic switch and last successful UTC time | VERIFIED → current_release | Transaction failure leaves former release active |
| **Published views / BI** | Same business metrics for all audiences; show freshness, definitions, lineage | Current/pinned release → reports | No separate Finance and Sales formulas; no candidate access |
| **Orchestrator and monitoring** | Schedule, bounded retries, run and data-quality status, alerts | Inputs/events → run log and DQ summaries | Does not equate completed jobs with published success |

**Accountability:** Daniel approves reliability and operational behavior; Michael approves Finance/FX/cancellation treatment; Sarah Sales report scope; Emma customer metrics; cross-functional metric governor/sponsor **TBA**.

## 4. Data layers

| Layer | Responsibility | Proposed datasets | Invariant |
|---|---|---|---|
| **RAW** | Source of reproducible evidence, not a clean business dataset | Immutable UCI XLSX and ECB response; source_batch; raw_uci_line; raw_ecb_observation | Preserve raw bytes, hash, row ordinal, original value, source vintage; no silent cleanup |
| **STAGING** | Parse and standardize technical formats | stg_uci_invoice_line, stg_ecb_rate_observation | Retain original + typed values, parse errors and null distinction |
| **INTERMEDIATE** | Express reusable entities and candidate business classifications | int_invoice_line, int_invoice_header, int_cancellation_candidate, int_ecb_usable_rate, int_fx_resolution, int_customer_invoice | One reusable definition of signed line amount; no invented cancellation linkage or revenue recognition |
| **MARTS** | Aggregate and validate data per metric version/release | mart_daily_sales, mart_daily_finance, mart_customer_period, mart_customer_value | Candidate versions remain isolated and never appear as current |
| **PUBLISHED ACCESS** | Consistent read-only semantic layer | vw_published_sales, vw_published_finance, vw_published_customers, vw_report_status | Views only expose active/pinned complete releases |

A RAW artifact store may be local immutable files in an educational implementation or object storage later; the decision does not change logical layer boundaries.

## 5. Logical data model

### 5.1 Tables, grain and keys

| Model | Grain — exactly one row per | Primary / candidate identity | Main fields, joins and caveats |
|---|---|---|---|
| **source_batch** | source acquisition/vintage | batch_id; source + content hash identifies immutable artifact | source, retrieval timestamp, request window, SHA-256, status, contract_version |
| **raw_uci_line** | physical XLSX line in source_batch | **(batch_id, row_number)** | All eight UCI columns as delivered; row_number is a technical key **not** a business line ID |
| **raw_ecb_observation** | physical API CSV observation in source_batch | **(batch_id, row_number)** | Original KEY, TIME_PERIOD, OBS_VALUE, dimensions, OBS_STATUS |
| **dq_violation** | one rule violation on a batch or row | violation_id | rule ID, severity, disposition, affected metric, impact, row reference |
| **stg_uci_invoice_line** | typed raw UCI line | (batch_id, row_number) | InvoiceNo, StockCode, Quantity, UnitPrice GBP, InvoiceDate, CustomerID nullable, Country, Description nullable |
| **stg_ecb_rate_observation** | typed ECB observation in vintage | (batch_id, row_number) | series_key, observation_date, rate_gbp_per_eur, status, validity flag |
| **int_invoice_line** | UCI line in a given snapshot | (uci_batch_id, source_row_number) | signed_line_amount_gbp, cancellation candidate flags, validity/eligibility |
| **int_invoice_header** | InvoiceNo within a UCI snapshot | (uci_batch_id, invoice_no) | group line count; date/customer/country consistency checks; **not** proof of enterprise order |
| **int_cancellation_candidate** | flagged invoice line | source line key | C prefix or negative quantity, candidate reason, **original_invoice_no NULL unless proven** |
| **int_ecb_usable_rate** | unique rate date and series within ECB vintage | (ecb_batch_id, series_key, observation_date) | positive finite GBP-per-EUR value, status and version |
| **int_fx_resolution** | source line × candidate release × FX policy version | release_id + source line key + policy_version | matched rate date/vintage/rate, matched/unmatched reason; no silent fallback |
| **int_customer_invoice** | identified customer and invoice in UCI snapshot | (uci_batch_id, customer_id, invoice_no) | grouping for candidate purchase frequency; purchase/return eligibility TBA |
| **metric_definition** | one version of one metric | (metric_id, metric_version) | status APPROVED/TBA/DIAGNOSTIC, formula, grain, policy and approver |
| **report_release** | one immutable candidate or published result set | release_id | source_batch references, metric/contract versions, coverage, QA gate result and timestamps |
| **mart_daily_sales** | release × day × agreed reporting dimensions × metric version | composite including release_id and metric_id/version | daily sales, invoice counts and source diagnostics, currency and included/flagged counts |
| **mart_daily_finance** | release × reporting day × currency × metric version × dimensions | scoped composite | signed GBP, cancellation/FX amounts if approved; rate coverage and reconciliation |
| **mart_customer_period** | release × identified customer × analysis period × metric version | scoped composite | customer spend, number of purchases, repeat flags, scope/denominator |
| **current_release** | active reporting scope | scope_id = retail_analytics | single published release_id, last successful publish time, coverage and status |

**Identity cautions:** InvoiceNo repeats legitimately across product lines; InvoiceNo + StockCode also repeats in the actual profile. Neither is a unique row-level key. StockCode is not guaranteed a single immutable description. Country is residence **not original currency**. An archived snapshot does not contain full customer master data, payment status or adjustment-version history.

### 5.2 Entity relationships (Mermaid)

~~~mermaid
erDiagram
  SOURCE_BATCH ||--o{ RAW_UCI_LINE : contains
  SOURCE_BATCH ||--o{ RAW_ECB_OBSERVATION : contains
  SOURCE_BATCH ||--o{ DQ_VIOLATION : reports
  RAW_UCI_LINE ||--o| INT_INVOICE_LINE : normalizes
  RAW_ECB_OBSERVATION ||--o| INT_ECB_USABLE_RATE : validates
  INT_INVOICE_HEADER ||--o{ INT_INVOICE_LINE : groups
  REPORT_RELEASE ||--o{ MART_DAILY_SALES : versions
  REPORT_RELEASE ||--o{ MART_DAILY_FINANCE : versions
  REPORT_RELEASE ||--o{ MART_CUSTOMER_PERIOD : versions
  METRIC_DEFINITION ||--o{ MART_DAILY_SALES : defines
  METRIC_DEFINITION ||--o{ MART_DAILY_FINANCE : defines
  CURRENT_RELEASE }o--|| REPORT_RELEASE : references
~~~

The release manifest must explicitly list **both source vintages, contract versions, metric versions and report scope**. The diagram is conceptual, not SQL DDL; conditional source-type relationships are simplified for readability.

### 5.3 Type and semantic decisions

- Monetary columns use **fixed-point decimal** arithmetic, not binary floating point for official accounting totals; precision and rounding are **TBA** with Michael.
- Source invoice timestamps are preserved in their original representation. A source-date diagnostic uses the date portion of InvoiceDate; business reporting timezone, date basis and cutoff remain **TBA**.
- Source line diagnostic: **source_signed_line_amount_gbp = Quantity × UnitPrice**. This is **not** approved net or recognized revenue.
- Cancellation candidates use C-prefix and/or negative Quantity as evidence, not proof of original invoice linkage.
- Missing CustomerID is preserved and flagged; no invented ID or deletion of otherwise valid source-level monetary lines.
- ECB EXR.D.GBP.EUR.SP00.A expresses **GBP per 1 EUR**. For an *approved selected rate*, **EUR = GBP / rate_gbp_per_eur**. Which date is selected and how missing business days are handled are **TBA**; never quietly substitute a future rate.

## 6. Shared KPI semantic model: why Sales and Finance agree

The authoritative catalogue is [kli_definitions.md](kli_definitions.md). A metric request is uniquely specified by **metric_id + metric_version + publication release_id + reporting date basis + currency + filters/dimensions**.

1. Metric formulas live in **shared intermediate/semantic models**, not separate Sales and Finance dashboards. A display name alone is not a definition.
2. Reports use published views that join only the release pinned for the whole report refresh. A refresh spanning multiple queries must retain one release_id even if a new release activates mid-refresh.
3. Finance-specific accounting measures (recognized revenue, cancellation-adjusted net revenue) remain **TBA** until business approval. They must use distinct metric IDs from raw signed invoiced values.
4. Every report identifies currency, time basis, metric version, source coverage, excluded/flagged counts, last successful publication and release_id.
5. Cross-view parity is checked using the **same metric, parameters, release and rounding policy** before activation. A failure blocks the full shared release.
6. There is **no independent finance ledger** in the two sources. Synthetic reference cases may test formulas but cannot be presented as real ledger reconciliation.

**Initial decision:** **One global Sales/Finance/Customer release**. Separate GBP-only and EUR report families could publish independently under DE-003 ALL-PUB-04, but **only with explicit approval** and strict scope labels. A global initial release is safer for the stated consistency requirement.

## 7. Reliability and failure isolation

### 7.1 Publication invariants

| ID | Must always hold |
|---|---|
| **INV-01** | RAW artifacts and earlier report releases remain unchanged after failed attempts |
| **INV-02** | Identical source hashes + contract/metric versions are idempotent; no double counting |
| **INV-03** | All writes before activation target a **new candidate release_id**, never current marts |
| **INV-04** | A complete set of required marts passes source, contract, reconciliation, FX coverage and parity checks |
| **INV-05** | One transactional activation changes the **single active release pointer** or changes nothing |
| **INV-06** | A multi-query dashboard/report uses a **pinned release_id** throughout its refresh |
| **INV-07** | Failure never advances last successful publication time or data-through period |
| **INV-08** | Every rejected/quarantined record, retry and release is auditable by rule and source vintage |

### 7.2 Publication protocol (design only)

1. Allocate a new **release_id** and immutable manifest listing source artifact hashes and selected contract/metric versions.
2. Validate source batches and classify all exceptions. CRITICAL input failures reject a batch; isolated record errors are quarantined, but **unresolved monetary impact blocks dependent publication**.
3. Build all candidate intermediate models and marts under this release_id. Confirm source/FX coverage, completeness, metric eligibility and agreement between Sales/Finance aggregations.
4. A candidate with missing critical dependencies or TBA policies for required metrics is **BLOCKED**; its data is never exposed via published views.
5. On complete validation, perform a **single PostgreSQL transaction**: verify current pointer has not changed unexpectedly, mark new release published and switch **current_release** to new release. Commit atomically. A rollback leaves old release visible.
6. Reports read only the new pointer after commit and pin its release_id for the duration of their refresh. The publication timestamp is recorded on successful commit.
7. Retain old releases for audited comparison under an approved retention policy (TBA).

### 7.3 Failure / retry / replay matrix

| Situation | Response / retry | Public result |
|---|---|---|
| UCI cannot be retrieved | Bounded retry for transient acquisition; fail closed for corrupt XLSX | Old published version preserved, failed state logged |
| ECB 429/5xx or network timeout | Bounded backoff, attempts/time window **TBA** with Daniel | Old published version preserved; dependent FX metrics not fabricated |
| Wrong/missing column, wrong ECB series | Reject whole batch; fix source/schema before reprocessing | No activation |
| Unparseable UnitPrice or Quantity | Quarantine row; hold dependent financial mart until reconciled or approved exclusion | No silent reduced financial total |
| NULL CustomerID or repeated-looking invoice line | Keep and flag; customer metric coverage disclosed | Candidate may proceed per approved eligibility |
| No usable rate for required date | Block FX-dependent metrics; **no implicit forward-fill** | Unified release remains old |
| Mart construction fails halfway | Retry idempotent candidate step; keep old release | Neither half-built Sales nor Finance becomes visible |
| Activation transaction fails | Roll back; inspect pointer before retrying | Last successful release and timestamp intact |
| Same inputs replayed | No-op or deterministic rebuild with same outcome | No duplicate released facts |
| Rate/source/definition revised | New vintage, new candidate release; impact and sign-off required | No silent historical restatement |
| Parity between Sales and Finance fails | Block activation and record metric variance | Old consistent version remains active |

**Retry transient failures, not deterministic bad business data.** Whether last valid data counts as stale is assessed against the approved Monday cutoff and freshness SLA (**TBA**); a failed run is not masked by a green status.

**History limit:** The archived UCI source does not establish complete cancellation-to-original-invoice lineage or as-originally-reported accounting history. Versioned replays explain this platform's releases, not missing upstream accounting events.

## 8. Architecture decision records (ADR)

| ADR | Recommendation | Why / trade-offs |
|---|---|---|
| **ADR-01** | Historical **batch** rather than streaming | UCI XLSX is static; ECB is reference-rate history; simpler to operate and replay |
| **ADR-02** | Python for acquisition and contract validation | Existing Python profiling work; strong XLSX and HTTP support; validator implementation deferred |
| **ADR-03** | PostgreSQL for staged data, marts and atomic publication | ACID transactions and consistent shared views; DuckDB lighter for exploration, but not chosen as multi-reader publication authority |
| **ADR-04** | Retain immutable raw source files and row lineage | Supports recovery, reproducibility and forensic analysis at modest dataset size |
| **ADR-05** | dbt Core for SQL transformations/tests and versioned models | Centralized definitions and testability, rather than formula copies in dashboards |
| **ADR-06** | Prefect as workflow/retry coordinator | Python-oriented batch scheduling and observability; simpler alternatives possible if operations stay minimal |
| **ADR-07** | Metabase or equivalent **read-only** BI over published views | Business reports use governed measures, not their own accounting formulas |
| **ADR-08** | One **unified global release pointer** | Prevents mixed Sales/Finance vintages; may delay GBP reports when FX inputs fail; independent families require approval |
| **ADR-09** | Fixed-point GBP calculations, versioned ECB rates | Avoids float errors and wrong FX direction; policy details TBA |
| **ADR-10** | Keep flagged duplicates, cancellations and anonymous-customer lines | DE-002/003 do not justify blanket deletion; financial totals must be reconcilable |

**Not decided or built here:** Docker/infrastructure, database DDL, Python ETL, dbt SQL, scheduling config, CI/CD, observability integrations, access control/retention settings, actual dashboard implementation and finance-ledger integration.

## 9. Nonfunctional evidence and monitoring

Every run/release records source IDs and hashes, contract version, requested window, rows received/accepted/quarantined, duplicates/anomalies, null rates, financial exception exposure, usable FX coverage, candidate consistency/parity, publication outcome, published release ID, data-through date and last successful publication UTC. Error logs retain rule IDs and clear reason codes. Target thresholds, alert recipients, freshness cutoff and recovery objectives are **TBA**.

## 10. Architecture acceptance criteria

These are **future test/walkthrough specifications**, not tests executed for this document.

| AC | Objective verification | Expected outcome |
|---|---|---|
| **ARCH-AC-01** | Trace one UCI invoice row and one ECB rate through the diagram | Every stage from acquisition through published report is accounted for |
| **ARCH-AC-02** | Review layer/table inventory | RAW, STAGING, INTERMEDIATE and MARTS each have stated purpose, ownership, grains and keys |
| **ARCH-AC-03** | Remove UCI Quantity column | Source batch rejected, previous report unaffected |
| **ARCH-AC-04** | Insert unparseable UnitPrice | Row quarantined and affected financial release held; no silent omission |
| **ARCH-AC-05** | Fail after building Sales candidate but before Finance | Both audiences retain old published data; candidate not queryable |
| **ARCH-AC-06** | Simulate ECB timeout / missing required rate | Last release remains; failure visible; no fabricated FX |
| **ARCH-AC-07** | Commit a fully verified new release | All views switch together; only then last-success advances |
| **ARCH-AC-08** | Refresh multi-query dashboard during release switch | All widgets resolve to one pinned release_id |
| **ARCH-AC-09** | Replay identical source/definition versions | No double counting or duplicate report facts |
| **ARCH-AC-10** | Compare Sales and Finance identical metric/version/filters/currency/release | Values match to approved rounding tolerance, else release gate fails |
| **ARCH-AC-11** | Trace one aggregate value backward | Identifiable release, metric version, source hash/row, FX vintage/rate and exception disposition |
| **ARCH-AC-12** | Inspect any unapproved revenue/cancellation/high-value KPI | Clearly marked **TBA**, not represented as accounting truth |

## 11. Open architecture decisions and sign-off

| Open decision | Owner | Blocks |
|---|---|---|
| Revenue definition, tax/shipping/fees, recognized date, cancellations, historic restatements | Michael + Sarah | Finance-approved marts |
| FX reporting currency, observation date, non-business-day fallback, maximum lookback and rounding | Michael | EUR reports |
| Duplicate-row/adjustment policy and independent ledger reference | Michael + Daniel | Financial reconciliation |
| Customer purchasing criteria, guest/unknown handling and high-value definition | Emma | Customer-ranking KPIs |
| Cutoff, refresh cadence, staleness, retry limits and incident ownership | Daniel + Sarah | Operational SLA |
| Metric definition authority, release-scope changes, access/retention | Sponsor + Daniel | Business sign-off |

**Decision:** Architecture ready for team discussion and validation against the DE-004 acceptance criteria; **not** a deployed implementation nor approved accounting specification.

## 12. References

- [Business requirements — DE-001](../../business/requirements.md)
- [Source profiling — DE-002](../../docs/data/source-profiling.md)
- [Data contracts — DE-003 reviewed](../../docs/data/data-contracts.md)
- [Recorded profiling evidence](../../profiling_evidence.json)
- [DE-004 KPI/metric definitions](kli_definitions.md)

**Evidence note:** Source profiling results are taken from repository artifacts, not recomputed in this task. Architecture assertions and failure walkthroughs are design proposals, not completed runtime tests.
