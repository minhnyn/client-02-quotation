# Session 7 Human UI, JSON Export & Fresh-Checkout Review Protocol (`HP-AC05`–`HP-AC07`, `B4`–`B6`, `D1`)

- **Project ID / Task ID:** `quotation-02` / `HP-S7-001`
- **Product Repository:** `HansePack Handelsgesellschaft` (`../client-02-quotation`, GitHub: [`minhnyn/client-02-quotation`](https://github.com/minhnyn/client-02-quotation))
- **GitHub Issue:** [`minhnyn/client-02-quotation#2`](https://github.com/minhnyn/client-02-quotation/issues/2) · [`mfadhilahm/agentic_ai_haw_2627#5`](https://github.com/mfadhilahm/agentic_ai_haw_2627/issues/5)
- **Review Date:** `2026-11-23` (Termin 7)
- **Accountable Human Reviewers (`D1`):**
  - `saad` – Requirements Owner & Technical Release Candidate Gate Approval (`Q-BASE`)
  - `felix` – QA & Business Reference Verification (`Q01`–`Q14`, `E01`–`E10`, Controlled Fault Rejection)
  - `mirko` – Web UI & JSON Export Verification

---

## 1. Fresh-Checkout Independent Startup & Fixture Provenance Check (`HP-AC01`, `HP-AC07`, `B6`)

### 1.1 Independent Startup Without Factory or LLM
The product was started and tested from a clean checkout of `client-02-quotation` with no Software Factory modules (`src.agents`, `src.llm`) or LLM server on `PYTHONPATH`:

```powershell
# 1. Automated full business & validation test suite (Q01-Q14, E01-E10, export consistency)
python -m pytest tests/test_quotation_s7.py -v
python -m unittest discover -s tests -p "test_*.py" -v

# 2. Standalone CLI verification (multi-line Q12 & single-line Q03)
python main.py --items-json '[{"sku": "HP-BOX", "quantity": 50}, {"sku": "HP-TAPE", "quantity": 10}]'

# 3. Local Web UI startup (FastAPI / Uvicorn on http://127.0.0.1:8000)
python app.py
```

### 1.2 Unchanged Customer Fixture Provenance
Both binding customer fixtures in `data/` were verified byte-for-byte prior to and during review:
- `data/HansePack_Katalog.json`: `SHA-256 = 70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a` (**Unchanged**)
- `data/HansePack_Referenzfaelle.json`: `SHA-256 = 7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a` (**Unchanged**)

---

## 2. Human Web UI & JSON Export Walkthrough (`HP-AC05`, `HP-AC06`, `B4`, `B5`)

### 2.1 Visible Net & Course Project Notice (`HP-AC05`, `B4`)
- **Checked by:** `saad`, `mirko`
- **Observation:** The top banner and quotation result header in the web UI (`http://127.0.0.1:8000/`) and the `"course_notice"` field in the exported JSON both display verbatim:
  > `Net amounts – course project, not a binding quotation` (`Nettobeträge – Lehrprojekt, kein verbindliches Angebot`)
- **VAT Check:** No VAT is added anywhere; all prices are clearly labeled as simulated net amounts in `EUR` (`integer` cents in JSON).

### 2.2 Multi-Line Case `Q12` (`HP-BOX × 50` + `HP-TAPE × 10`) – UI Display vs. Downloaded JSON (`B4`, `B5`)
- **Action Performed by Human Reviewer (`saad`, `felix`):**
  1. In Line 1 of the Web UI, selected SKU **`HP-BOX`** and entered quantity **`50`**.
  2. In Line 2 of the Web UI, selected SKU **`HP-TAPE`** and entered quantity **`10`**.
  3. Clicked **Calculate Quotation** (`POST /api/quotation`) and inspected the displayed line table and summary totals.
  4. Clicked **Download JSON** (`POST /api/quotation/export` $\rightarrow$ `hansepack-quotation.json`) and compared every field against the Web UI display and customer reference case `Q12` in `data/HansePack_Referenzfaelle.json`.

| Field | Customer Reference (`Q12`) | Web UI Displayed Value | Downloaded `hansepack-quotation.json` | Match? |
| :--- | ---: | ---: | ---: | :---: |
| **`currency` / `rule_version`** | `"EUR"` / `"HP-V1"` | `EUR` / `HP-V1` | `"currency": "EUR"`, `"rule_version": "HP-V1"` | **Yes (100%)** |
| **Line 1 (`HP-BOX × 50`) `unit_price_cents`** | `250` | `250 ct` (`2,50 EUR`) | `250` | **Yes (100%)** |
| **Line 1 (`HP-BOX × 50`) `list_amount_cents`** | `12500` | `12500 ct` (`125,00 EUR`) | `12500` | **Yes (100%)** |
| **Line 1 (`HP-BOX × 50`) `discount_percent` / `discount_cents`** | `5%` / `625` | `5%` / `625 ct` (`6,25 EUR`) | `"discount_percent": 5`, `"discount_cents": 625` | **Yes (100%)** |
| **Line 1 (`HP-BOX × 50`) `net_cents`** | `11875` | `11875 ct` (`118,75 EUR`) | `11875` | **Yes (100%)** |
| **Line 2 (`HP-TAPE × 10`) `unit_price_cents`** | `400` | `400 ct` (`4,00 EUR`) | `400` | **Yes (100%)** |
| **Line 2 (`HP-TAPE × 10`) `list_amount_cents`** | `4000` | `4000 ct` (`40,00 EUR`) | `4000` | **Yes (100%)** |
| **Line 2 (`HP-TAPE × 10`) `discount_percent` / `discount_cents`** | `0%` / `0` | `0%` / `0 ct` (`0,00 EUR`) | `"discount_percent": 0`, `"discount_cents": 0` | **Yes (100%)** |
| **Line 2 (`HP-TAPE × 10`) `net_cents`** | `4000` | `4000 ct` (`40,00 EUR`) | `4000` | **Yes (100%)** |
| **`goods_net_cents`** | **`15875`** | **`15875 ct` (`158,75 EUR`)** | **`15875`** | **Yes (100%)** |
| **`shipping_cents` (`HP-V1`, `< 50000`)** | **`1200`** | **`1200 ct` (`12,00 EUR`)** | **`1200`** | **Yes (100%)** |
| **`total_cents` (`HP-V1`)** | **`17075`** | **`17075 ct` (`170,75 EUR`)** | **`17075`** | **Yes (100%)** |

**Exact Downloaded JSON Payload (`hansepack-quotation.json` for `Q12`):**
```json
{
  "currency": "EUR",
  "rule_version": "HP-V1",
  "course_notice": "Net amounts – course project, not a binding quotation",
  "lines": [
    {
      "sku": "HP-BOX",
      "quantity": 50,
      "unit_price_cents": 250,
      "list_amount_cents": 12500,
      "discount_percent": 5,
      "discount_cents": 625,
      "net_cents": 11875
    },
    {
      "sku": "HP-TAPE",
      "quantity": 10,
      "unit_price_cents": 400,
      "list_amount_cents": 4000,
      "discount_percent": 0,
      "discount_cents": 0,
      "net_cents": 4000
    }
  ],
  "goods_net_cents": 15875,
  "shipping_cents": 1200,
  "total_cents": 17075
}
```

### 2.3 Human Verification of Invalid Inputs Reaching Python Business Logic (`HP-AC04`, `B3`, `B4`)
To verify that invalid inputs are **not** merely blocked in browser HTML attributes but actually reach `calculate_quotation()` in Python and return a structured error without producing a quotation:

| Negative Case Tested in UI | User Input in Browser Form | Python Backend Response (`POST /api/quotation`) | Observed UI Behavior | Status |
| :--- | :--- | :--- | :--- | :---: |
| **`E01` (Quantity `0`)** | Line 1: `HP-BOX`, Quantity: `0` | HTTP `400` (`QuotationValidationError`, `reason: "quantity_out_of_range"`, `"Invalid quantity 0 for SKU 'HP-BOX': quantity must be between 1 and 10000."`) | Visible error banner displayed; previous quotation result & JSON export hidden/disabled; no valid quotation created. | **Passed** |
| **`E03` (Duplicate SKU)** | Line 1: `HP-BOX × 10`, Line 2: `HP-BOX × 20` | HTTP `400` (`QuotationValidationError`, `reason: "duplicate_sku"`, `"Duplicate SKU 'HP-BOX'; each SKU may appear at most once per quotation."`) | Visible error banner displayed; no silent aggregation to `30` units; no valid quotation created. | **Passed** |
| **`E07` / `E08` (Non-Integer / String)** | Line 1: `HP-BOX`, Quantity: `1.5` / `"abc"` | HTTP `400` (`QuotationValidationError`, `reason: "quantity_not_integer"` / `"quantity_wrong_type"`) | Visible error banner displayed; no silent rounding or coercion. | **Passed** |

---

## 3. Separation of Approved Release Candidate (`Q-BASE`), Blocked Fault State, and Customer Acceptance (`D1`)

| State / Run | Decision & Accountable Human | Product State & Isolation |
| :--- | :--- | :--- |
| **Release Candidate `Q-BASE` (`WF-QUOTATION02-S7-001`)** | **Technical Team Gate: `approved`** (`saad`, `felix`, `2026-11-23`) | Passes all `14/14` valid (`Q01`–`Q14`) and `10/10` invalid (`E01`–`E10`) tests plus human UI/export review. Frozen as **`Q-BASE`** on `main`. |
| **Controlled Fault Run (`WF-QUOTATION02-S7-FAULT-001`)** | **Technical Team Gate: `changes_requested` / blocked (`escalate_to_human`)** (`felix`, `2026-11-23`) | Executed on an isolated checkout with 5% discount boundary `quantity > 50` instead of `>= 50`. Failed `Q03` (`13700 != 13075` cents, `pytest_exit_code = 1`). **Blocked by Factory gate and never merged into `main`.** |
| **Isolated `R-02` Baseline (`R-02-BASELINE-001`)** | **Baseline Experiment Recorded** (`yaw`, `muhammad`, `2026-11-23`) | Executed on an isolated copy of `Q-BASE` (`calculation_note: "Net amounts; shipping shown separately."`). **Isolated experiment; not merged into customer release `main`.** |
| **External Customer Acceptance** | **`pending_customer_acceptance`** | Strictly separated from internal team technical gate approval; awaits live instructor acceptance review. |
