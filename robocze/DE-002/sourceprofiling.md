# Retail Analytics Data Platform — Source Profiling & Feasibility Report

**Document ID:** DE-002  
**Version:** 0.2 — technical review, empirical evidence pending  
**Prepared:** 2026-11-02  
**Input specification:** [`business/requirements.md`, BRS-DE-001 v0.2](https://github.com/AgnieszkaPawlak/retail-analytics-data-platform/blob/main/business/requirements.md)  
**Sources under assessment:** UCI Online Retail (dataset 352) and ECB Exchange Rates (EXR)  
**Decision:** **CONDITIONAL GO for designing the historical training/MVP project; NOT ACCEPTED as a completed empirical profiling baseline.** Full-file UCI measurements and actual ECB response evidence are still pending. This technical review does not imply stakeholder approval.

> **Evidence integrity / significant limitation**  
> This report distinguishes **[P]** publisher documentation, **[S]** independently published analyses of the original UCI file, **[I]** inference from source structure, and **[T]** tests executed in this assessment. The UCI ZIP (~22.6 MB) could not be downloaded to the execution environment; the ECB data endpoint could not be queried successfully from it. Consequently, **no numerical results below are presented as a new full-file [T] measurement**, and no ECB HTTP response/status is presented as an observed service response. Secondary statistics are provided to inform feasibility and must be **recomputed from an identified input-file SHA-256** before this report is accepted as a completed empirical baseline. A companion `profile_sources.py` implements those checks; its previous author reported a synthetic-fixture smoke test, **not** a test against UCI production data; independent reviewer execution has not been evidenced. No raw financial record is altered by this report.

## Executive summary

The sources support a useful **historical, line-item-level retail analytics prototype**. Retail provides invoice reference, item, quantity, unit price **in GBP**, timestamp, customer ID when present, and country; ECB documentation describes a historically queryable daily **GBP-per-EUR** rate series. They do **not**, by themselves, establish complete order/return lineage, finance-grade revenue recognition, an independently authoritative ledger, or operational update status. In particular, `Country` is **not** transaction currency. Currency conversion would be GBP → reporting currency, not evidence of original multicurrency sales. [P][I]

The published raw-file analyses report **541,909 records**, **135,080 missing `CustomerID` values (~24.93%)**, **1,454 missing descriptions (~0.27%)**, approximately **5,268 exact duplicate occurrences (~0.97%)**, and both negative quantities and prices. These are *previously published third-party observations*, not fresh measurements from this environment. [S] They warrant deliberate business rules; automatically deleting all negative rows, null-customer sales, or duplicate-looking lines can materially distort revenue. [I]

| Business capability | Preliminary feasibility | Reason / qualification |
|---|---|---|
| Recurring historical sales reporting (`FR-01`, `FR-02`, `FR-13`) | **Conditional / largely supported** | Time, country, product, quantities and GBP prices exist, but **sales vs revenue definition** is still unapproved. |
| Agreed revenue definition and historical figures (`FR-03`, `FR-04`) | **Conditional** | Source has observable invoiced line amounts but lacks tax, fulfillment/payment events and accounting policy. |
| Full/partial cancellation history (`FR-05`, `NFR-06`) | **Insufficient to guarantee** | `C` invoices and negative quantities exist; reliable original-invoice linkage, partial refund and late-correction history are not proven. |
| FX conversion (`FR-06`) | **Conditionally supported** | GBP-denominated source can be combined with documented ECB historical GBP/EUR observations **if** approved date/fallback/rounding rules exist. Actual API coverage is untested here. |
| Customer purchasing trends (`FR-07`, `FR-08`) | **Partially supported** | A customer ID exists for a substantial subset, but ~25% of lines lack an identity; value definitions remain open. |
| Independent financial reconciliation (`FR-09`, `NFR-01`) | **Not supported by these two sources alone** | No independent accounting reference or ledger is supplied. |
| Update freshness, failure consistency (`FR-10`–`FR-12`, `NFR-03`–`NFR-05`) | **Requires system capability, not present in source** | An archived XLSX and an external reference-rate API do not contain the future platform's successful-update timestamp/status. |

## 2.1 Source inventory

| Attribute | SRC-01 — UCI Online Retail | SRC-02 — ECB Exchange Rates |
|---|---|---|
| Publisher | UCI Machine Learning Repository; dataset donated by Daqing Chen | European Central Bank (ECB) / ECB Data Portal |
| Origin / meaning | Historical retail invoice-line observations from a UK-based non-store retailer | Officially published reference exchange-rate observations, series `EXR` |
| Canonical reference | [UCI dataset 352](https://archive.ics.uci.edu/dataset/352/online+retail); DOI `10.24432/C5BW33` | [ECB Data API examples](https://data.ecb.europa.eu/help/api/data-examples); [EXR dimensions](https://data.ecb.europa.eu/data/datasets/EXR/structure) |
| Interface / format | Downloadable ZIP containing `Online Retail.xlsx` (Excel workbook) | HTTPS Data API; SDMX; `format=csvdata` CSV or supported SDMX formats |
| Version / reproducibility | UCI records donation in Nov 2015; **no dataset-file hash or immutable snapshot version established** in this run | Time-varying published series; request key, date window, retrieval time, response hash and revision policy must be recorded |
| Expected temporal coverage | 2010-12-01 to 2011-12-09 | Historically queryable daily exchange-rate series; overlap for the retail dates **not empirically checked** |
| Acquisition frequency | Archived static dataset; no ongoing transaction feed promised | Reference observations published on eligible working days; not one per calendar day |
| Availability check in this run | Publisher metadata opened; full ZIP **download failed** in execution environment | Documentation opened via search; direct API data request **not accessible from this environment**; source-side availability **unverified** |
| Authentication | Public download page | Public data documented; no API credential required in published examples |
| Use conditions | **CC BY 4.0**: sharing/adaptation with attribution and license terms | Public ESCB statistics can be reused with source attribution subject to [ESCB reuse conditions](https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html); preserve distinction between published rates and derived calculations |
| Primary limitations | Historical only; missing customer IDs; cancellation matching; source currency GBP; no operational freshness | Not a transaction ledger; non-business-day gaps; reference-rate policy may not equal company's accounting FX policy; potential revisions |

**Attribution text for distributed work:** “Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33. Licensed CC BY 4.0.” For reused ECB statistical observations: “Source: ECB statistics.” [P]

**Scope guard:** Do **not** accidentally substitute *Online Retail II* (UCI dataset 502): it is a **different** two-year dataset. Here the reference is dataset **352** only.

## 2.2 Schema analysis

### SRC-01 — UCI Online Retail

**Grain:** One exported **invoice line / item observation**, **not** one invoice and not necessarily a uniquely identified order line. Eight stored columns are described; the UCI landing page's summary “6 features” is not the physical column count (identifier-role variables are listed separately). [P]

| Field | Recommended analytical type | Source meaning | Main caveat / validation |
|---|---|---|---|
| `InvoiceNo` | **String**, categorical business identifier | Invoice/transaction reference; code beginning with `C` signals cancellation | Repeats across items; preserve prefix, do not parse to integer; a cancellation invoice is **not** a foreign key to the original sale. |
| `StockCode` | **String**, categorical code | Product/item code | Documented “5-digit” pattern is an oversimplification: alphanumeric and operational codes exist. Preserve original text. |
| `Description` | Nullable string | Product/item description | May be absent or change for the same `StockCode`; unsuitable as immutable product key. |
| `Quantity` | Signed integer | Item count on invoice line | Negative values may mean returns/corrections rather than invalid purchases; very large magnitudes need review. |
| `InvoiceDate` | Timestamp **without established time zone** | Time invoice was generated | It is **not** documented as payment, delivery, recognition or cancellation-effective time. Time-zone and business-day cutoff missing. |
| `UnitPrice` | Decimal currency amount (GBP) | Unit price in sterling | Zero/negative and extreme amounts require interpretation; tax/discount inclusion is unspecified. Avoid floating-point for final accounting arithmetic. |
| `CustomerID` | Nullable string / identifier | Customer number | Export often imports it as float due to missing values. Normalize without decimal suffix; null does not prove “guest checkout.” |
| `Country` | Categorical string | Country of customer's residence | Not transaction currency, VAT country, delivery location or definitive market/region without approval. |

**Important absent fields:** line-item ID, original invoice reference on returns, cancellation/refund reason, original transaction currency per row, explicit status lifecycle, payment timestamp, tax, discount, shipping, cost, source event version, ingestion timestamp, updated-at timestamp, and independent financial ledger link. The *absence* here is a schema-level observation, not a claim that no other business system could provide them. [P][I]

**Derived measure for exploratory validation only:** `line_value_gbp = Quantity × UnitPrice`. It is a signed source-based amount, **not automatically recognized, net, or gross revenue**. Business authorization required before naming/reporting it as revenue (`OQ-01`–`OQ-03`).

### SRC-02 — ECB EXR

**Relevant series key:** `EXR/D.GBP.EUR.SP00.A` (daily, GBP quotation, EUR denominator, reference spot series). Based on ECB's EXR data structure, its dimensions include `FREQ`, `CURRENCY`, `CURRENCY_DENOM`, `EXR_TYPE`, `EXR_SUFFIX`, with a `TIME_PERIOD` observation date and `OBS_VALUE` rate. Depending on requested detail/format, observation status, metadata and other attributes may also be returned. [P]

| Element | Expected meaning / type | Validation requirement |
|---|---|---|
| `KEY` / series dimensions | Identifier/string defining specific EXR series | Confirm every returned row matches `D.GBP.EUR.SP00.A`. |
| `TIME_PERIOD` | Calendar date of observation | Must parse to valid ISO date; ensure unique within a given series/vintage. |
| `OBS_VALUE` | Positive numeric rate; **GBP per 1 EUR** | No null, negative or zero rate may be used for conversion. Verify units and decimal precision from actual response. |
| `OBS_STATUS` and attributes | Optional status or series metadata | Determine how absent/revised/provisional observations are signaled. |
| Response time / retrieval version | Not an intrinsic FX date field | Capture separately for freshness and historical reproducibility. |

**Conversion direction (illustrative only):** `EUR_amount = GBP_amount / (GBP_per_EUR_rate)`; e.g., £100 at an *illustrative* 0.85 GBP/EUR = €117.65 before approved rounding. **Do not multiply by this quoted rate to convert GBP → EUR.** Currency/date selection and fallback remain `OQ-04`.

## 2.3 Completeness analysis

**Population basis:** published original dataset, 541,909 rows × 8 columns = 4,335,272 field slots. Column null counts below are **[S] external raw-file analyses**; the raw file was not independently loaded here.

| Column | Null rows [S] | Missing % of rows | Impact |
|---|---:|---:|---|
| `InvoiceNo` | 0 | 0.00% | Core invoice reference appears populated. |
| `StockCode` | 0 | 0.00% | Item code appears populated. |
| `Description` | 1,454 | 0.27% | Product labeling incomplete; analyze nulls by item and period. |
| `Quantity` | 0 | 0.00% | Non-null does not imply valid quantity. |
| `InvoiceDate` | 0 | 0.00% | Parseability and time-zone semantics still need checks. |
| `UnitPrice` | 0 | 0.00% | Non-null does not imply positive/valid price. |
| `CustomerID` | 135,080 | **24.93%** | Major limitation for customer-level cohorts, ranking and repeat rates. |
| `Country` | 0 | 0.00% | Validity/classification still need checks. |

Published counts imply **136,534 null field cells**, i.e. approximately **96.85% populated cells** (field-cell completeness, not order/customer completeness). A separate write-up reports that all 1,454 missing descriptions fall among rows with missing customer ID; this **must be independently verified**, not assumed to hold for a future export. [S]

**Distribution analysis status:** **PENDING RAW FILE.** Exact null breakdown by month, country, cancellation indicator, invoice, and whether missingness is concentrated in operational/non-product rows has not been measured in this run. Do not classify null `CustomerID` as a guest purchase or remove those rows from finance reporting without supporting evidence.

**Proposed minimum retest:** for each column compute null count, percentage, nulls per calendar month, nulls by cancellation class, and impact on the number/value of customer-attributable vs all source lines; require independent re-computation from the original file before closeout.

## 2.4 Uniqueness and candidate identifiers

| Assessment | Reported finding / assessment | Interpretation |
|---|---|---|
| Distinct `InvoiceNo` | **25,900** [S] | Invoice identifier, **not** unique at invoice-line grain. |
| Distinct `StockCode` | **4,070** [S] | Product-like code, not a record identifier. |
| Distinct non-null `CustomerID` | **4,372** [S] | Useful customer grouping key for identified records. |
| Distinct `Country` | **38** [S] | Reporting dimension, not an ID. |
| Full-row duplicates (`duplicated(keep='first')`) | **5,268 (~0.97%)** [S] | Duplicate-looking rows exist; no proof each represents an erroneous duplicate source event. |
| `InvoiceNo + StockCode` | **Not verified** [I] | Candidate to investigate but **not** a safe primary key without counting repeated pairs. |
| Source-native line ID | **Absent** [P] | Cannot conclusively distinguish an accidental duplicate from two intentional identical lines without additional evidence. |

At least one third-party assessment reports **650** stock codes with more than one observed description under its normalization/grouping rules. Treat the exact number as method-dependent until reproduced; `StockCode` can be stable enough for grouping but **not** a one-to-one description mapping by assumption. [S]

**Recommendation:** preserve invoice lines as observed during source validation; quantify the effects of alternative deduplication rules on amount totals and transaction counts. Seek supplier documentation or transaction-level examples before declaring exact duplicates invalid. Define a defensible event/line identity policy before implementing idempotency.

## 2.5 Validity / anomalous-value analysis

| Test | Published result [S] | Data-quality assessment / necessary decision |
|---|---:|---|
| `Quantity < 0` | **10,624** rows (1.96%) | Expected in returns/adjustments as well as suspicious records; **not** globally invalid. Confirm semantics. |
| `InvoiceNo` prefix `C` | **9,288** rows (1.71%) | Cancellation indicator, **row count**, not number of canceled invoices; compare overlap with negative quantity. |
| `Quantity == 0` | **0** rows | Recheck original file. |
| `UnitPrice == 0` | **2,515** rows (0.46%) | Possibly free lines or adjustments; keep separate from paid merchandise until approved. |
| `UnitPrice < 0` | **2** rows | Likely adjustment-type entries; inspect original descriptions; do not interpret as normal retail price. |
| `Quantity` extrema | **−80,995 / +80,995** | Investigate offsetting entries, large wholesale movements or corrections. |
| `UnitPrice` extrema | **−£11,062.06 / +£38,970** | Investigate fees/adjustments, outlier price and sign treatment. |
| Distinct code patterns | Alphanumeric and service/adjustment codes reported | Do not enforce numeric-only SKU schema or assume every row is a sale of goods. |
| Invalid parsed dates | **NOT TESTED in this run** | No missing values published; parsing validity must be measured on original XLSX. |
| Impossible cross-field combinations | **NOT TESTED in this run** | Check `C` vs quantity sign, invoice-date consistency, customer/country conflicts, zero-price/negative-quantity overlap. |

**Illustrative non-merchandise codes to verify against raw data:** `POST`, `DOT`, `M`, `D`, `BANK CHARGES`, `AMAZONFEE`. Their inclusion in customer/revenue/product metrics requires explicit policy. It would be incorrect to label all statistically large quantities as errors: this business includes wholesalers. [S][I]

**Revenue impact of anomalies: NOT QUANTIFIED.** No approved sales, cancellation, refund or recognition policy exists in DE-001, so neither a final “clean revenue total” nor a universal list of rows to drop is defensible at this stage.

## 2.6 Temporal analysis

| Measure | Current evidence | Status |
|---|---|---|
| First invoice timestamp | `2010-12-01 08:26` | [S] independently reported |
| Last invoice timestamp | `2011-12-09 12:50` | [S] independently reported |
| Coverage window | 2010-12-01 through 2011-12-09, **374 calendar dates inclusive** | [P]/date arithmetic |
| Coverage year boundaries | Only Dec 2010 and Jan–early Dec 2011 present; neither 2010 nor 2011 is a full calendar year | [P] |
| Monthly record counts | **NOT MEASURED** | Requires source file |
| Days with zero rows | **NOT MEASURED** | Requires source file; weekends or store-closed days are not automatically missing data |
| Invalid timestamp/time-zone offsets | **NOT MEASURED / zone unspecified** | Must define reporting cutoffs with business owners |
| Real-time/current updates | No ongoing feed documented; dataset ends in 2011 | [P]; historical replay only |

**Meaning of temporal gaps:** an invoice-free day may be an authentic non-trading day or a missing batch. Distinguish these via the expected sales calendar and source-system controls, not merely a date-sequence check. Monthly distributions must be computed on **raw rows**, separately for `C` invoices/negative quantities and lines with known customers. December 2011 should never be compared with a *full* December without a partial-period warning.

**Historical corrections:** no source `created_at`/`updated_at` or source observation version is provided. `InvoiceDate` alone cannot reproduce when a correction became known, which is critical for `NFR-06` (“as originally reported” vs “as currently known”).

## 2.7 ECB API assessment

### Request definition — documented, not executed successfully

**Intended endpoint** (a narrow, reproducible historical request):

```text
GET https://data-api.ecb.europa.eu/service/data/EXR/D.GBP.EUR.SP00.A?startPeriod=2010-12-01&endPeriod=2011-12-09&format=csvdata
Accept: text/csv
```

**Expected on a valid data response:** a tabular SDMX-CSV payload with a series identifier/dimensions, `TIME_PERIOD`, `OBS_VALUE`, and possibly attributes/status. ECB's documentation also supports `format=jsondata`, date filtering, `detail`, `includeHistory`, and `updatedAfter`. A successful metadata lookup does **not** prove historical data coverage for every transaction date. [P]

| Test case | Expected verification | Observed result here |
|---|---|---|
| Valid `D.GBP.EUR.SP00.A`, specified date window | Record HTTP code, content type, row count, first/last observation date, sample row and data hash | **Not executed end-to-end** — data endpoint inaccessible in environment |
| Response schema | Confirm dimensions, `TIME_PERIOD` and `OBS_VALUE` numeric positive | **Not observed** |
| Duplicate/missing rates | Check duplicate dates, null/zero/non-numeric values, status flags | **Not observed** |
| Retail date coverage | Compare distinct invoice **dates** against available FX dates; analyze weekday/holiday gaps | **Not observed** |
| Weekend/holiday date request | Verify whether no quote is returned (do not assume zero FX rate) | **Not observed**; holiday behavior described in documentation |
| Invalid series/date parameters | Capture actual HTTP status and body; distinguish invalid request vs missing series | **Not observed** |
| Network interruption/timeout | Assess explicit timeout and recoverability | **Not observed** |
| History/revisions (`includeHistory=true`) | Check revisions/vintages relevant to historical reproducibility | **Not observed** |
| Rate-limiting / service availability | Capture 429/5xx if encountered; no claim of a live outage based on local access failure | **Not observed** |

**API error model to handle later:** invalid request (potential 4xx), no matching observations (often 404 in SDMX services), format negotiation failure (potential 406), throttling (potential 429), server failure (5xx), timeouts, and malformed/empty payloads. These are **planned cases, not measured ECB responses**. A transport error in the analysis environment is not evidence of ECB downtime.

**Non-trading days:** do not assume a rate for every retail calendar date. The business must approve whether to use the most recent prior **published** rate, wait for the next rate, use a monthly average, or follow another accounting policy (`OQ-04`). If a prior-rate policy is chosen, the boundary/lookback and maximum permitted staleness must be explicit; never silently fill gaps or substitute `0`.

**Reproducibility requirement:** retain series key, quotation direction, rate date, observed value, source retrieval timestamp, and—if used—revision/version evidence. Currency conversion of archived GBP lines requires historical rates for relevant dates, not 2026 spot rates.

## 2.8 Risk assessment against DE-001

| Risk ID / severity | Evidence or source gap | Affected DE-001 requirements | Business effect | Proposed decision / mitigation |
|---|---|---|---|---|
| **R-01 / HIGH** | Missing `CustomerID` on ~24.93% of lines [S] | `DR-04`, `FR-07`, `FR-08`, `NFR-01` | Customer-level spend, repeat rate and cohorts are incomplete and potentially biased. | Emma to approve denominator, treatment of unknown customers and display of unattributed spend; quantify amount coverage. |
| **R-02 / CRITICAL** | `C`/negative items lack proven original-sale linkage, effective histories [P][I] | `DR-02`, `FR-05`, `FR-04`, `NFR-06`, `AC-03`, `AC-05` | Partial/late cancellations and historical restatements cannot be guaranteed. | Michael to decide required fidelity; request source adjustment references or use **clearly labeled synthetic acceptance fixtures** for unsupported cases. |
| **R-03 / HIGH** | Revenue accounting meaning not inferable from `Quantity × UnitPrice` [P][I] | `FR-03`, `FR-04`, `FR-09`, `NFR-01`, `OQ-01`–`OQ-03` | Sales and Finance may publish different totals despite same raw records. | Obtain signed metric definition, inclusion of fees/tax/discount and historical attribution before metric approval. |
| **R-04 / HIGH** | Exact duplicate-looking rows; missing immutable line ID [S][I] | `DR-01`, `FR-01`–`FR-04`, `NFR-02`, `NFR-03` | Naive replay/dedup could over/under-count revenue; unreliable identity rules. | Measure repeated invoice/SKU pairs, inspect sample records and agree source-specific dedup policy; preserve original evidence. |
| **R-05 / HIGH** | Original data **GBP only**; currency approval, rate policy and ECB overlap unconfirmed [P][I] | `DR-03`, `FR-06`, `NFR-01`, `AC-04`, `OQ-04`, `OQ-14` | Misconverted financial totals or false claim of multicurrency ingestion. | Confirm GBP→EUR requirement, rate direction/date/rounding/non-business-day rules; validate actual ECB response. |
| **R-06 / HIGH** | No independent finance ledger/reference [P][I] | `FR-09`, `NFR-01`, `AC-08` | Cannot demonstrate true ledger reconciliation. | Finance to supply authoritative benchmark, or downgrade evidence explicitly to test-case reconciliation. |
| **R-07 / HIGH** | Source static in 2011, no ongoing transactions or update-status fields [P] | `FR-10`–`FR-12`, `NFR-03`–`NFR-05`, `OQ-07`, `OQ-11` | Cannot claim current Monday reporting; failure safety must be proven in a future system test. | Classify as historical replay/training, define failure/freshness acceptance fixtures and operational success criteria. |
| **R-08 / MEDIUM** | Service/non-product codes, negative/zero/extreme values [S] | `FR-02`–`FR-05`, `NFR-01` | Non-merchandise adjustments can contaminate product sales metrics. | Review suspicious rows with Finance; separate event categories in approved semantic policy. |
| **R-09 / MEDIUM** | Time zone unknown; truncated year boundaries; daily gaps not yet enumerated [P][I] | `FR-02`, `FR-04`, `FR-07`, `NFR-04` | Incorrect week/month comparisons and date-based FX matching. | Approve business zone/calendar and partial-period labels; reproduce day/month distribution. |
| **R-10 / MEDIUM** | ECB reference rate can be revised; no snapshot/retrieval metadata in retailer [P] | `NFR-06`, `FR-06`, `AC-05` | Historical converted totals may differ across re-runs. | Define immutable rate snapshot or revision/as-of policy for accepted reports. |
| **R-11 / HIGH — validation blocker** | Full UCI source and live ECB response **not profiled directly in this run** [T] | `DE-002` evidence acceptance; all empirical counts | Third-party calculations may use different cleaning logic/file versions. | Re-run companion script on UCI XLSX; record SHA-256, raw results and API response; peer-review discrepancies. |

### Go/no-go gates

**Permitted as a training/MVP hypothesis:** historical GBP invoice-line reporting; customer analysis for identified customers with an explicit excluded/unattributed population; test-case-defined cancellations; FX conversions **once** rate series and finance policy are confirmed. Clearly label this as a simulation, not a current operating platform.

**Do not claim acceptance of:** complete historical net/recognized revenue, full/partial cancellation linkage, a multi-original-currency source, independent ledger reconciliation, production freshness, or fault-tolerant publication *on the strength of these two source datasets alone*.

### Evidence required to move DE-002 to “Accepted”

1. **Raw-source reproducibility:** download UCI dataset 352 and retain original XLSX SHA-256, file size, acquisition date and schema. Reproduce every `[S]` metric and document any differences.
2. **Granularity and data quality:** calculate missingness **by month/country/cancellation type**, duplicate patterns (`all columns`, `InvoiceNo+StockCode`), abnormal-sign intersections and the effect of proposed inclusion rules on signed line values.
3. **Time-series audit:** output monthly row counts, distinct invoice dates, nontrading/missing days, boundary truncation and source timestamp validity.
4. **ECB integration evidence:** record actual HTTP response, exact CSV header, historical GBP/EUR rows, observation-status handling, date-match coverage, weekend/holiday case, one bad-request case, retrieval timestamp and response hash.
5. **Business decisions:** sign off revenue definition (`OQ-01`–`OQ-03`), conversion policy (`OQ-04`, `OQ-14`), cancellation linkage/fixtures (`OQ-15`), independent reconciliation oracle (`OQ-05`), and customer attribution policy (`OQ-08`, `OQ-09`).
6. **Release decision:** identify which `FR`/`AC` are supported **by raw source evidence**, which require synthetic fixtures/system behavior, and which remain explicitly deferred. Have a business owner approve that boundary.

## Reproduction and audit procedure

The companion script [`profile_sources.py`](profile_sources.py) is supplied **for local execution**. It profiles the original XLSX without dropping records, computes field nulls, duplicate candidates, negative/zero value intersections, extremes, month-level missingness, timestamp gaps, and source SHA-256. Optional ECB mode makes the specified historical API request and records the HTTP status, response SHA-256, schema, series-dimension consistency where available, dates and key rate-quality checks. No credentials are embedded.

```bash
python -m pip install pandas openpyxl requests
python profile_sources.py --download-retail --with-ecb --output profiling_evidence.json
# OR, if already downloaded from UCI:
python profile_sources.py --retail-xlsx 'Online Retail.xlsx' --with-ecb --output profiling_evidence.json
```

**Execution caveat:** this environment could not fetch the 22.6 MB UCI archive or the ECB service data. The script was syntax-checked and **smoke-tested on an explicitly synthetic 3-row XLSX**; successful smoke testing does **not** validate the full dataset counts or rate availability. The produced `profiling_evidence.json` on a network-enabled machine is the appropriate source for updating provisional `[S]` observations to `verified [T]` results.

**Interpretation caution:** the script reports raw data characteristics only; it deliberately does **not** deduplicate, choose a financial revenue definition, match cancellation lines to original invoices or fill missing FX dates. Those decisions belong to business validation, not unreviewed cleaning logic.

## Open questions for sign-off

| Owner | Required decision |
|---|---|
| **Michael (Finance)** | Are `Quantity × UnitPrice` and negative lines sufficient to model *any* approved revenue metric? How do cancellations, fees, tax, rounding and later restatements work? Which ledger is authoritative? |
| **Michael (Finance)** | Which reporting currency, FX date (invoice/recognition), rate direction, non-business-day fallback, rounding precision and revision policy apply? |
| **Emma (Customer Analytics)** | What share of monetary value lacks customer ID (to be measured)? How do unattributed, repeat and high-value customer metrics account for the missing population? |
| **Sarah (Sales)** | Which dimensions are actually required beyond available product, customer country and timestamp? Does the archived 2010–2011 timeframe serve only a demo, rather than actual weekly business reports? |
| **Daniel (Engineering)** | How are published-data consistency, failure state, last successful update, backfill and source integrity verified with separate system-level acceptance fixtures? |
| **Sponsor / governance** | Does the team accept historical replay and constrained source coverage as MVP scope, or must additional operational/financial sources be supplied? |

## References and evidence provenance

- **[P-1]** UCI dataset 352, *Online Retail*, DOI and original description: https://archive.ics.uci.edu/dataset/352/online+retail (CC BY 4.0; 541,909 observations; 8 listed variables; GBP price; cancellation prefix; published date range).
- **[S-1]** Independent raw-data quality assessment with completeness, duplicate, cancellation and validity counts: https://github.com/ermakovamus/Online-retail-dataset-assesment/blob/main/README.md (analysis dated 2026-04-26; **secondary, not guaranteed independently reproducible**).
- **[S-2]** Independent R exploration with timestamp bounds, value extremes and missing values: https://kimberlyhwaldron.github.io/TimeSeries_OnlineRetailData/ (secondary analysis of Excel dataset).
- **[S-3]** Separate raw-file notebook/write-up corroborating customer/description nulls: https://github.com/eaintkyawthmu/UCI_Online_Retail_Dataset_Cleaned_Version (use raw-file exploratory results; **not** its cleaned output as source of the above counts).
- **[P-2]** ECB Data API data examples: https://data.ecb.europa.eu/help/api/data-examples and data parameters: https://data.ecb.europa.eu/help/api/data.
- **[P-3]** ECB EXR dimensional schema: https://data.ecb.europa.eu/data/datasets/EXR/structure; content negotiation: https://data.ecb.europa.eu/help/api/content-negotiation.
- **[P-4]** ESCB reuse policy: https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html.
- **[BRS]** Project's reviewed business requirements (`v0.2`): https://github.com/AgnieszkaPawlak/retail-analytics-data-platform/blob/main/business/requirements.md.

**Reviewer note:** UCI's landing-page field “Has Missing Values? No” conflicts with the secondary empirical missing-value analyses. Prefer a hash-identified raw-file recomputation to settle that inconsistency. No arbitrary 90% “accuracy score” from a third-party notebook is adopted as proof that finance definitions are correct: business validity is not the same as a single technical row filter.

---

**DE-002 disposition:** **Reviewed with corrections / empirical profiling incomplete.** The appropriate next step is to run the raw-file and ECB checks above, fill the missing per-period statistics and live API observations, and obtain Finance/Customer business-policy decisions **before** promoting this report to a verified source baseline or starting to claim DE-001 acceptance.

## Technical Lead Review — v0.2 (2026-11-02)

**Review scope:** `sourceprofiling.md` and companion `profile_sources.py` in the repository. This was a static technical review of the GitHub source; no successful full-data execution or live ECB API response was independently verified during this review.

### Corrections recorded

1. **Evidence status clarified.** External-source statistics ([S]) remain useful hypotheses, not measurements from the source XLSX. DE-002 is reviewed but cannot be marked empirically complete until an identified raw-file SHA-256 and an API response record are provided.
2. **Prevented stale-file misattribution in the collector.** A failed `--download-retail` request must not silently profile an existing local `Online Retail.xlsx` as though the new download succeeded. The collector now distinguishes `not_measured_download_failed` from successful retrieval.
3. **Improved source-profile coverage.** The script now additionally records missing `CustomerID` and `Description` counts by country and by invoice-prefix class, supplementing existing month-level analysis. These outputs are still to be generated against the real dataset.
4. **Improved ECB audit evidence.** The script records a SHA-256 fingerprint of the HTTP response and, where series dimensions are returned, checks that the response belongs to the requested `D.GBP.EUR.SP00.A` series.
5. **Scope remains constrained.** There is still no evidence of full cancellation lineage, a second original transaction currency, or an independent finance ledger. Business approval and additional fixtures are required for those claims.

### Reviewer-identified gaps still open

- The script has not been run successfully on the original UCI XLSX and ECB response in this review; published [S] figures must be reconciled against actual collector outputs.
- Missingness by country and invoice class is now instrumented, but validity intersections, full row-level reconciliation, and effect on signed line amounts still need explicit evidence.
- ECB response validation still requires real execution, observation-date coverage analysis, a non-trading-day case, failure-case testing, and a documented policy for historical rates.
- Unit/integration tests for the collector and committed execution evidence are not present in the repository snapshot reviewed.

**Decision for roadmap:** Proceed to **DE-003 — Data Contracts & Quality Rules** provisionally using the documented source schema and explicit assumptions. Keep DE-002 evidence completion as a blocking prerequisite before accepting final data contracts or implementing ingestion against unverified assumptions.
