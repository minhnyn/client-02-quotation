# Issue #2: [HP-S7-001] Session 7 Complete HP-V1 Quotation Calculator, Small Web UI, JSON Export, Full Q01–Q14 / E01–E10 Suite & Controlled Fault Verification

- **Project ID:** `quotation-02`
- **Customer:** `HansePack Handelsgesellschaft` (fictional B2B packaging supplier)
- **Task IDs:**
  - `HP-S7-001` – Customer Release Candidate (`HP-AC01`–`HP-AC07` under `HP-V1`, frozen as **`Q-BASE`**)
  - `HP-S7-FAULT-001` – Controlled Discount Boundary Fault (`> 50` instead of `>= 50` on isolated checkout, blocked by quality gate)
  - `R-02` – Isolated Reference Baseline Experiment (`calculation_note: "Net amounts; shipping shown separately."` on isolated copy of `Q-BASE`, not merged into customer release)
- **GitHub Issue Links:**
  - Product Repository Issue: [`minhnyn/client-02-quotation#2`](https://github.com/minhnyn/client-02-quotation/issues/2)
  - Factory Repository Issue: [`mfadhilahm/agentic_ai_haw_2627#5`](https://github.com/mfadhilahm/agentic_ai_haw_2627/issues/5)
- **Session:** Termin 7 (`2026-11-23`)
- **Target Product Files:** `quotation/calculator.py`, `app.py`, `main.py`
- **Target Product Test Suite:** `tests/test_quotation_s7.py`

---

## 1. Binding Customer Fixtures & Provenance (Unchanged)

The official customer fixtures in `data/` remain strictly read-only and byte-identical to the course task sheets:

| Fixture File | Purpose | Verified SHA-256 |
| :--- | :--- | :--- |
| [`data/HansePack_Katalog.json`](../data/HansePack_Katalog.json) | Binding SKU catalogue (`HP-BOX`: `250` cents, `HP-TAPE`: `400` cents, `HP-FILM`: `1250` cents) | `70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a` |
| [`data/HansePack_Referenzfaelle.json`](../data/HansePack_Referenzfaelle.json) | Binding valid reference cases `Q01`–`Q14` (`HP-V1` & `HP-V2`) and invalid cases `E01`–`E10` | `7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a` |

---

## 2. Session 7 Scope (`HP-AC01`–`HP-AC07`)

1. **`HP-AC01` & `HP-AC07` (Independent Release Candidate `Q-BASE`):**
   - Versioned Release Candidate (`Q-BASE`) starts and passes all automated tests from a fresh checkout (`python app.py`, `python main.py`, `python -m pytest tests/test_quotation_s7.py -q`) without any runtime dependency on the Software Factory or an LLM.
2. **`HP-AC03` (All Valid Reference Cases `Q01`–`Q14` under `HP-V1`):**
   - Full support for all three SKUs (`HP-BOX`, `HP-TAPE`, `HP-FILM`), per-line quantity discount tiers (`1–49`: `0%`, `50–99`: `5%`, `>= 100`: `10%` applied to the entire line list amount), commercial half-up rounding (`Decimal` `ROUND_HALF_UP`, specifically verified on half-cent cases `Q04` `1237.5 -> 1238`, `Q13` `3187.5 -> 3188`, `Q14` `662.5 -> 663`), and `HP-V1` shipping (`1200` cents when `goods_net_cents < 50000` after discount as in `Q06`, `0` cents when `goods_net_cents >= 50000` as at threshold `Q07`).
3. **`HP-AC04` (All Invalid Reference Cases `E01`–`E10` Rejected in Python Business Logic):**
   - All invalid inputs (`E01` quantity `0`, `E02` negative quantity `-5`, `E03` duplicate SKU `HP-BOX`, `E04` unknown SKU `HP-PALLET`, `E05` empty line list `[]`, `E06` quantity `10001 > 10000`, `E07` fractional quantity `1.5`, `E08` string quantity `"50"`, `E09` missing quantity `None`, `E10` 4 lines `> 3`) reach Python business logic (`calculate_quotation`) and raise `QuotationValidationError` without silent type coercion or SKU aggregation.
4. **`HP-AC05` (Small Usable Web UI):**
   - Local web interface (`app.py` / FastAPI + HTML/JS) allowing entry of 1–3 line items, displaying calculated line values, totals, and understandable validation error messages from Python backend validation, and prominently displaying `"Net amounts – course project, not a binding quotation"`.
5. **`HP-AC06` (Consistent JSON Export Download):**
   - JSON export (`export_quotation_dict` / `POST /api/quotation/export`) contains all mandatory integer-cent fields (`sku`, `quantity`, `unit_price_cents`, `list_amount_cents`, `discount_percent`, `discount_cents`, `net_cents`, `goods_net_cents`, `shipping_cents`, `total_cents`, `currency: "EUR"`, `rule_version: "HP-V1"`, `course_notice`) and matches the displayed calculation byte-for-byte.

---

## 3. Controlled Fault Verification (`L7.2`, `L7.3`) & `R-02` Baseline (`L7.4`)

- **Controlled Discount Fault (`HP-S7-FAULT-001`):** On an isolated checkout/branch, change the 5% discount boundary from `quantity >= 50` to `quantity > 50` (starting at `51`). Case `Q03` (`HP-BOX × 50`) must fail in `tests/test_quotation_s7.py` with total `13700` cents (`0%` discount) instead of expected `13075` cents (`5%` discount = `625` cents), causing the Factory workflow to block approval (`human_gate_status = "escalate_to_human"`, human decision `"changes_requested"`). Never merge the fault state into `main`.
- **Isolated `R-02` Baseline Experiment (`R-02-BASELINE-001`):** On an isolated copy of `Q-BASE` using `F-BASE`, add `"calculation_note": "Net amounts; shipping shown separately."` to the exported quotation JSON while keeping all monetary values, validation rules, and `Q01`–`Q14`/`E01`–`E10` checks passing. Preserve metrics and artifacts under `runs/quotation-02/R-02-BASELINE-001/` without merging into `main`.

---

## 4. Accountable Humans (`D1`)

| Responsibility | Accountable Human(s) | Factory Role(s) |
| :--- | :--- | :--- |
| **Commission, Budget & `R-02` Cost / Evidence Lead** | `yaw` | `managing_director_customer_lead`, `cost_observability_engineer` |
| **Requirements Owner, GitHub Issue #2 & Candidate Gate Approval** | `saad` | `product_owner_requirements` |
| **Full `Q01`–`Q14` / `E01`–`E10` Test Suite & Fault Gate Rejection** | `felix` | `qa_test_engineer`, `project_manager` |
| **Software Architecture & `quotation-02.yaml` Task Contracts** | `minh` | `software_architect` |
| **Technical Delivery, Web UI & JSON Export (`app.py`, `calculator.py`)** | `mirko` | `backend_api_engineer` |
| **Factory Workflow, Fault/Baseline Execution & Gate Unit Tests** | `muhammad` | `agent_engineer`, `integration_engineer` |
