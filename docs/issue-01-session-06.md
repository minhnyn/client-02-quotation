# Issue #1: [HP-S6-001] Session 6 HansePack Initial Quotation Calculator Slice (HP-AC01, HP-AC02 Q01/Q03, HP-AC04 E01)

- **Project ID:** `quotation-02`
- **Customer:** `HansePack Handelsgesellschaft` (fictional B2B packaging supplier)
- **Task ID:** `HP-S6-001`
- **Session:** Session 6 (Second customer, same Software Factory)
- **Target Product Path:** `quotation/calculator.py` (invoked independently via `main.py`)
- **Target Product Test:** `tests/test_quotation_s6.py`

---

## 1. Customer Fixtures & Provenance (Unchanged)

The official customer inputs were copied unchanged without modification into `data/`:

| Fixture File | Purpose | Verified SHA-256 |
| :--- | :--- | :--- |
| [`data/HansePack_Katalog.json`](../data/HansePack_Katalog.json) | Binding SKU catalogue (`HP-BOX`, `HP-TAPE`, `HP-FILM`) and unit prices in integer cents | `70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a` |
| [`data/HansePack_Referenzfaelle.json`](../data/HansePack_Referenzfaelle.json) | Customer reference cases `Q01`–`Q14` (`HP-V1` & `HP-V2`) and invalid cases `E01`–`E10` | `7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a` |

---

## 2. Today's Scope (Session 6) vs. Roadmap (Sessions 7–8)

### In Scope for Session 6 (`HP-S6-001`)
1. **`HP-AC01` (Initial Version):** Separate product repository (`client-02-quotation`), documented independent startup (`main.py`) and automated test commands (`tests/test_quotation_s6.py`), zero runtime dependency on the Software Factory or any LLM.
2. **`HP-AC02` (`Q01` & `Q03` under `HP-V1`):** Deterministic Python quotation calculation using integer cents and `Decimal` with `ROUND_HALF_UP`:
   - **`Q01` (`HP-BOX` × 1):** unit price `250` cents, list `250` cents, discount `0%` (`0` cents), line net / goods net `250` cents, shipping `1200` cents, total `1450` cents (`EUR`, `HP-V1`).
   - **`Q03` (`HP-BOX` × 50):** unit price `250` cents, list `12500` cents, discount `5%` (`625` cents), line net / goods net `11875` cents, shipping `1200` cents, total `13075` cents (`EUR`, `HP-V1`).
3. **`HP-AC04` (`E01` minimum):** Reject quantity `0` in Python business logic with an understandable error and produce no valid quotation.

### Explicitly Scheduled for Later Sessions (Out of S6 Scope)
- **Session 7:** Full `Q01`–`Q14` coverage under `HP-V1` (`HP-AC03`), full invalid case suite `E01`–`E10` (`HP-AC04`), FastAPI/HTML web UI (`HP-AC05`), JSON export download (`HP-AC06`), fresh checkout & controlled fault verification (`HP-AC07`), plus `R-02` baseline experiment.
- **Session 8:** Announced shipping change **`CR-02`** (`HP-V2`: shipping `1500` cents below `40000` cents goods net after discount, `0` cents from `40000` cents; `HP-AC08`, `HP-AC09`) and `R-02` Factory evaluation.

---

## 3. Open Questions, Clarifications & Explicit Assumptions

| Topic | Question / Ambiguity | Binding Clarification / Explicit Assumption |
| :--- | :--- | :--- |
| **Monetary Arithmetic & Rounding** | How should fractional cents in percentage discounts be rounded? | **Clarified in Brief:** Use integer cents / `decimal.Decimal` (never binary floats) and round each line's discount amount using `ROUND_HALF_UP` (half-up to whole cents). |
| **Discount Tier Semantics** | Does the quantity discount apply marginally or to the whole line, and across SKUs? | **Clarified in Brief:** Applied per line to the entire list amount of that single line (`1–49`: `0%`, `50–99`: `5%`, `100+`: `10%`), not marginally and not summed across SKUs. |
| **Shipping Rule Version (`HP-V1`)** | When is shipping free in S6/S7? | **Clarified in Brief (`HP-V1`):** `1200` cents if goods net (sum of line net amounts after discounts) `< 50000` cents; `0` cents if `>= 50000` cents. |
| **Input Validation** | Which input shapes and types are valid? | **Clarified in Brief & Reference Data:** `1–3` lines, unique SKUs present in `HansePack_Katalog.json`, integer quantities in `[1, 10000]`. Reject `bool` (`isinstance(qty, bool)`), `float`, `str`, `<= 0`, `> 10000`, missing quantities, duplicate SKUs, unknown SKUs, and empty lists without coercion. |
| **Session 6 Interface** | Is a web UI required in Session 6? | **Clarified in Task Sheet S6:** No. A Python calculation module (`quotation/calculator.py`) with reproducible CLI invocation (`main.py`) suffices for S6; web UI and JSON download follow in S7. |
| **VAT & Net Notice** | Should VAT be added, and how is the net notice surfaced in S6? | **Clarified in Brief:** No VAT calculation; simulated net EUR amounts only. Include `"course_notice": "Net amounts – course project, not a binding quotation"` in structured quotation output and display it in the CLI/UI. |
| **Open Customer Confirmation** | Should the S6/S7 web UI in S7 display German or English labels, and is a timestamp/quotation number desired in the JSON export? | **Open Question for Instructor (Customer):** Brief permits DE or EN UI and marks timestamp/quotation number optional. **Explicit S6 Assumption:** English API/JSON keys matching `HansePack_Referenzfaelle.json` (`sku`, `quantity`, `unit_price_cents`, `list_amount_cents`, `discount_percent`, `discount_cents`, `net_cents`, `goods_net_cents`, `shipping_cents`, `total_cents`, `currency`, `rule_version`) with no optional timestamp/quotation ID so outputs compare cleanly against reference values. |

---

## 4. Delivery Budget Plan (`S6`/`S7`) & `CR-02` Reserve (`S8`)

Consistent with the course credit model (`100` credits/person-hour human, `1.0 + 0.01/s + 0.02/1k in + 0.04/1k out` agent, `1.0` credit/CI run), customer delivery is budgeted separately from one-off Factory adaptation:

| Budget Scope | Human (Credits) | Agent (Credits) | CI (Credits) | Total Planned Credits | Notes |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **`S6` + `S7` Customer Delivery (`HP-AC01`–`HP-AC07`)** | `600.0` *(6.00 h)* | `25.0` | `6.0` | **`631.0`** | Covers S6 Python core/CLI/tests (`~1.5 h` delivery + review) and S7 full rules, web UI, JSON export, fault test (`~4.5 h`). |
| **`S8` Change Reserve (`CR-02` / `HP-V2`, `HP-AC08`–`HP-AC09`)** | `300.0` *(3.00 h)* | `10.0` | `5.0` | **`315.0`** | Reserved strictly for Session 8 shipping change (`HP-V2`), regression checks, and release handover. |
| **Separate Factory Multi-Project Adaptation (`S6`–`S8`)** | `150.0` *(1.50 h)* | — | — | **`150.0`** | One-off central Factory engineering (`config/projects/quotation-02.yaml`, Python module delivery support, isolation tests). |

---

## 5. Accountable Humans

| Responsibility | Accountable Human(s) | Factory Role(s) |
| :--- | :--- | :--- |
| **Commission & Cost / Budget Lead** | `yaw` | `managing_director_customer_lead` |
| **Requirements Owner & Technical Gate Approval** | `saad` | `product_owner_requirements` |
| **Project Manager, QA & Product Checks** | `felix` | `project_manager`, `qa_test_engineer` |
| **Software Architecture (`architect_node`)** | `minh` | `software_architect` |
| **Technical Delivery (`implementation_node`)** | `mirko` | `backend_api_engineer` |
| **Agent Integration & Project Isolation** | `muhammad` | `agent_engineer`, `integration_engineer` |
