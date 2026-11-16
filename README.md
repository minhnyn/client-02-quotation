# HansePack Handelsgesellschaft – Quotation Calculator (`client-02-quotation`)

> **Course Notice:**  
> Net amounts – course project, not a binding quotation.

Customer product repository for **Customer Project 02 (HansePack Handelsgesellschaft)**, developed through our existing Software Factory (`agentic_ai_haw_2627`).

---

## 1. Runtime Requirements & Zero Factory Dependency (`HP-AC01`)

- **Python:** Python `>= 3.11` (verified on Python `3.12.10`)
- **Third-Party Runtime Dependencies:** None (uses Python standard library only: `decimal`, `json`, `pathlib`, `argparse`)
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
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 4. Scope & Documentation

- **Session 6 Customer Issue:** [`docs/issue-01-session-06.md`](docs/issue-01-session-06.md) (`HP-S6-001`)
- **Binding Fixtures (Unchanged):**
  - [`data/HansePack_Katalog.json`](data/HansePack_Katalog.json) (`SHA-256: 70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a`)
  - [`data/HansePack_Referenzfaelle.json`](data/HansePack_Referenzfaelle.json) (`SHA-256: 7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a`)
