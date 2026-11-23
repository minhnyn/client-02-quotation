# HansePack Handelsgesellschaft – Quotation Calculator (`client-02-quotation`)

> **Course Notice:**  
> Net amounts – course project, not a binding quotation.

Customer product repository for **Customer Project 02 (HansePack Handelsgesellschaft)**, developed through our existing Software Factory (`agentic_ai_haw_2627`).

---

## 1. Runtime Requirements & Zero Factory Dependency (`HP-AC01`)

- **Python:** Python `>= 3.11` (verified on Python `3.12.10`)
- **Calculator and CLI:** Python standard library only.
- **Web UI:** FastAPI and Uvicorn; tests additionally use pytest and HTTPX (installation below).
- **Factory / LLM Dependency:** None — all pricing, discount, rounding (`ROUND_HALF_UP`), shipping (`HP-V1`), and input validation run deterministically in Python without the Software Factory or any LLM.

---

## 2. Independent Startup & CLI Invocation (`HP-AC01`, `HP-AC02`, `HP-AC04`)

Run directly from a checkout of `client-02-quotation`:

```powershell
# Case Q01: HP-BOX x 1 (goods_net=250, shipping=1200, total=1450 cents)
python main.py --sku HP-BOX --quantity 1

# Case Q03: HP-BOX x 50 (list=12500, discount=625, goods_net=11875, shipping=1200, total=13075 cents)
python main.py --sku HP-BOX --quantity 50

# Case E01: quantity 0 (rejected with understandable error, exit code 1)
python main.py --sku HP-BOX --quantity 0
```

Multi-line JSON input is also supported:

```powershell
python main.py --items-json '[{"sku": "HP-BOX", "quantity": 50}, {"sku": "HP-TAPE", "quantity": 10}]'
```

---

## 3. Separate Automated Product Tests (`HP-AC01`, `HP-AC02`, `HP-AC04`)

Automated checks verify fixture SHA-256 provenance (`data/HansePack_Katalog.json`, `data/HansePack_Referenzfaelle.json`), `Q01`, `Q03`, and `E01` against customer-supplied expectations:

```powershell
python -m pytest tests/test_quotation_s6.py -q
```

Or using the Python standard library only (zero external packages required):

```powershell
python -m unittest discover -s tests -p "test_quotation_s6.py" -v
```

---

## 4. Scope & Documentation

- **Session 6 Customer Issue:** [`docs/issue-01-session-06.md`](docs/issue-01-session-06.md) (`HP-S6-001`)
- **Binding Fixtures (Unchanged):**
  - [`data/HansePack_Katalog.json`](data/HansePack_Katalog.json) (`SHA-256: 70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a`)
  - [`data/HansePack_Referenzfaelle.json`](data/HansePack_Referenzfaelle.json) (`SHA-256: 7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a`)


## 5. Session 7 Web UI and JSON Download

Start from a fresh checkout with Python 3.11 or newer. No Factory, database,
model provider or API key is needed. Run all commands in the product repository.

```powershell
git clone https://github.com/minhnyn/client-02-quotation.git
cd client-02-quotation
git switch feat/s7-product-ui-and-tests
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi==0.141.1 uvicorn==0.52.4 httpx==0.28.1 pytest==9.1.1
python app.py
```

On macOS/Linux activate with `source .venv/bin/activate`. If PowerShell blocks
activation, invoke `.\.venv\Scripts\python.exe` instead of `python` directly.
The feature branch must be pushed before another machine can check it out;
after merging, use the release commit or `main` instead.

Open http://127.0.0.1:8000. Stop the server with Ctrl+C.
The app binds only to the local machine. JavaScript is required for the form.

Enter one to three positions, calculate, inspect line values and totals, then
choose **JSON herunterladen**. All position amounts are displayed in integer
cents; totals also include a EUR rendering. The exact result object is visible
under **Berechnetes JSON anzeigen**. Changing an input invalidates the old result
and disables its download until recalculation. No calculations are performed by
an LLM or duplicated in the UI.

### HTTP contract

- `GET /`: German web interface with the visible course notice.
- `POST /api/quotation`: accepts `{"items": [{"sku": "HP-BOX", "quantity": 50}]}`.
- `POST /api/quotation/export`: accepts the same input; returns the same JSON
  bytes with an attachment header for `hansepack-quotation.json`.
- Success is HTTP 200. Validation errors are HTTP 400 with
  `{"error": {"reason": "...", "message": "..."}}`, without quotation totals.
- Both endpoints call `calculate_quotation(items)` without coercing JSON values.
  Monetary fields are integer cents, currency is `EUR`, and rule version is `HP-V1`.

Quantity inputs use text fields and the form uses `novalidate`. Integer text
entered in the form is encoded as a JSON number. Decimal input such as `1.5`
is sent as a decimal; empty input and `abc` are sent unchanged as strings.
Values such as `1.0` are not silently truncated into integers. The API rejects
string quantities such as `"50"` and booleans without conversion. Zero, negative,
empty, nonnumeric and duplicate-SKU inputs reach Python business validation;
the UI displays its error. There is no HTML `min`, `max`, `required` or `pattern`
validation preventing these submissions.

### Independent tests

```powershell
python -m pytest tests/test_quotation_s7.py -v
python -m pytest -q
```

The S7 suite reads `data/HansePack_Referenzfaelle.json` unchanged. The mapping is
`expected_lines` to `result.lines`, and every `expected["HP-V1"]` field to the
same result key. All Q01–Q14 compare complete positions and totals, including
half-up rounding Q04/Q13/Q14, shipping after discount Q06 and the exact 50000-cent
threshold Q07. E01–E10 must raise `QuotationValidationError` in the calculator.
API tests verify those inputs reach the calculator, are rejected on both routes,
and cannot become downloads. All valid cases compare calculation, display API
and export, including exact response bytes and integer types. Additional tests
cover three/four lines, malformed JSON and missing or incorrectly typed input.
The existing S6 tests also verify customer fixture hashes.

For a manual browser check use HP-BOX × 50 plus HP-TAPE × 10 (Q12): goods 15875,
shipping 1200, total 17075 cents. Compare the downloaded JSON with the visible
JSON. Then try 0, -1, 1.5, abc, an empty quantity and duplicate SKUs; each must
show a server error and hide the previous result. Check narrow-screen layout
and keyboard navigation. Automated API tests do not replace human release approval.
