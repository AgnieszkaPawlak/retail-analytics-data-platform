# Northstar Retail — Source Data Contracts (DE-003)

**Document ID:** DC-DE-003  
**Version:** 0.2 — technical review and targeted corrections  
**Status:** TECHNICALLY REVIEWED; business approvals and empirical validator tests pending  
**Date:** 2026-11-02  
**Scope:** UCI Online Retail (dataset 352) and ECB EXR daily GBP/EUR reference rates  
**Business context:** DE-001 Business Requirements; DE-002 Source Profiling  
**Accountable reviewers:** Daniel (engineering), Michael (financial semantics), Sarah (sales reporting), Emma (customer analytics)  
**Delivery:** Contract specifications only; implementation architecture, pipeline design and software selection are out of scope. This document is the reviewed reference copy; the original submission remains in `robocze/DE-003/data_contracts.md`.

## 1. Purpose and governing principles

Northstar Retail needs deterministic rules for accepting source data, classifying exceptions, and determining whether an internally consistent set of reports may be published. A contract breach must never silently change revenue or expose partially refreshed numbers.

The following principles are mandatory for the proposed design:

1. **Preserve raw evidence.** Never silently drop, overwrite, impute or mutate an original source record. Keep source identity, retrieval time, content hash and reason for each exception.
2. **Differentiate validity from business meaning.** A negative Quantity, zero UnitPrice, missing CustomerID or repeated invoice line is not automatically corrupt. Its treatment depends on a documented rule and metric-specific eligibility.
3. **Separate receipt from publication.** A source batch can be received and profiled while still being **not eligible for publication**. A failed or partially validated candidate must not replace the last accepted, consistent published state (FR-11).
4. **No invented relationships or financial policy.** A C-prefixed invoice is a cancellation indicator, not proof of linkage to its original invoice. Quantity × UnitPrice is an exploratory signed line amount, not an approved definition of revenue.
5. **Contract versioning and replayability.** Record the source fingerprint and contract version with every evaluation. Reprocessing the same source under the same rules should yield the same classifications; deliberate source revisions require their own recorded version.
6. **No unapproved thresholds as facts.** The proposal makes structural and arithmetic safety checks firm, but business-specific percentages, time limits, classification and foreign-exchange policies are **TBA** until approved.

### 1.1 Classification, severity and required responses

| Severity | Meaning | Default response |
|---|---|---|
| **CRITICAL** | Whole response/batch cannot be safely interpreted, source identity is wrong, or accepting it would undermine report-wide consistency. | **REJECT_BATCH**: do not accept the candidate for publication; retain the prior successfully published state; log and escalate. |
| **ERROR** | One or more records cannot be correctly interpreted or used for a specified measure. | **QUARANTINE_ROW / EXCLUDE_RATE**: preserve raw input and a reason code; block dependent publication while any financially material exception remains unresolved or lacks an approved exclusion policy. |
| **WARNING** | A record is structurally usable but semantically ambiguous, unusual or incomplete for some analyses. | **RETAIN_FLAG**: retain in source-level totals, mark its classification; restrict only the affected downstream metric under an approved rule; track and alert as agreed. |
| **INFO** | Expected variation or an operational observation to measure. | **ACCEPT_MONITOR / NO_OP**: include in quality metrics and lineage; already accepted input may be recognized as a harmless replay without changing published results. |

**Precedence:** CRITICAL overrides other severities. An ERROR in a required financial value does not become harmless simply because it affects only one row: the record is isolated, while **publication of dependent financial results remains on hold** until the exception is accounted for. An accepted batch and a publishable report are separate decisions.

**Exception disposition values:** OPEN, UNDER_REVIEW, APPROVED_EXCEPTION (with owner, justification and expiry), RESOLVED. Approval must state which measures may exclude an exception and whether financial reconciliation remains valid.

### 1.2 Scope, granularity and contract inputs

| Source | Contracted unit | Input identity | Expected behavior |
|---|---|---|---|
| **SRC-01 UCI** | One XLSX export containing individual **invoice-line observations**, not one record per invoice | UCI dataset 352, file hash, retrieval timestamp, dataset publication reference | Historical snapshot (2010-12-01 through 2011-12-09); no promise of live transaction updates |
| **SRC-02 ECB** | One requested series snapshot with individual **date/rate observations** | EXR series D.GBP.EUR.SP00.A, request parameters, response hash, retrieval timestamp and vintage | Historical daily reference series; not every calendar day has a published rate |

**Required evidence per evaluated batch:** source ID; contract version; source file or API URL and parameters; UTC retrieval and validation times; original content SHA-256; input record count; counts by rule and disposition; acceptance and publication eligibility decision; last successful published update; reviewer/override details when applicable. Data must remain auditable without relying on a particular storage or orchestration tool.

## 2. Profiling baseline and evidence quality

The following numbers are copied from the repository's **profiling_evidence.json**, recorded 2026-11-02 12:45:28 UTC. It reports UCI status **measured_from_download** and ECB status **response_observed**. They were **read from the repository, not independently recomputed for this contract**, and therefore are an observed baseline supplied by the project, not approved quality targets.

| Metric | Recorded result | Contract implication |
|---|---:|---|
| UCI records | 541,909 | Establishes historical baseline only, not a hard-coded count for all future batches |
| UCI missing CustomerID | 135,080 (24.9267%) | Must remain admissible for source-level sales; customer-specific analysis has lower coverage |
| UCI missing Description | 1,454 (0.2683%) | Nullable label, not a reason to discard monetary facts |
| UCI exact repeated rows (beyond first) | 5,268 | Potential duplicates, not independently proven incorrect lines |
| UCI repeated InvoiceNo + StockCode (beyond first) | 10,684 | This pair is **not** a guaranteed line key |
| UCI C-prefixed invoice rows | 9,288 | Cancellation indicator only |
| UCI rows with negative Quantity | 10,624 | 1,336 negative-quantity rows do **not** have a C prefix; require investigation |
| UCI zero UnitPrice / negative UnitPrice | 2,515 / 2 | Need explicit treatment; do not infer all are invalid retail orders |
| UCI date coverage | 2010-12-01 to 2011-12-09 | 305 days with records; 69 calendar dates without transactions are not automatically source outages |
| ECB HTTP response | 200; text/csv | Status 200 alone is insufficient for data quality acceptance |
| ECB date observations | 268, from 2010-12-01 through 2011-12-09 | Not daily calendar coverage |
| ECB missing or invalid OBS_VALUE | 2 | Non-usable observations must be identified, not converted using a fake rate |
| ECB unexpected series / duplicate dates / nonpositive rates | 0 / 0 / 0 | Snapshot observations; recheck each retrieval |

UCI source SHA-256 recorded: **43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d**.  
ECB response SHA-256 recorded: **451245e2eb899ddab2c7e58de6ad270eb9854ee7e6e875b1c9295c7f84ad9bb0**.

**Evidence caveat:** The originally committed `profiling_evidence.json` contained unquoted `NaN` tokens in nested sample metadata. That is a **profiling-artifact serialization defect**, not proof that the UCI or ECB feed was corrupt. During the DE-003 review, a copy of the original artifact was archived, the active evidence was normalized to strict JSON (`null` for nonfinite sample metadata), and the profiling script was updated to enforce strict JSON output. Source measurements and hashes were not recomputed during this correction; independent reconciliation and business sign-off remain open.

## 3. Contract SRC-01 — UCI Online Retail

### 3.1 Physical and semantic schema

| Column | Contract type | Required field? | Nullable value? | Interpretation |
|---|---|---|---|---|
| **InvoiceNo** | Nonempty string; preserve original code and C prefix | Yes | **No** | Invoice/transaction reference, repeated across items; not a row key |
| **StockCode** | Nonempty string; nonnumeric product/service codes allowed | Yes | **No** | Item/service code; no rigid five-digit regex |
| **Description** | String | Yes | **Yes** | Optional descriptive label; not stable identity |
| **Quantity** | Signed integer, exactly representable | Yes | **No** | Source line quantity; signed to accommodate adjustments |
| **InvoiceDate** | Parseable date and time, source time zone unspecified | Yes | **No** | Invoice-generation timestamp; not payment/recognition timestamp |
| **UnitPrice** | Finite decimal numeric amount, currency **GBP** | Yes | **No** | Unit price, may require special handling at zero/negative values |
| **CustomerID** | Nullable string identifier; convert integral Excel numeric IDs losslessly | Yes | **Yes** | Customer identifier where available; must not become "nan" or receive a fabricated ID |
| **Country** | Nonempty string/categorical | Yes | **No** | Reported customer residence, not source currency or necessarily shipping country |

A field being **required** in the schema means its column must exist; it does **not** mean every value in nullable Description or CustomerID must be populated. No source-native line-item ID, original-return invoice reference, accounting ledger, taxes, shipping, or payment/recognition fields are supplied.

### 3.2 Schema validation rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **UCI-SCH-01** | Source is readable as the expected dataset-352 XLSX workbook; not an HTML error page, corrupt ZIP or unrelated workbook. | CRITICAL | REJECT_BATCH; record acquisition failure and preserve previous publication. | Wrong/corrupt input cannot support trusted Sales/Finance reporting (FR-01, FR-11). |
| **UCI-SCH-02** | Exactly one unambiguous instance of each of the eight named columns is present; no required column is absent or duplicated. | CRITICAL | REJECT_BATCH; request schema review. | Missing/ambiguous core attributes could silently change totals (FR-03). |
| **UCI-SCH-03** | Unexpected additional columns, reordered columns or metadata changes do not overwrite or redefine existing fields. | WARNING | RETAIN_FLAG batch; preserve extra data, require compatibility review before adopting new semantics. | Allows safe schema evolution without accidental redefinition. |
| **UCI-SCH-04** | InvoiceNo and StockCode can be represented as nonempty strings with stable source spelling; C prefix must not be lost. | ERROR | QUARANTINE_ROW; hold publication of affected money measures pending disposition. | Correct invoice grouping and cancellations depend on identifiers (FR-04/05). |
| **UCI-SCH-05** | Quantity is an exact signed integer (not boolean, fractional or malformed text). | ERROR | QUARANTINE_ROW and block affected monetary publication until resolved. | Inexact quantity distorts sales and refunds (FR-03/05). |
| **UCI-SCH-06** | UnitPrice is numeric, finite and representable at source precision; no NaN, infinity or unparseable value. | ERROR | QUARANTINE_ROW and block affected monetary publication. | Reliable amount arithmetic is non-negotiable (NFR-01). |
| **UCI-SCH-07** | InvoiceDate parses as an actual timestamp; source time zone is **not inferred** or silently converted. | ERROR | QUARANTINE_ROW; block affected time-based reporting until disposition. | An invalid or shifted date changes historical periods (FR-04). |
| **UCI-SCH-08** | CustomerID, if nonnull, converts to a stable textual integral identifier without losing digits or appending a decimal suffix; Description stays nullable text. | WARNING | RETAIN_FLAG or quarantine only the invalid customer identity for customer metrics; do not drop otherwise valid money line. | Preserves revenue while protecting customer grouping (FR-07/08). |
| **UCI-SCH-09** | Country is nonempty text; unknown labels are reported rather than mapped to invented countries. | ERROR | QUARANTINE_ROW for country-based measures; preserve source line and hold any dependent country breakdown if unaccounted. | Geography reports must not silently invent classifications (FR-02). |

### 3.3 Completeness rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **UCI-CMP-01** | InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice and Country must be populated and parseable on each publishable monetary line. | ERROR | QUARANTINE_ROW if invalid; do not publish unreconciled dependent totals. | Core transaction components are necessary for reliable aggregation. |
| **UCI-CMP-02** | Null CustomerID is allowed and measured by row, country, month and cancellation class; cannot be interpreted automatically as a guest. | WARNING | RETAIN_FLAG as unidentified customer; include in approved overall source/sales counts, exclude from identifiable-customer metrics with coverage disclosure. | 24.93% of source lines would otherwise be lost; limits Emma's analysis (FR-07/08). |
| **UCI-CMP-03** | Null Description is allowed and its count is measured; item identity comes from StockCode, not description. | WARNING | RETAIN_FLAG; use an explicit missing-label indicator in applicable breakdowns. | Prevents loss of valid transactions because of an incomplete label. |
| **UCI-CMP-04** | Missingness distributions and changes relative to the approved historical baseline are recorded for each batch; alert tolerance is **TBA**. | WARNING | ACCEPT_MONITOR and issue threshold-based alert once agreed; do not reject merely because CustomerID matches the known high-missingness baseline. | Detects deterioration without incorrectly failing the historical dataset. |

### 3.4 Uniqueness and idempotency rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **UCI-UNI-01** | InvoiceNo is **not** assumed unique per row; many items may share the same invoice number. | INFO | ACCEPT_MONITOR; group by invoice only when calculating invoice-level metrics. | Prevents accidental line loss and understatement. |
| **UCI-UNI-02** | InvoiceNo + StockCode is **not** assumed unique; measure repeated pairs without automatic deletion. | WARNING | RETAIN_FLAG repeated pairs for investigation; publish only under approved line-identity rules. | Recorded 10,684 repeats make naive composite-key deduplication unsafe. |
| **UCI-UNI-03** | An exact duplicate across the eight source fields is a **potential** duplicate, not conclusive proof of an erroneous event. | WARNING | RETAIN_FLAG and quantify financial effect both with and without proposed exclusion; never silently deduplicate. | Recorded 5,268 exact repeats can affect reported totals. |
| **UCI-UNI-04** | A re-ingestion of the **same source hash** under the **same contract version** is identified as an already evaluated input, not as a malformed source batch. | INFO | ACCEPT_MONITOR / NO_OP for a previously accepted snapshot; log the replay and preserve published totals. | A normal idempotent replay should succeed harmlessly rather than appear as a critical data-quality incident. |
| **UCI-UNI-06** | Replaying that unchanged source and contract must never create additional logical published lines or change published totals. | CRITICAL | BLOCK_DEPENDENT_PUBLICATION, retain the last consistent version and investigate if double counting or a changed result is detected. | Detects a genuine idempotency failure, rather than mistaking a normal retry for invalid data (FR-11, NFR-02). |
| **UCI-UNI-05** | A changed source file hash or a changed contract version is a separate evaluated vintage, not a silent replacement. | WARNING | RETAIN_FLAG, version and compare; require authorization before replacing accepted historical results. | Makes history reproducible (NFR-06). |

### 3.5 Validity rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **UCI-VAL-01** | InvoiceDate must be a valid timestamp. Outside the documented 2010-12-01–2011-12-09 window is a source-version anomaly, not automatically impossible. | WARNING | RETAIN_FLAG and investigate scope/version; invalid parsing is handled as UCI-SCH-07. | Avoids mixing historical snapshots or discarding a legitimate documented revision. |
| **UCI-VAL-02** | Quantity = 0 is unusual for an invoice line, but is not proof of corruption without a supplier rule. | WARNING | RETAIN_FLAG; keep out of positive-sale-unit counts under an approved metric rule; never invent units. | Prevents misleading sales-unit KPIs. |
| **UCI-VAL-03** | Quantity < 0 is allowed as a signed adjustment candidate, regardless of InvoiceNo prefix. | WARNING | RETAIN_FLAG with negative-quantity classification; do not turn it positive or auto-delete. | Cancellation/return corrections must remain visible (FR-05). |
| **UCI-VAL-04** | Very large absolute Quantity (including observed ±80,995) is an outlier for investigation, not an unconditional schema failure; numeric threshold **TBA**. | WARNING | RETAIN_FLAG; compare against documented wholesaler/adjustment context and alert thresholds. | Wholesale transactions make blanket outlier rejection unsafe. |
| **UCI-VAL-05** | UnitPrice = 0 is permitted as an exceptional source value, never automatically a paid sale. | WARNING | RETAIN_FLAG as zero-price line; include/exclude from each metric only under approved semantics. | Avoids inflating paid-unit/product KPIs. |
| **UCI-VAL-06** | UnitPrice < 0 is not a standard positive retail unit price; retain for manual business classification. | ERROR | QUARANTINE_ROW from standard paid-product/revenue calculations; block publication if material amount lacks approved handling. | Protects against incorrect charges or undocumented adjustment semantics. |
| **UCI-VAL-07** | Extremely large finite UnitPrice (including observed 38,970) is flagged; no arbitrary upper bound is treated as a known business limit. | WARNING | RETAIN_FLAG and investigate exception, not automatic rejection. | Large fees/adjustments can be valid despite unusual size. |
| **UCI-VAL-08** | Negative Quantity with non-C invoice number, C prefix with nonnegative Quantity, and other sign/prefix inconsistencies are explicitly counted. | WARNING | RETAIN_FLAG for review; do not auto-reclassify or erase. | Source has 1,336 negative-quantity rows without C prefix; they may represent adjustments (FR-05). |
| **UCI-VAL-09** | StockCode may contain letters and service/adjustment codes; Country values are not treated as currency codes. | WARNING | RETAIN_FLAG non-merchandise classifications for approved business review; do not discard by numeric-only SKU regex. | Prevents omission of fees or corrections and mistaken FX treatment. |
| **UCI-VAL-10** | The same invoice has potentially inconsistent dates/country/customer assignments; these inconsistencies are measured, not silently harmonized. | WARNING | RETAIN_FLAG invoice group and request business investigation. | Avoids inconsistent invoice-level and customer views (FR-02/07). |

### 3.6 Business-semantic rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **UCI-BIZ-01** | InvoiceNo starting with C (case-insensitive) indicates a cancellation **candidate** under UCI's source definition. | WARNING | RETAIN_FLAG with cancellation indicator; preserve signed value and original invoice number. | Supports cancellation-aware revenue without inventing details (FR-05). |
| **UCI-BIZ-02** | No explicit original-invoice foreign key or complete partial-refund history exists. A C number is not automatically joined to a supposed original invoice. | WARNING | RETAIN_FLAG as unmatched cancellation when linkage is unproven; disclose limits of historical adjustment analysis. | Incorrect matching can misstate prior-period revenue (NFR-06). |
| **UCI-BIZ-03** | Raw signed line amount may be calculated as Quantity × UnitPrice in GBP, with controlled decimal arithmetic. | INFO | ACCEPT_MONITOR as **source_line_amount_gbp** only; prohibit renaming it to recognized/net revenue before Finance approval. | Michael and Sarah need one approved revenue definition (FR-03). |
| **UCI-BIZ-04** | Original retail prices are in GBP regardless of Country; do not infer transaction currency from residence. | CRITICAL | BLOCK_DEPENDENT_PUBLICATION if a downstream mapping or conversion incorrectly treats the same raw source as another transaction currency; retain the original UCI batch and escalate the semantic mismatch. | Prevents systematically incorrect conversions without misclassifying an otherwise valid input file as corrupt (FR-06). |
| **UCI-BIZ-05** | Product, shipping, discounts, bank charges, postage and adjustments cannot be assumed equivalent merchandise without a business classification. | WARNING | RETAIN_FLAG unknown service/adjustment codes; prohibit unapproved inclusion in a published revenue category. | Finance totals must be explainable (FR-03/09). |
| **UCI-BIZ-06** | Customer value, frequency and repeats use only identified customers, and must state their denominator, exclusion counts and cancellation policy. | WARNING | RETAIN_FLAG coverage caveat; do not invent IDs or treat missing-ID rows as new customers. | Avoids biased customer rankings (FR-07/08). |
| **UCI-BIZ-07** | The archived dataset contains invoice-generation dates, not verified payment/delivery/recognition dates or a financial ledger. | WARNING | RETAIN_FLAG financial-scope limitation; withhold claims of ledger reconciliation or recognized revenue without independent evidence. | Meets honesty and accuracy requirements for Finance (FR-04/09). |

## 4. Contract SRC-02 — ECB exchange rates

### 4.1 Expected data envelope and schema

**Dataflow:** ECB EXR.  
**Requested series:** **D.GBP.EUR.SP00.A** (daily spot reference, amount of **GBP per 1 EUR**).  
**Example request:** https://data-api.ecb.europa.eu/service/data/EXR/D.GBP.EUR.SP00.A?startPeriod=2010-12-01&endPeriod=2011-12-09&format=csvdata  
**Expected response:** CSV with observations, their series dimensions, date and value. Additional attributes may be present; do not require unused optional fields to be nonnull.

| Element | Contract type | Required? | Notes |
|---|---|---|---|
| **KEY** | Series identifier string | Yes for configured full CSV response | Expected EXR.D.GBP.EUR.SP00.A |
| **FREQ** | String | Yes | D |
| **CURRENCY** | String | Yes | GBP |
| **CURRENCY_DENOM** | String | Yes | EUR |
| **EXR_TYPE** | String | Yes | SP00 |
| **EXR_SUFFIX** | String | Yes | A |
| **TIME_PERIOD** | ISO calendar date | Yes | Date of rate observation, not invoice date |
| **OBS_VALUE** | Nullable finite decimal | Column yes; value nullable | Missing/non-numeric observation is **not** a usable conversion rate |
| **OBS_STATUS** | Optional categorical attribute | No (unless specifically contracted format requires it) | Interpret statuses per ECB documentation; do not equate missing status with a valid rate |

**Key semantics:** 0.85 GBP per EUR means GBP→EUR is **GBP amount ÷ 0.85**, not multiplication. The reporting currency, eligible rate date, fallback on non-publication days and rounding are still Michael's decisions (DE-001 OQ-04).

### 4.2 Schema and API-response rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **ECB-SCH-01** | Request identifies the approved dataflow, exact series, date window, response format and retrieval/vintage policy; retain resolved request URL. | CRITICAL | REJECT_BATCH if source identity is incorrect or undocumented. | A rate from another series can misstate all converted revenue (FR-06). |
| **ECB-SCH-02** | HTTP response succeeds and body is parseable CSV of the contracted format. A 200 response with an HTML page or malformed CSV is invalid. | CRITICAL | REJECT_BATCH, record raw error details and preserve previous accepted rates. | HTTP status alone is not sufficient evidence of data correctness. |
| **ECB-SCH-03** | TIME_PERIOD, OBS_VALUE, KEY and the five contracted series dimensions exist and are unambiguous in the selected full CSV format. | CRITICAL | REJECT_BATCH for missing/ambiguous required fields; preserve source response for analysis. | Prevents using dates/rates without currency identity. |
| **ECB-SCH-04** | For every observation, KEY and dimension values match EXR.D.GBP.EUR.SP00.A / D, GBP, EUR, SP00, A. | CRITICAL | REJECT_BATCH on unexpected series mixing or inconsistent dimensions. | Wrong FX direction or reference type is a systemic financial error. |
| **ECB-SCH-05** | Extra metadata/attribute columns or blank optional attributes do not alter the contracted date, value or series fields. | INFO | ACCEPT_MONITOR; retain useful metadata; flag incompatible semantic changes for review. | Normal ECB response metadata should not cause false failures. |

### 4.3 Completeness, uniqueness and validity rules

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **ECB-CMP-01** | TIME_PERIOD is present and parseable; a missing/invalid date makes the observation unusable. | ERROR | EXCLUDE_RATE/QUARANTINE_ROW and block dependent FX publication if required coverage cannot be met. | A rate without a date cannot be assigned to transactions. |
| **ECB-CMP-02** | OBS_VALUE may be missing in an ECB response, but such an observation is **not a usable rate**. | ERROR | EXCLUDE_RATE, count and preserve status/metadata; hold dependent report if no approved fallback covers the required dates. | Repo evidence contains two missing/invalid observations; zero-filling would corrupt revenue. |
| **ECB-CMP-03** | Missing weekends and ECB non-publication dates are expected; no requirement for one observation per calendar day. | INFO | ACCEPT_MONITOR; evaluate against an approved business-day/reference calendar and fallback policy, not raw calendar-day completeness. | Prevents false alerts and invented weekend rates. |
| **ECB-CMP-04** | A required FX date must be resolvable under Michael's approved date-selection/lookback policy; a maximum lookback is **TBA**. | CRITICAL | BLOCK_DEPENDENT_PUBLICATION when no approved usable rate can be selected; do not invent, forward-fill without approval or substitute a future rate. | Financial reports must apply consistent historical FX rules (FR-06). |
| **ECB-UNI-01** | Within one response/vintage, each (series KEY, TIME_PERIOD) resolves to at most one unambiguous usable observation. | CRITICAL | REJECT_BATCH if conflicting values occur for the same key/date; log both observations. | Conflicting FX values make converted totals nondeterministic. |
| **ECB-UNI-02** | Identical repeated observations and overlapping fetches do not duplicate stored rate dates or change already accepted results; revisions are separately versioned. | WARNING | Treat exact replays as idempotent NO-OP; flag new or revised vintages for controlled evaluation. | Ensures reproducibility (NFR-06). |
| **ECB-VAL-01** | TIME_PERIOD is a real date and falls within the explicitly requested window. | ERROR | EXCLUDE_RATE and investigate; reject whole batch if systematic window mismatch shows wrong response. | Rates outside the requested historical scope are not automatically relevant. |
| **ECB-VAL-02** | Every rate chosen for conversion is finite, strictly greater than zero and parseable as a decimal. | ERROR | EXCLUDE_RATE; block dependent reporting if required rate becomes unavailable. | Division by zero/negative/nonfinite rate is invalid (FR-06). |
| **ECB-VAL-03** | OBS_STATUS and other relevant observation flags must not be silently ignored when they indicate missing, break, revised or otherwise unsuitable data. | WARNING | RETAIN_FLAG; require approved status-eligibility policy before conversion. | A published figure needs a traceable authoritative observation. |
| **ECB-VAL-04** | Rate direction is consistently GBP per EUR. Converting GBP→EUR divides by OBS_VALUE, preserving original GBP amount and selected rate. | CRITICAL | BLOCK_DEPENDENT_PUBLICATION on inverted formula or changed currency meaning; correct and retest. | Incorrect FX arithmetic affects every converted revenue figure. |
| **ECB-VAL-05** | Extreme rate movements relative to adjacent valid observations are flagged with a business-approved tolerance (**TBA**); no plausible rate is silently clipped. | WARNING | RETAIN_FLAG and review; retain source value and vintage. | Detects data or series changes without fabricating market values. |
| **ECB-VAL-06** | Retrieval timestamps, response hash, rate vintage and applied rate date are traceable; historical revisions must not silently change a previously published basis. | ERROR | Version revised observations; hold historical restatement until policy and impact are approved. | Supports auditable financial reporting (NFR-06). |

### 4.4 API failures and partial responses

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **ECB-API-01** | Connection timeout, DNS/TLS failure, 5xx, 429 or temporary upstream error prevents retrieving the required snapshot. | CRITICAL | REJECT_BATCH / mark retrieval FAILED; retry only under documented bounded policy (limits/backoff TBA); do not replace accepted rates. | External API outages must not produce inconsistent figures (FR-11/12). |
| **ECB-API-02** | 4xx errors other than a documented valid conditional-request response, wrong series, or invalid query parameters occur. | CRITICAL | REJECT_BATCH, surface actionable error and require configuration fix rather than unbounded retry. | Source/configuration mistakes should not masquerade as fresh rates. |
| **ECB-API-03** | If incremental requests are introduced, documented HTTP 304 / unchanged result is not treated as a corrupted data response; a successful unchanged state must be traceable to an already accepted vintage. | INFO | ACCEPT_MONITOR as NO_CHANGE only when existing coverage and identity are verified; otherwise fail safe. | Keeps freshness truthful without inventing new observations. |
| **ECB-API-04** | API returns 200 but no usable requested observations, or coverage is incomplete for a report's required FX dates. | CRITICAL | BLOCK_DEPENDENT_PUBLICATION until completeness policy passes; previous consistent published state stays visible. | A superficially successful API call is not a valid financial update. |

## 5. Cross-source consistency and publication controls

These are contractual obligations on the **data presented to consumers**, independent of implementation technology.

| ID | Validation condition | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **ALL-PUB-01** | A report version is published only if **all inputs required for that report** have passed structural checks and material exceptions have approved dispositions. | CRITICAL | BLOCK_DEPENDENT_PUBLICATION; retain the last complete, consistent report version. | A failed refresh cannot expose mixed/partial data (FR-11). |
| **ALL-PUB-02** | Sales and Finance asking for the same approved metric, filters, period, currency and published version must obtain the same result. | CRITICAL | BLOCK publication or roll back an inconsistent candidate; alert owner. | Single Source of Truth is defined by shared metrics, not a single physical database (FR-03, NFR-02). |
| **ALL-PUB-03** | Every published result identifies data coverage period, last successful **publication** time, applicable source vintages, and any stale/failed state. | ERROR | Keep previous version and mark stale/failed; do not present candidate processing time as a success timestamp. | Required by Daniel (FR-10/12). |
| **ALL-PUB-04** | GBP-only reports may be independently publishable if all their required UCI checks pass; EUR/FX-dependent reports must additionally satisfy ECB and approved FX date policy. | WARNING | Scope the hold to **dependent report families** if and only if that separation is formally defined and cross-report consistency remains valid. | Avoids unnecessary outage without letting Finance see inconsistent EUR figures. |
| **ALL-PUB-05** | All rejected, quarantined, unmatched or excluded financial lines and unused FX dates must be measurable and traceable to their potential impact. | ERROR | HOLD dependent publication until the impact is reconciled or explicitly approved; publish exception coverage if allowed. | Silent omissions undermine reconciliation (FR-09). |
| **ALL-PUB-06** | The actual independent finance reconciliation ledger is not part of these two feeds. A controlled reference test is not represented as ledger reconciliation. | WARNING | Disclose missing source and keep FR-09 status CONDITIONAL/UNMET until approved external benchmark exists. | Prevents unsupported claims of finance-grade accuracy. |

### 5.1 Deterministic decision order

1. **Identify input**: match registered dataset/series, requested period, contract version and source fingerprint.
2. **Validate batch envelope**: transport, file/CSV parseability, schema and series identity. Any CRITICAL failure rejects the candidate.
3. **Inspect all records**: classify record-level ERROR, WARNING and INFO findings; preserve raw rows and reasons.
4. **Determine metric eligibility**: sales, Finance, customer, geographic and currency measures may have different required fields. Use only approved business exclusions/transformations.
5. **Apply dependency gates**: check complete revenue/cancellation policy and, for converted results, ECB conversion coverage; unresolved financial impact blocks dependent publication.
6. **Publish consistently or not at all for each defined report family**: label the accepted version and success timestamp; a failed candidate leaves the prior version intact.
7. **Monitor and reconcile**: record rule counts, rejected and quarantined values, coverage, freshness and dispositions; make failed/stale status visible.

### 5.2 Example outcomes

| Example input / failure | Correct default | Must NOT happen |
|---|---|---|
| UCI line has null CustomerID but valid invoice, quantity, date and price | Retain for source/sales totals; tag unidentified for customer metrics | Delete entire line or generate imaginary customer ID |
| UCI contains exact repeated rows | Flag, count and investigate; do not remove automatically | Assume the repeated rows are definitely errors |
| UCI row has negative Quantity with no C prefix | Retain and flag as ambiguous adjustment | Discard it or automatically assert it is a cancellation |
| UCI line has malformed Quantity | Quarantine line; hold affected financial publication until reconciled | Publish a smaller total with no warning |
| ECB observation has null OBS_VALUE | Preserve observation metadata, exclude as a rate; check approved fallback | Replace null with zero or divide by zero |
| ECB has no weekend observation | Do not classify as an API outage by itself | Require 365/365 daily rates or use a future rate silently |
| ECB endpoint returns 500 | Mark failed and retain previous accepted financial state | Mark report refreshed with partially updated rates |
| New batch fails after processing some records | Candidate not published; last accepted report stays complete | Expose partial new totals as successful |

## 6. Error handling: row versus batch versus publication

| Failure level | Trigger | Response | Audit/notification |
|---|---|---|---|
| **Acquisition failure** | File unreachable; API timeout/5xx/429 | No replacement batch; bounded retry policy TBA | Source, time, error category, retry count, owner alert |
| **Batch structural failure** | Missing required columns; corrupt format; wrong ECB series/currency | Reject whole batch, fail closed | Batch ID/hash, contract version, specific failed rule |
| **Record error** | Invalid core UCI numeric/timestamp value or unusable ECB observation | Isolate affected row/observation; preserve raw content and reason | Row fingerprint/position, failed rule, affected measure and value |
| **Record warning** | Null CustomerID, unusual negative quantity, potential duplicate, extreme value | Retain with warning; monitor and apply approved metric-specific classification | Warning counts and distribution, review status |
| **Business-policy gap** | Unknown revenue recognition, ambiguous cancellation matching, missing approved FX fallback | Hold affected metric publication; ask responsible owner to decide | Open question, impact, owner, decision version |
| **Publish failure** | Mixed source vintages, unresolved monetary exceptions, inconsistent totals | Do not replace existing report; mark failed/stale | Last successful publication, failed candidate, affected report(s) |

**No global hard-coded percentage of bad rows should automatically permit losing financially material values.** Structural integrity and zero silently omitted financial value are the initial safety invariants. Quantitative alert/rejection thresholds for noncritical anomalies must be approved based on the measurement baseline and desired service level.

## 7. Data quality monitoring contract

### 7.1 Metrics, grouping and alerts

Each monitoring rule below has the same fields as ingestion rules and applies to every evaluated batch. For every metric, retain its numerator, denominator, percentage, source ID, retrieval time, contract version and comparison to the approved baseline.

| ID | Validation / measure | Severity | Expected system reaction | Business rationale |
|---|---|---|---|---|
| **DQM-01** | Report counts and percentages of required-column and type violations for each source; acceptable structural failures = **0** per accepted batch. | CRITICAL | REJECT_BATCH if schema invalid; alert engineering with rule-level counts. | Avoids corrupt or misinterpreted updates. |
| **DQM-02** | UCI null rates by column, month, country and cancellation class; compare CustomerID 24.9267% and Description 0.2683% to validated baseline; drift threshold TBA. | WARNING | ACCEPT_MONITOR with anomaly alert when approved threshold exceeded. | Detects changing customer-analytics coverage. |
| **DQM-03** | Track exact duplicates, repeated invoice-stock pairs and source-hash replays as **separate** metrics. | WARNING | RETAIN_FLAG; notify on drift; no automatic row deletion; idempotent duplicate input produces no new output. | Prevents double counting and false deduplication. |
| **DQM-04** | Track negative/zero quantity, zero/negative price, C-prefix, negative-without-C, outlier counts and their **signed monetary impact**. | WARNING | RETAIN_FLAG and alert on approved impact/drift thresholds; escalate unresolved financial materiality. | Reveals sources of discrepancy in Sales/Finance figures. |
| **DQM-05** | Count invalid dates, active calendar days, absent calendar days, coverage endpoints, monthly volume and unusual temporal gaps; thresholds TBA. | WARNING | ACCEPT_MONITOR and investigate changes; do not treat weekends/closed days as missing data automatically. | Protects historical-period comparisons. |
| **DQM-06** | ECB checks: response code, latency, observations, missing rates, usable-rate ratio, duplicate/conflicting dates, unexpected series, revisions and FX-date coverage for each dependent report. | CRITICAL | Alert; BLOCK_DEPENDENT_PUBLICATION when required coverage or identity fails. | Prevents silent FX gaps or incorrect conversions. |
| **DQM-07** | Track accepted/quarantined/rejected observations, unresolved exceptions, affected GBP value and report eligibility per source and report. | ERROR | Escalate material unresolved exceptions; do not publish silently incomplete amounts. | Makes quality decisions financially auditable. |
| **DQM-08** | Track last successful published version/time, report data-through date, processing failure and staleness vs agreed Monday cutoff (TBA). | ERROR | Mark failed/stale accurately and notify designated owners; keep prior accepted report. | Daniel's required operational transparency (FR-10/12). |
| **DQM-09** | Quality evidence itself must be strict, machine-readable JSON if JSON is the chosen evidence format: no unquoted NaN/Infinity literals, missing essential metadata or ambiguous null encoding. | ERROR | Fail the evidence artifact, re-serialize nonfinite sample metadata as JSON null, verify strict JSON parsing and preserve the unmodified original for audit; do not fabricate source anomalies. | Prevents an invalid JSON evidence file from hiding breaches or breaking audits. |
| **DQM-10** | Track report-to-report consistency and signed reference-case reconciliation results under identical filters, currency and metric version. | CRITICAL | Block or reject candidate publication if results differ beyond signed-off tolerance (TBA); record variance. | Ensures consistent Sales/Finance figures (FR-03/09). |

### 7.2 Required quality-report contents

At minimum a **per-batch Data Quality Report** shall include:
- identity: source, batch/request ID, source SHA-256, UTC run time, input period, contract version and source vintage;
- decisions: ACQUIRED / REJECTED / ACCEPTED_WITH_WARNINGS, publication eligibility, affected report families, last successful publication;
- statistics: input and valid rows/observations, quarantined and warning counts, null percentages, duplicate candidates, temporal coverage, anomaly counts, usable FX coverage;
- financial impact: total/source signed GBP amount and any unreconciled or held amount, **without labelling it recognized revenue before policy approval**;
- exceptions: failed rule IDs, representative non-sensitive samples or fingerprints, owners, dispositions and remediation status;
- freshness: data-through period, last success, current failed/stale state and agreed SLA compliance status.

**Proposed default operating stance:** alert on **any CRITICAL event** and on **any unresolved financially material ERROR**. For known historical baseline anomalies, monitor trend until business owners approve thresholds; no invented “5% maximum missing CustomerID” is used because the historical source already exceeds it.

## 8. Acceptance tests for the contracts

These are deterministic examples to test **when a validator is implemented**. They are not claims that such tests have already run.

| Test | Fixture or scenario | Expected result | Covered rules |
|---|---|---|---|
| **DC-AT-01** | Correct UCI eight-column schema and source snapshot | Valid candidate with warnings where documented anomalies occur; no arbitrary removal | UCI-SCH-01/02; UCI-CMP-02/03 |
| **DC-AT-02** | Remove Quantity column from a UCI fixture | Whole batch rejected; prior report unchanged | UCI-SCH-02; ALL-PUB-01 |
| **DC-AT-03** | Add a line with unparseable UnitPrice | Line quarantined; dependent revenue publication held pending approved disposition | UCI-SCH-06; ALL-PUB-05 |
| **DC-AT-04** | Null CustomerID on an otherwise valid sale | Line preserved in source/sales totals; not assigned to an invented customer | UCI-CMP-02; UCI-BIZ-06 |
| **DC-AT-05** | Two identical UCI lines; two same InvoiceNo+StockCode lines | Both types flagged; no unapproved line deduplication | UCI-UNI-02/03 |
| **DC-AT-06** | Re-run same snapshot SHA and contract version | Already accepted snapshot is recognized as a normal no-op and published totals remain unchanged | UCI-UNI-04 |
| **DC-AT-17** | Deliberately simulate a replay that would double-count previously accepted lines | Reject inconsistent candidate publication, alert owner, and retain last consistent results | UCI-UNI-06 |
| **DC-AT-07** | Negative Quantity on a non-C invoice | Retained and flagged as ambiguous, not silently discarded or reclassified | UCI-VAL-03/08 |
| **DC-AT-08** | GBP 100 and illustrative GBP/EUR 0.80 with signed-off conversion policy | EUR amount 125 before rounding, using division and traceable observation | ECB-VAL-04; UCI-BIZ-04 |
| **DC-AT-09** | ECB response with wrong CURRENCY_DENOM | Whole ECB batch rejected; dependent conversion not published | ECB-SCH-04 |
| **DC-AT-10** | ECB rate is null or zero on a needed date | Rate excluded; dependent report blocked unless approved eligible prior-date fallback applies | ECB-CMP-02/04; ECB-VAL-02 |
| **DC-AT-11** | Date on weekend with no ECB observation | No automatic outage; select rate only under approved fallback rule | ECB-CMP-03/04 |
| **DC-AT-12** | HTTP 500 or malformed CSV after previously accepted rates | Candidate fails; older consistent financial report remains; status indicates failure | ECB-API-01; ALL-PUB-01/03 |
| **DC-AT-13** | UCI accepted; ECB failed; GBP-only and EUR report families explicitly separated | GBP-only may proceed if approved; EUR report remains at last accepted state | ALL-PUB-04 |
| **DC-AT-14** | Partly processed candidate fails before publication | No newly mixed totals visible; last published state unchanged | ALL-PUB-01/02 |
| **DC-AT-15** | Evidence serializer outputs raw NaN token in JSON | Evidence rejected as invalid JSON and regenerated with null | DQM-09 |
| **DC-AT-16** | Same revenue metric/period/filters/currency/version in Sales and Finance | Matching results within approved numeric tolerance; discrepancy fails acceptance | ALL-PUB-02; DQM-10 |

## 9. Business-requirements traceability

| BRS item | Contract coverage | Remaining limit |
|---|---|---|
| **FR-01/02** recurring sales report and breakdowns | UCI-SCH, UCI-CMP, UCI-UNI, UCI-VAL, DQM-05 | Exact Monday report scope, cutoff and dimensions remain TBA |
| **FR-03/04/13** approved historical revenue definitions | UCI-BIZ-03/05/07, ALL-PUB-02, DQM-10 | Gross/net/tax/shipping/date recognition are not defined by source |
| **FR-05** cancellations and corrections | UCI-VAL-03/08, UCI-BIZ-01/02 | Original-invoice linkage and full historical adjustment lineage unavailable |
| **FR-06** currency conversion | UCI-BIZ-04, ECB-CMP/VAL, ECB-API | Reporting currency, date selection, lookback, rounding and restatements require Michael |
| **FR-07/08** customer behavior and value | UCI-CMP-02, UCI-BIZ-06, DQM-02 | Missing CustomerID and customer-value policy limit accuracy |
| **FR-09** finance reconciliation | ALL-PUB-05/06, DQM-10 | Independent finance ledger has not been supplied |
| **FR-10/11/12** freshness and failure consistency | ALL-PUB-01/03/04, DQM-08, error-handling policy | Service cutoff, alert ownership and recovery SLAs are TBA |
| **NFR-01/02/03/06** accuracy, consistency, resilience, reproducibility | Structural gates, idempotency, source/vintage lineage, no-partial-publish controls | Implementation and proof of these properties are future tasks |

## 10. Open decisions, assumptions and contract change control

| Decision | Proposed owner | Required before |
|---|---|---|
| What is net/gross/recognized revenue; how taxes, postage, discounts and fees are counted? | **Michael + Sarah** | Approval of financial metric eligibility and reconciliation |
| Are signed negative non-C rows and all C rows considered cancellations, adjustments or separate financial events? | **Michael** | Cancellation-aware revenue publication |
| Are any exact duplicate-looking lines source errors? Is there an authoritative line ID or invoice ledger? | **Michael + Daniel** | Deleting or aggregating them as deduplicated facts |
| Which metrics may exclude quarantined financial lines, and what exception sign-off is sufficient? | **Michael + Daniel** | Financial batch publish gate |
| What currency, rate date, non-working-day fallback, maximum lookback, rounding and FX revision/restatement policy apply? | **Michael** | Converted reports |
| What are acceptable missing-customer coverage, anomaly drift and alert thresholds? | **Emma + Daniel** | Customer reporting SLA and monitoring alert tuning |
| Which report families may publish independently; what is the Monday cutoff and failure notification target? | **Sarah + Daniel** | Production publication and freshness SLA |
| What independent finance source/reference cases prove correct historical revenue? | **Michael** | FR-09 reconciliation sign-off |
| Who approves a new contract version, exception override and historical restatement? | **Business sponsor + Daniel** | First accepted baseline |

**Proposed assumptions (not stakeholder decisions):** UCI dataset 352 remains the designated historical sample; UCI prices are GBP; ECB EXR/D.GBP.EUR.SP00.A remains the selected reference series; historical data replays simulate refreshes rather than real operational sales events.

**Change management:** Any alteration to field meaning, requiredness, exception eligibility, currency interpretation or accepted historical results requires a new contract version, an impact assessment on dependent reports, reproducible tests and approval from the relevant owner. Breaking changes must not silently overwrite existing accepted results.

## 11. Sign-off and readiness

**Decision:** **ENGINEERING REVIEW COMPLETED WITH CORRECTIONS; NOT BUSINESS-APPROVED OR IMPLEMENTED.** The contract identifies proposed deterministic controls and explicit policy gaps. Implementations should not silently choose financial definitions, exception thresholds or FX fallback behaviors.

**Minimum approval conditions:**
1. Daniel approves batch/record/publication failure boundaries and quality telemetry.
2. Michael approves financial exception treatments, cancellation, FX and reconciliation rules.
3. Sarah approves report scope, identical-metric consistency and publication cutoff.
4. Emma approves identified-customer metric coverage and high-value-customer semantics.
5. Contract tests DC-AT-01 through DC-AT-17 are implemented and evidenced separately; no test execution is claimed by this document.

**Status:** Daniel — pending; Michael — pending; Sarah — pending; Emma — pending; final sponsor — not assigned.

## 12. References and provenance

**Project source material — only outside the working folder:**
- [DE-001 business requirements, v0.2](../../business/requirements.md)
- [DE-002 source profiling review](../../docs/data/source-profiling.md)
- [Source measurements / API response evidence](../../profiling_evidence.json) (2026-11-02 recorded snapshot; normalized to strict JSON during DE-003 review, no new measurement)
- [Profile collector script](../../scripts/profiling/profile_sources.py) (strict JSON serialization enabled in DE-003 review)
- [Project README](../../README.md)

**Official documentation:**
- [UCI Online Retail dataset 352](https://archive.ics.uci.edu/dataset/352/online+retail)
- [ECB Data API documentation](https://data.ecb.europa.eu/help/api/data)
- [ECB Data API examples](https://data.ecb.europa.eu/help/api/data-examples)

**Provenance note:** Repository measurements were consulted but not independently reexecuted. Every proposed rule above is a **contract requirement**, not a result of executing a validator. Thresholds and business semantics explicitly marked **TBA** require sign-off.

## 13. Technical Lead Review — v0.2

**Reviewed input:** `robocze/DE-003/data_contracts.md`. This version retains the proposed business semantics and source-data limitations. It does not imply stakeholder sign-off or successful execution of the 17 future acceptance tests.

| Change | Review rationale |
|---|---|
| Archived original submission | Original document is preserved under the normalized `robocze/DE-003/` ticket folder for comparison. |
| Corrected replay severity (`UCI-UNI-04`) | A normal second delivery of the same accepted input is a valid idempotent NO-OP, not a critical ingestion failure. |
| Added `UCI-UNI-06` and `DC-AT-17` | A *real* idempotency defect—duplicate published rows or changed totals after replay—must be a critical publication failure and separately testable. |
| Corrected `UCI-BIZ-04` reaction | Incorrect downstream currency interpretation should block affected publication, not falsely classify the original GBP source file as corrupted. |
| Corrected JSON-evidence handling | Previous evidence contained invalid bare NaN tokens. Original evidence is preserved; working copy is serialized as strict JSON and the collector prevents reintroduction. |
| Clarified review state | Technical review is complete; final business approval, policy decisions, data-source reconciliation and validator execution are still pending. |

**Outstanding DE-003 conditions:** Finance must approve the meaning and eligibility of published monetary measures, FX fallback and cancellation policy; Engineering must approve report-family publication boundaries; customer analytics must approve identified-customer coverage. The recorded profiling baseline needs independent source-hash verification before it is elevated from project evidence to signed baseline.
