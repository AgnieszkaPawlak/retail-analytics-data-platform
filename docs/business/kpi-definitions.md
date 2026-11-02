# Northstar Retail — Business KPI & Metric Definitions

**Document ID:** KPI-DE-004  
**Version:** 0.2 — reviewed semantic metric catalogue  
**Status:** TECHNICALLY REVIEWED; proposed official KPI definitions remain **TBA** until stakeholder approval  
**Date:** 2026-11-02  
**Companion architecture:** [architecture.md](../architecture/architecture.md)  
**Filename:** Standardized to **kpi-definitions.md** in the reviewed documentation. The original user submission is retained unchanged in `robocze/DE-004/kli_definitions.md`.  
**References:** [DE-001 requirements](../../business/requirements.md), [DE-002 profiling](../../docs/data/source-profiling.md), [DE-003 data contracts](../../docs/data/data-contracts.md), [profiling evidence](../../profiling_evidence.json).

## 1. Purpose and metric governance

Sales and Finance must not create competing definitions of the same KPI. Each metric needs one owner, an explicit formula and eligibility policy, a declared aggregation grain, approved date and currency handling, and a versioned implementation in shared semantic models.

**A value derived from raw invoice fields is not automatically an accounting definition of revenue.** The UCI data does not establish recognized revenue, full return history, taxes, discounts, shipping accounting, payment status or a finance ledger. In this catalogue, a **DIAGNOSTIC** measure can be computed from source observations without claiming business approval. An **OFFICIAL KPI — TBA** is a proposed interface **not publishable as an approved business metric** until its open decisions are resolved.

### 1.1 Metric record contract

Each published/validated measure must carry:
- **metric_id, metric_version, status and owner**;
- business name, meaning, unit/currency and calculation formula;
- **grain** and allowed reporting dimensions; event/reporting date basis and time zone;
- required source fields, eligibility/exclusion policy and dependency on FX/cancellation rules;
- **release_id** and input source/vintage IDs (and ECB observation metadata for EUR);
- population size, unidentified/excluded/flagged coverage and quality limitations;
- verification fixture, expected result and approval record.

**Metric identity for comparison:** metric_id + metric_version + date_basis + reporting period + filters/dimensions + currency + release_id. Matching these fields must yield identical Sales and Finance results (DE-003 ALL-PUB-02); different business concepts must have different metric IDs.

**Default scope:** Same global published release for Sales, Finance and Customer reporting. A downstream dashboard is not allowed to redefine line eligibility, sum a different period, or choose a different FX rate. Report widgets pin one release_id for the full refresh.

### 1.2 What the sources actually contain

- **UCI Online Retail:** eight fields (InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country), grain **invoice line**, original UnitPrice in **GBP**. InvoiceNo repeats; the pair InvoiceNo + StockCode also repeats. A C-prefixed invoice denotes a cancellation candidate but does not give a verified foreign key to an original invoice.
- **CustomerID** may be missing; the committed profiling evidence records **135,080 missing values from 541,909 lines**, not necessarily 135,080 unknown *customers*. Never invent an identifier or drop a line solely due to this null.
- **ECB:** EXR.D.GBP.EUR.SP00.A, dated **GBP per 1 EUR** reference quotations, not one rate for each calendar day. Repo evidence records **268** observations for the historical window, including **2** missing/invalid rate values. A valid rate must be positive, finite, for the right series and eligible under an approved observation-status policy.
- **No independent finance ledger** or full adjustment lineage is available from these two sources. The data demonstrates historical invoice analysis, not automatic financial reconciliation.

## 2. KPI catalogue — at-a-glance

**Status legend:** DIAGNOSTIC = source-defined, calculated for validation with clear caveats; **TBA = not an official publishable KPI** until relevant business policy is signed off. Formula descriptions below specify desired semantics; they are not authority to choose defaults.

| ID | Metric | Status | Business owner | Unit / default reporting grain |
|---|---|---|---|---|
| **KPI-001** | Source signed invoice-line value | DIAGNOSTIC | Michael (review) | GBP / source line |
| **KPI-002** | Daily signed invoiced amount | DIAGNOSTIC | Sarah + Michael | GBP / source InvoiceDate × selected source dimensions |
| **KPI-003** | Distinct observed invoice references | DIAGNOSTIC | Sarah | count / source date × approved invoice-level dimensions |
| **KPI-004** | Daily sales (approved business definition) | **TBA** | Sarah + Michael | GBP / approved sales reporting day × dimensions |
| **KPI-005** | Number of orders | **TBA** | Sarah | count / approved reporting period × dimensions |
| **KPI-006** | Value of cancellations / adjustments | **TBA** | Michael | GBP / approved cancellation date or original sale period |
| **KPI-007** | Sales amount converted to EUR | **TBA** | Michael + Sarah | EUR / approved reporting date × dimensions |
| **KPI-008** | Finance revenue / net revenue | **TBA** | Michael | GBP or EUR / finance recognition period |
| **KPI-009** | Observed customer-invoice count | DIAGNOSTIC | Emma | count / identified customer × source period |
| **KPI-010** | Customer purchase frequency | **TBA** | Emma | purchases / identified customer × approved window |
| **KPI-011** | Customer total purchasing value | **TBA** | Emma + Michael | GBP/EUR / identified customer × approved window |
| **KPI-012** | Repeat customer rate | **TBA** | Emma | percent / approved customer cohort and period |
| **KPI-013** | High-value customer ranking | **TBA** | Emma | rank/segment / identified customer × analysis window |
| **KPI-014** | Identified-customer line coverage | DIAGNOSTIC | Emma + Daniel | percent / UCI snapshot or reporting period |
| **KPI-015** | Approved FX-rate coverage | DIAGNOSTIC once policy selected | Michael + Daniel | percent / conversion-required lines or dates |
| **KPI-016** | Average order value | **TBA** | Sarah + Michael | GBP/EUR per eligible order × period |

All KPI names above are catalog entries. **Only DIAGNOSTIC metrics may be reported without claiming an approved revenue policy**, and even these must be labelled as diagnostics and respect material invalid-row publication holds. The names “sales”, “orders”, “cancellation value” and “revenue” in TBA entries are target business capabilities, **not** implicitly implemented interpretations.

## 3. Detailed definitions (meaning, calculation, grain, source, limitations)

### KPI-001 — Source signed invoice-line value (DIAGNOSTIC)

| Attribute | Specification |
|---|---|
| **Business meaning** | Signed monetary amount of one UCI invoice-line observation, used for technical reconciliation and exploration; **not recognized or net revenue** |
| **Calculation** | **Quantity × UnitPrice** in GBP with fixed-point arithmetic |
| **Grain** | One source line key = (uci_batch_id, source_row_number) |
| **Required sources/fields** | UCI Quantity, UnitPrice; source line identity and validity flags |
| **Aggregation** | Additive across valid eligible lines when grouping within **one source vintage**; keep negative signs and potential duplicate-looking rows until policy decided |
| **Limitations** | Zero or negative UnitPrice can be business adjustments; malformed numeric rows require exception disposition; tax, discount, shipping, accounting recognition unknown |
| **Verification** | 2 units at GBP 10 → signed GBP 20; −2 units at GBP 10 → signed GBP −20, without asserting business cancellation |

### KPI-002 — Daily signed invoiced amount (DIAGNOSTIC)

| Attribute | Specification |
|---|---|
| **Business meaning** | Source-observed signed invoice-line total assigned to the **source InvoiceDate calendar date**; NOT approved daily sales/revenue |
| **Calculation** | Sum of KPI-001 over retained, numerically valid lines for each source date and filter set |
| **Grain** | Source InvoiceDate date × chosen source dimensions (e.g., Country; StockCode only for line-based analyses) × release/vintage |
| **Required sources/fields** | UCI InvoiceDate, Quantity, UnitPrice, Country, StockCode; flags |
| **Aggregation** | Sum daily signed values across non-overlapping date/dimension groups **if line populations are not double counted** |
| **Limitations** | Date time zone, payment/recognition basis, cancellations, shipping/service classification and treatment of anomalous lines not approved. A line quarantined for bad price may block a dependent financial output. |
| **Verification** | For two valid lines on one day of GBP 20 and GBP −5, diagnostic signed total = GBP 15; do not label it as GBP 15 of approved sales |

### KPI-003 — Distinct observed invoice references (DIAGNOSTIC)

| Attribute | Specification |
|---|---|
| **Business meaning** | Count of unique invoice reference values present in a scoped source slice, not confirmed placed/completed orders |
| **Calculation** | Distinct count of InvoiceNo within **one UCI snapshot and specified filter scope** |
| **Grain** | UCI source date or reporting period × allowed **invoice-level** dimensions × release |
| **Required sources/fields** | UCI InvoiceNo, InvoiceDate, Country for applicable grouping |
| **Aggregation** | **Non-additive** across product/country/day groups unless invoices are proven to partition uniquely; recompute distinct for the requested total |
| **Limitations** | C-prefix invoices may be cancellations; invoice reference ≠ individual line or necessarily approved order. Conflicting dates/countries within one invoice require flags; cross-snapshot repeated invoices are not extra orders. |
| **Verification** | Two lines with InvoiceNo 1001 and one line with 1002 → two distinct references, three lines. If cancellation C1003 is also present, raw count becomes three, not an approved order count. |

### KPI-004 — Daily sales in GBP (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Approved Sales performance for a business reporting day, consistently defined with Finance |
| **Proposed calculation framework** | Sum of **eligible_sales_line_amount_gbp** over the approved reporting date/dimensions; **eligibility and amount adjustments are TBA**. KPI-002 must not be silently substituted. |
| **Grain** | Reporting day (which date/time basis **TBA**) × approved Country/product/channel dimensions × published release/metric version |
| **Required sources/fields** | UCI InvoiceNo, InvoiceDate, Quantity, UnitPrice, StockCode, Country, cancellation/adjustment flags; potentially missing tax, discounts, shipping/payment data |
| **Aggregation** | Amount additive if exact line eligibility, currency, period and grain are consistent; avoid overlapping category partitions |
| **Limitations/TBA** | What is “sale”? Include C lines, negative non-C lines, zero/negative prices, service fees, taxes, returns? Invoice versus payment versus recognized date? Timezone/cutoff? |
| **Verification after approval** | Business-approved reference invoices with expected daily totals; same result in Sales/Finance views with identical metric/version/release/filters |

### KPI-005 — Number of orders (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Number of qualifying customer orders in period, not number of invoice lines |
| **Proposed calculation framework** | Distinct **eligible order identifier** within approved period. InvoiceNo is only a **candidate** order proxy; eligible order states and dedup/cancellation rules **TBA**. |
| **Grain** | Reporting day/week/month × approved invoice-level dimensions × published release |
| **Required sources/fields** | UCI InvoiceNo, InvoiceDate, C-prefix, Quantity and transaction validity; ideally an actual order-status/order-ID source (not supplied) |
| **Aggregation** | Non-additive across item, country and other dimensions where same order may span groups. Recompute distinct at requested scope. |
| **Limitations/TBA** | Is one invoice an order? Are cancelled invoices counted? Partial returns? Non-C negative lines? How allocate invoices appearing on more than one date/country? |
| **Verification after approval** | Fixture with two lines of one invoice, one other invoice and one C-prefixed invoice: show that line count ≠ invoice count and assert expected **business** order count only after approval |

### KPI-006 — Value of cancellations / adjustments (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Financial effect of approved cancelled/returned/adjusted sales under Michael's accounting policy |
| **Proposed calculation framework** | Sum approved adjustment amounts, with approved sign convention (positive magnitude or negative signed delta **TBA**); use **C-prefix and negative Quantity only as candidates**, not an unquestioned universal calculation |
| **Grain** | Cancellation event date or original sale reporting period **TBA** × relevant dimensions × published release |
| **Required sources/fields** | UCI InvoiceNo, Quantity, UnitPrice, InvoiceDate, candidate flags; original-invoice linkage and partial-refund history **not available as trustworthy fields** |
| **Aggregation** | Additive only once per eligible adjustment, under agreed dating/linkage; avoid double counting a C line and its negative-quantity indicator |
| **Limitations/TBA** | Full vs partial cancellation, adjustment vs refund, sign handling for negative prices, allocation to original period, late corrections, service/fee effects; historic linkage cannot be guaranteed |
| **Verification after approval** | Separate fixtures for one C-prefixed negative line and one negative non-C line; expected cancellation classifications and totals require Michael's signed policy |

### KPI-007 — Sales in EUR (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | The **same approved sales measure** as KPI-004, expressed in EUR; not a new independent revenue definition |
| **Proposed calculation framework** | For each **eligible GBP amount/date according to approved conversion policy**, calculate **amount_eur = amount_gbp ÷ ECB_rate_gbp_per_eur**; then sum line/period converted amounts under approved rounding/order of operations |
| **Grain** | Approved reporting day × dimensions × currency EUR × release and metric version; FX observation date and vintage traceable per contributing amount |
| **Required sources/fields** | KPI-004 eligible GBP basis from UCI; ECB series EXR.D.GBP.EUR.SP00.A (TIME_PERIOD, OBS_VALUE, status, vintage); approved rate selection |
| **Aggregation** | Convert at approved line/day grain **before** aggregating across different rate dates; do not divide a multi-day GBP total by an arbitrary single rate |
| **Limitations/TBA** | EUR must be approved as reporting currency; FX date, business-day fallback, maximum lookback, status eligibility, conversion precision, rounding and historical revisions are not yet signed off. Missing required rate blocks dependent publication. |
| **Verification** | **Arithmetic only:** GBP 100 with a preselected illustrative 0.80 GBP/EUR → EUR 125 **before rounding**. This does **not** approve use of that rate on a particular date. |

### KPI-008 — Finance recognized/net revenue (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Financially approved historical recognized/net revenue for reporting and reconciliation |
| **Proposed calculation framework** | Apply **approved** recognition, taxes, discounts, shipping, fees, cancellations, adjustments and FX rules to eligible monetary events; no truthful complete formula can be defined from current sources alone |
| **Grain** | Recognition period / finance dimensions / currency × metric version × release |
| **Required sources/fields** | UCI source amounts and indicators; ECB rates for EUR; additional accounting ledger/status/adjustment history for authoritative recognition/reconciliation |
| **Aggregation** | Additive amounts after approved recognition and restatement rules; policy version pinned |
| **Limitations/TBA** | No independent finance ledger, payment/fulfilment events, reliable partial-cancellation mapping or approved revenue definition; this KPI **cannot** receive finance-grade acceptance on current sources alone |
| **Verification after approval** | Independently reconciled ledger/reference cases matching the same scope/period/currency; synthetic fixtures prove formula behavior but **not** real ledger reconciliation |

### KPI-009 — Observed customer-invoice count (DIAGNOSTIC)

| Attribute | Specification |
|---|---|
| **Business meaning** | Count of distinct UCI invoice references associated with a **known** CustomerID; source-observed invoices, not necessarily confirmed purchases |
| **Calculation** | Distinct count InvoiceNo grouped by non-null CustomerID and source date/window |
| **Grain** | CustomerID × source InvoiceDate reporting window × UCI snapshot/release |
| **Required sources/fields** | UCI CustomerID, InvoiceNo, InvoiceDate |
| **Aggregation** | Non-additive across overlapping windows/product groups; recompute distinct at customer-period grain |
| **Limitations** | Null CustomerID rows excluded **from identified-customer grouping only**, not source sales; C invoices may count as observed invoice references, not valid purchases; multiple customer IDs per invoice require investigation |
| **Verification** | Two lines with same InvoiceNo and CustomerID → 1 observed invoice, not 2 purchases |

### KPI-010 — Customer purchase frequency (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Number or rate of qualifying purchases made by an identified customer over an approved time window |
| **Proposed calculation framework** | Distinct eligible **purchase/order events** per CustomerID, optionally divided by window duration under an approved frequency unit |
| **Grain** | Non-null CustomerID × approved 30/90-day, monthly or lifetime window **TBA** × release |
| **Required sources/fields** | UCI CustomerID, InvoiceNo, InvoiceDate, cancellation flags; approved purchase/order eligibility |
| **Aggregation** | Must count eligible unique purchases; not raw line count; non-additive over overlapping intervals |
| **Limitations/TBA** | What constitutes a purchase? Cancellation handling, late adjustments, customer identity stability, inactive definition, time zone/window and order proxy |
| **Verification after approval** | Two lines same eligible order plus a second distinct eligible order → purchase count 2, not 3; use only after eligibility rule approved |

### KPI-011 — Customer purchasing value (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Monetary value of eligible purchases attributable to one identified customer within a period |
| **Proposed calculation framework** | Sum approved customer-eligible monetary line values with cancellation, return, shipping and FX handling per signed policy |
| **Grain** | Identified CustomerID × approved period × currency × release/metric version |
| **Required sources/fields** | UCI CustomerID, Quantity, UnitPrice, InvoiceDate, InvoiceNo; adjustment flags, ECB for EUR |
| **Aggregation** | Additive across disjoint periods for same customer only when identical accounting/time/currency policy applies |
| **Limitations/TBA** | Net vs gross value, cancellation allocation, unidentified customers, partial returns, original invoice linkage, conversion and customer lifetime |
| **Verification after approval** | Reference customer with ordinary purchase and cancellation; compare against Michael's and Emma's expected signed total |

### KPI-012 — Repeat customer rate (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Percentage of eligible identified customers that purchase repeatedly in the defined observation window |
| **Proposed calculation framework** | Count eligible customers with qualifying purchase_count ≥ 2 divided by count of eligible customers in the **same approved cohort/window** × 100% |
| **Grain** | Defined cohort × time window × release; optionally Country when source classification is sound |
| **Required sources/fields** | KPI-010 eligible customer purchase count and customer eligibility set |
| **Aggregation** | **Ratio non-additive**; recompute numerator and denominator for each new grouping, do not average country percentages |
| **Limitations/TBA** | Cohort inclusion (one-time vs inactive), cancellations, guest/unknown IDs, window length, equality boundary, definition of purchase |
| **Verification after approval** | Approved fixture with known repeat and one-time customers; independently recompute numerator and denominator |

### KPI-013 — High-value customer ranking / segment (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Identify customers who meet an agreed business definition of “valuable” |
| **Proposed calculation framework** | Rank/classify identified customers using **approved** customer monetary/frequency/recency metrics and thresholds; **no top-N, percentile or RFM threshold is assumed** |
| **Grain** | Identified CustomerID × analysis window × metric/segment version × release |
| **Required sources/fields** | CustomerID, eligible purchase value, frequency, recency source dates; optionally further data not provided |
| **Aggregation** | Customer classification evaluated at stated window; not meaningfully additive |
| **Limitations/TBA** | Value definition, threshold and tie-breaker; guest customers unranked; lifetime value/profit cannot be inferred from source prices without costs/margins |
| **Verification after approval** | Approved sample customers immediately below/on/above classification boundary; compare exact expected membership |

### KPI-014 — Identified-customer line coverage (DIAGNOSTIC)

| Attribute | Specification |
|---|---|
| **Business meaning** | Proportion of source lines that can be associated with a known CustomerID |
| **Calculation** | Count source lines with non-null, parseable CustomerID ÷ count all source lines in same scope × 100% |
| **Grain** | UCI snapshot, optionally month × Country × invoice class; **line-based denominator** |
| **Required sources/fields** | UCI CustomerID and source row identity; validated source vintage |
| **Aggregation** | Recompute ratio using summed numerators and denominators, not average percentages |
| **Limitations** | **Not customer-level identity coverage** and not automatically a percentage of orders; missing CustomerID is not proof of guest purchase |
| **Verification** | 3 of 4 example lines identified → 75% **line** coverage. Repo baseline: 135,080 missing of 541,909 rows, so roughly 75.07% identified-line coverage. |

### KPI-015 — Approved FX-rate coverage (DIAGNOSTIC once policy selected)

| Attribute | Specification |
|---|---|
| **Business meaning** | Extent to which a reporting population requiring conversion has a usable, policy-eligible ECB rate |
| **Calculation** | Count conversion-required eligible **lines** with approved resolved rate ÷ count all conversion-required eligible lines × 100%; separately count required **distinct dates** with/without a valid rate |
| **Grain** | Source vintage × requested reporting period × release × approved FX policy version |
| **Required sources/fields** | UCI eligible monetary lines/dates; ECB series/date/value/status/vintage; FX date selection |
| **Aggregation** | Recompute from raw numerator/denominator; two ECB null observations are not the same as two conversion-required missing days |
| **Limitations** | Cannot prove complete GBP→EUR conversion before Michael approves date fallback/status/lookback. Weekend dates are not automatically invalid. For an EUR-dependent release, **all required lines must be resolvable** or an explicit exception decision must be recorded. |
| **Verification after policy** | Fixture with one eligible line and a missing required rate: matched_count = 0 unless approved fallback applies; no zero or invented rate |

### KPI-016 — Average order value (OFFICIAL KPI — TBA)

| Attribute | Specification |
|---|---|
| **Business meaning** | Average approved sales value attributable to one qualifying order |
| **Proposed calculation framework** | Approved eligible order sales amount ÷ number of approved eligible orders (KPI-005), with zero-denominator handled as undefined/NULL, not 0 |
| **Grain** | Reporting period × approved invoice-level dimensions × currency × metric version/release |
| **Required sources/fields** | Approved KPI-004/KPI-007 sales basis and KPI-005 orders based on same population and period |
| **Aggregation** | **Ratio non-additive**; recompute from sum of numerator and correctly deduplicated denominator |
| **Limitations/TBA** | Sales versus recognized revenue basis, partial cancellations, order definition, FX conversion, dimensions and zero-order behavior |
| **Verification after approval** | Sum of eligible order values and eligible order count independently calculated from business fixture; ratio matches approved precision |

### MVP publication eligibility

A metric's presence in this catalogue **does not automatically make it a required publication gate**. The MVP release manifest must explicitly list the metric IDs/versions and report families that are required for the approved MVP scope. Missing sign-off keeps a TBA metric out of **official published reporting**; this does not by itself justify blocking unrelated diagnostics or an otherwise complete separately approved release. At the same time, no unsupported revenue or financial KPI may be silently substituted with a source-signed diagnostic. Because the initial architecture assumes one global release, any later split into independently publishable families needs a separate approved architecture change.

## 4. Operational metrics needed to make KPIs trustworthy

These are **platform health metrics**, not Sales/Finance revenue measures.

| Operational ID | Meaning / computation | Grain / source | Acceptance role |
|---|---|---|---|
| **OPS-01 Published release** | Active release_id of all published report families | one global current_release row | All consumers must use one pinned ID |
| **OPS-02 Last successful publication** | UTC commit timestamp of atomic release activation | published release / publication registry | Failed candidate cannot update timestamp |
| **OPS-03 Data-through coverage** | Source coverage through date, plus scoped minimum required coverage for each metric | source and release manifest | Shown on every report |
| **OPS-04 Failed/stale state** | Candidate failure + comparison of publication age to approved freshness target (**TBA**) | run registry and published pointer | Do not label failed refresh successful |
| **OPS-05 Exception exposure** | Count and signed GBP value of unapproved quarantined monetary rows | per UCI batch/rule/metric | Publication cannot silently omit value |
| **OPS-06 Cross-report metric parity** | Difference of same metric ID/version/release/filter/currency/date basis in Sales and Finance | per candidate release and metric | Must equal 0 within approved arithmetic/rounding tolerance (**TBA**) |
| **OPS-07 ECB required-date exceptions** | Count/list of FX-required lines and dates with no approved matched usable rate | FX resolution candidate | Unresolved required coverage blocks EUR results |

## 5. Dimensional and aggregation contract

| Dimension or operation | Allowed / risk |
|---|---|
| **Reporting date** | InvoiceDate calendar date for **source diagnostics** only; order/payment/recognized/cancellation event date for official KPIs remains **TBA** |
| **Country** | Source customer's residence; do not infer transaction currency, billing country or shipping country |
| **StockCode** | Source product/service code; same code may have different descriptions; fees/services require classification |
| **CustomerID** | Nullable, customer-level reporting only for identified customers, with visible coverage |
| **Original source currency** | GBP for **all UCI UnitPrice values**, regardless of Country |
| **EUR FX dimension** | ECB GBP per EUR rate, **rate date and rate vintage** both recorded |
| **InvoiceNo** | Invoice reference; may repeat across source rows and may be cancellation candidate; not a stable individual line ID |
| **Summation** | Signed GBP line amounts additive for source diagnostics when one line counted exactly once. Monetary official sums depend on accepted eligibility. |
| **Count distinct** | Non-additive across overlapping dimensional groups; must recompute from the relevant invoice/order population |
| **Ratios / ranks** | Non-additive; calculate from complete numerator/denominator or full eligible customer set at the target grain |
| **Historical release** | Measures compare only if currency, policy, definition version and source vintage/release basis are made explicit |

**Potential issue:** A single invoice may contain several products. If you group by StockCode and count InvoiceNo in each group, summing those product-level invoice counts does **not** reconstruct the overall order count. Never rely on sum-of-distinct-counts for the total.

## 6. Sample verification fixture (arithmetic, NOT revenue policy)

This example is **synthetic**, solely for proving technical calculations and grain. It does **not** approve what Finance considers sales, orders or cancellations.

| Source line | InvoiceNo | Source date | CustomerID | Quantity | UnitPrice GBP | Raw signed amount GBP |
|---|---|---|---|---:|---:|---:|
| L1 | 1001 | 2011-01-04 | A | 2 | 10.00 | 20.00 |
| L2 | 1001 | 2011-01-04 | A | 1 | 5.00 | 5.00 |
| L3 | 1002 | 2011-01-04 | NULL | 3 | 7.00 | 21.00 |
| L4 | C1003 | 2011-01-04 | A | -1 | 10.00 | -10.00 |

**Checkable results for diagnostics:**
- KPI-001 by line: **20, 5, 21, −10 GBP**.
- KPI-002 daily signed source amount: **36 GBP** (20 + 5 + 21 − 10).
- KPI-003 raw distinct invoice references: **3** (1001, 1002, C1003) versus **4** physical source lines. This is **not yet** number of approved orders.
- KPI-009 for identified A: **2** observed invoice references (1001 and C1003) and **3** associated lines; **not** the same as 2 approved purchases.
- KPI-014 identified line coverage: **3 / 4 = 75%**; one unidentified line remains in source-level signed total.
- L4 is a cancellation **candidate**, but KPI-006 official cancellation value remains **TBA**. The synthetic signed source amount of that line is **−10 GBP**, not automatically a recognized adjustment.
- With a **preselected illustrative** ECB rate of **0.80 GBP per EUR**, arithmetic for a hypothetical **GBP 100 eligible amount** gives **EUR 125 before rounding**. This verifies conversion **direction only**. It does **not** authorize selecting a rate or treating the GBP 36 diagnostic as approved EUR sales.

### 6.1 Acceptance test catalogue

| Test ID | Setup / check | Objective expected result | Metrics / business rule |
|---|---|---|---|
| **KPI-AT-01** | Evaluate L1–L4 raw signed values | 20, 5, 21, −10 GBP, sum **36 GBP** | KPI-001/002 |
| **KPI-AT-02** | Count distinct raw InvoiceNo | **3** observed invoices, not **4** lines | KPI-003; source grain |
| **KPI-AT-03** | Exclude null CustomerID only from identified metrics | KPI-014 = **75%**; source signed total still 36 GBP | KPI-009/014; UCI-CMP-02 |
| **KPI-AT-04** | Read L4 as negative + C-prefixed | Flag candidate, keep signed value; no invented original-order link | KPI-006; UCI-BIZ-01/02 |
| **KPI-AT-05** | GBP 100 / selected rate 0.80 | EUR **125 before rounding**, with original GBP/rate retained | KPI-007; ECB-VAL-04 arithmetic |
| **KPI-AT-06** | Required EUR rate missing/null | No zero fill; EUR metric BLOCKED without approved fallback; prior published release unchanged | KPI-007/015; ECB-CMP-04 |
| **KPI-AT-07** | Two lines of one invoice in different StockCode groups | Product-level distinct invoice counts may sum above global total; global recomputed distinct correct | KPI-003/005 grain |
| **KPI-AT-08** | Compare identical approved metric, filters, date basis, currency, version, release across Sales and Finance | Equal values within approved rounding tolerance; mismatch blocks release | FR-03; OPS-06 |
| **KPI-AT-09** | Deliberately fail a candidate after one mart is prepared | None of its candidate KPIs visible; prior report values/timestamp unchanged | FR-11; OPS-01/02 |
| **KPI-AT-10** | Replay same source hash and metric versions | No duplicated published lines or altered totals | NFR-02/06; OPS-01 |
| **KPI-AT-11** | Request official revenue, cancellation value, high-value segment before sign-off | Metric status **TBA**, no fabricated official values | KPI-006/008/013 |
| **KPI-AT-12** | Independent Finance ledger absent | FR-09 reconciliation shown as unavailable/conditional; synthetic reference cases not misrepresented as real ledger reconciliation | KPI-008; FR-09 |
| **KPI-AT-13** | Valid source but metric requires unknown business date basis | Diagnostics can remain labelled; approved KPI publication blocked until policy resolved | KPI-004/005/008 |
| **KPI-AT-14** | Refresh several dashboard widgets across an activation | Every widget uses the same pinned release_id | All shared KPIs |

**Evidence for acceptance:** approved example input rows, metric definition and policy version, expected/actual result with precision and filters, report_release ID, source UCI/ECB hashes, line eligibility counts, unresolved exception list and stakeholder sign-off. These are **future** tests; no ETL validation was executed in this task.

## 7. Traceability: business request → KPI → source and gap

| Business requirement | Business output / KPI | Source availability | Gap / owner |
|---|---|---|---|
| **FR-01/02** — Monday sales performance | KPI-004 daily sales, KPI-005 order count, KPI-016 average order value | UCI InvoiceDate, InvoiceNo, Quantity, UnitPrice, dimensions | Exact sales definition, period/cutoff, invoice as order: Sarah + Michael |
| **FR-03/13** — shared definitions | metric registry and identical semantic views | All metrics versioned | Metric approval authority and recognized revenue: Michael + sponsor |
| **FR-04/05** — historical revenue and cancellations | KPI-006 cancellation amount, KPI-008 finance revenue | UCI signed lines and C-prefix | Original-invoice linkage/partial returns, historical recognition: Michael |
| **FR-06** — currency | KPI-007 EUR sales, KPI-015 FX coverage | UCI original GBP + ECB GBP/EUR observations | FX observation date, missing day, rounding and revisions: Michael |
| **FR-07/08** — purchase behavior and high-value customers | KPI-009/010/011/012/013/014 | UCI CustomerID (incomplete), InvoiceNo, InvoiceDate, signed amounts | Purchase/cohort/segment definitions and unknown-customer policy: Emma |
| **FR-09** — independent reconciliation | KPI-008 + OPS-06 | Two current feeds **do not** contain ledger | Need authoritative reference: Michael |
| **FR-10/11/12** — update status and atomic reports | OPS-01–OPS-04 plus release gates | Generated by future platform, **not source columns** | Cutoff, freshness/recovery and alert recipients: Daniel + Sarah |

## 8. Open questions and approval matrix

| Decision ID | Business question | Owner | Until approved |
|---|---|---|---|
| **MET-OQ-01** | Are Sales and Finance reporting gross sales, net sales, recognized revenue or all as **different** KPIs? | Sarah + Michael | KPI-004 and KPI-008 **TBA** |
| **MET-OQ-02** | What counts as an order, purchase, partial cancellation, refund and adjustment? | Sarah + Michael | KPI-005/006/010 **TBA** |
| **MET-OQ-03** | Are postage, bank charges, discounts, taxes, zero/negative prices and duplicated-looking lines included? | Michael | Money eligibility **TBA** |
| **MET-OQ-04** | Which time basis: source invoice, cancellation event, payment, recognized period? Which time zone/cutoff? | Michael + Sarah | Business daily/year totals **TBA** |
| **MET-OQ-05** | What FX date, non-business-day fallback, maximum lookback, status, rounding and revision policy? | Michael | KPI-007 and usable FX coverage **TBA** |
| **MET-OQ-06** | What is a qualifying purchase, repeat, inactive cohort and high-value threshold/ranking tie-break? | Emma | KPI-010–013 **TBA** |
| **MET-OQ-07** | Which independent ledger/reference, acceptable variance and correction/restatement policy? | Michael | Finance reconciliation **TBA** |
| **MET-OQ-08** | Who approves metric versions and what release/report cutoff is needed each Monday? | Sponsor + Daniel + Sarah | Business publication SLA **TBA** |
| **MET-OQ-09** | Must reports support as-originally-reported history, and what source information exists for late adjustments? | Michael + Daniel | Historical finance accuracy scope **TBA** |

### Sign-off and status

**DIAGNOSTIC** formulas are transparent source definitions for testing and data exploration; they must not be branded as official sales or recognized revenue. **OFFICIAL KPI — TBA** entries describe intended measurements and exact decisions needed to make them calculable. No thresholds or accounting definitions in this document constitute business approval.

**Required sign-off before implementation acceptance:** Sarah (Sales), Michael (Finance and FX), Emma (Customer), Daniel (failure/monitoring), and a named cross-functional metric owner/sponsor. **All pending.**

## 9. References and evidence provenance

- [DE-004 Architecture](../architecture/architecture.md)
- [DE-001 Business Requirements](../../business/requirements.md)
- [DE-002 Source Profiling](../../docs/data/source-profiling.md)
- [DE-003 Data Contracts (technically reviewed)](../../docs/data/data-contracts.md)
- [Committed profiling evidence](../../profiling_evidence.json)

**Evidence status:** Source counts are copied from repository evidence and not independently recalculated here. The sample records are synthetic. No pipelines, infrastructure, ETL code or executable tests have been produced in DE-004.

## 10. Technical Lead review / changelog — v0.2

1. Normalized the filename and corrected the architecture link after publishing the reviewed catalogue in `docs/business/kpi-definitions.md`; the original draft remains under `robocze/DE-004/`.
2. Distinguished diagnostic measurements derived directly from UCI source rows from official business metrics requiring Sales, Finance or Customer approval.
3. Clarified that **TBA metrics should not be advertised as approved** and that MVP-required release gates need an explicit, versioned set of approved metrics; this avoids accidentally blocking all progress merely because optional financial metrics lack a source ledger.
4. Retained correct GBP-per-EUR conversion direction (GBP ÷ rate), non-additive distinct counts and ratios, release ID pinning, and source-vintage coverage.
5. Preserved illustrative fixtures as specifications, not test execution results. No business sign-off or end-to-end calculation has been performed.

**Disposition:** Technically reviewed for design; all business-defined KPI policies, approval records and executable test evidence remain open.
