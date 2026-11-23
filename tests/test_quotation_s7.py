"""Independent automated product test suite for HansePack Session 7 (HP-AC01..HP-AC07, B1..B6).

Verifies:
1. Unchanged customer fixture provenance (SHA-256 of HansePack_Katalog.json and HansePack_Referenzfaelle.json)
   and zero Factory/LLM runtime dependencies (B6, HP-AC01, HP-AC07).
2. All 14 valid customer reference cases Q01-Q14 under HP-V1: line values, 0%/5%/10% tier boundaries,
   Decimal ROUND_HALF_UP half-cent cases (Q04, Q13, Q14), shipping evaluation after discount (Q06)
   and at the 50,000-cent threshold (Q07), and summary totals (B1, B2, HP-AC03).
3. All 10 invalid customer reference cases E01-E10 rejected in Python business logic without silent
   type coercion or SKU aggregation (B3, HP-AC04).
4. Small FastAPI Web UI (GET /, POST /api/quotation) displaying the mandatory net course notice and
   forwarding invalid inputs to Python business logic (B4, HP-AC05).
5. Consistent JSON export download (POST /api/quotation/export) matching displayed and calculated
   data 100% with integer cents and rule version HP-V1 (B5, HP-AC06).
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient

from app import app, export_quotation_dict
import quotation.calculator as _calc_mod
from quotation.calculator import (
    COURSE_NOTICE,
    QuotationValidationError,
    calculate_quotation,
)


def build_quotation_export_payload(items_or_quotation):
    fn = getattr(_calc_mod, "build_quotation_export_payload", None)
    if callable(fn):
        return fn(items_or_quotation)
    if isinstance(items_or_quotation, dict) and "lines" in items_or_quotation:
        return dict(items_or_quotation)
    return export_quotation_dict(items_or_quotation)


def export_quotation_json(items_or_quotation):
    fn = getattr(_calc_mod, "export_quotation_json", None)
    if callable(fn):
        return fn(items_or_quotation)
    return json.dumps(build_quotation_export_payload(items_or_quotation), indent=2, ensure_ascii=False)

DATA_DIR = REPO_ROOT / "data"
CATALOGUE_PATH = DATA_DIR / "HansePack_Katalog.json"
REFERENCE_PATH = DATA_DIR / "HansePack_Referenzfaelle.json"

EXPECTED_CATALOGUE_SHA256 = (
    "70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a"
)
EXPECTED_REFERENCE_SHA256 = (
    "7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a"
)

FORBIDDEN_RUNTIME_IMPORTS = (
    "openai",
    "ollama",
    "langchain",
    "langgraph",
    "src.agents",
    "src.llm",
)


def _load_reference_data() -> dict:
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


class TestHansePackSession07FullSuite(unittest.TestCase):
    """Complete Session 7 business, validation, web UI, and JSON export tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.ref_data = _load_reference_data()
        cls.valid_cases = {c["id"]: c for c in cls.ref_data["valid_cases"]}
        cls.invalid_cases = {c["id"]: c for c in cls.ref_data["invalid_cases"]}
        cls.client = TestClient(app)

    def test_01_fixture_provenance_and_zero_factory_dependency(self) -> None:
        """B6, HP-AC01, HP-AC07: Customer fixtures are unchanged and product code has zero LLM/Factory imports."""
        self.assertTrue(CATALOGUE_PATH.is_file())
        self.assertTrue(REFERENCE_PATH.is_file())
        self.assertEqual(
            hashlib.sha256(CATALOGUE_PATH.read_bytes()).hexdigest(),
            EXPECTED_CATALOGUE_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest(),
            EXPECTED_REFERENCE_SHA256,
        )
        self.assertEqual(len(self.valid_cases), 14)
        self.assertEqual(len(self.invalid_cases), 10)

        for rel_py in ("quotation/calculator.py", "main.py", "app.py"):
            py_path = REPO_ROOT / rel_py
            self.assertTrue(py_path.is_file(), f"Missing product file: {rel_py}")
            source = py_path.read_text(encoding="utf-8")
            self.assertNotIn("TODO_FACTORY_GENERATION", source)
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for bad in FORBIDDEN_RUNTIME_IMPORTS:
                            self.assertFalse(
                                alias.name == bad or alias.name.startswith(f"{bad}."),
                                f"Forbidden import {alias.name!r} in {rel_py}",
                            )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    for bad in FORBIDDEN_RUNTIME_IMPORTS:
                        self.assertFalse(
                            node.module == bad or node.module.startswith(f"{bad}."),
                            f"Forbidden import from {node.module!r} in {rel_py}",
                        )

    def test_02_all_valid_cases_q01_to_q14_discounts_and_rounding_hp_v1(self) -> None:
        """B1, HP-AC03: All Q01-Q14 line values, tier boundaries (49/50/99/100), and ROUND_HALF_UP cases (Q04/Q13/Q14)."""
        for case_id in [f"Q{i:02d}" for i in range(1, 15)]:
            with self.subTest(case_id=case_id):
                case = self.valid_cases[case_id]
                result = calculate_quotation(case["input"]["items"])
                exp_v1 = case["expected"]["HP-V1"]
                expected_lines = case["expected_lines"]

                self.assertEqual(
                    result["total_cents"],
                    exp_v1["total_cents"],
                    f"{case_id} total_cents mismatch: got {result['total_cents']}, expected {exp_v1['total_cents']} "
                    f"(goods_net_cents={result['goods_net_cents']} vs {exp_v1['goods_net_cents']})",
                )
                self.assertEqual(len(result["lines"]), len(expected_lines))
                for actual_line, exp_line in zip(result["lines"], expected_lines):
                    for field in (
                        "sku",
                        "quantity",
                        "unit_price_cents",
                        "list_amount_cents",
                        "discount_percent",
                        "discount_cents",
                        "net_cents",
                    ):
                        self.assertIsInstance(
                            actual_line[field],
                            int if field != "sku" else str,
                            f"{case_id} field {field} must be integer cents/qty",
                        )
                        self.assertEqual(
                            actual_line[field],
                            exp_line[field],
                            f"Line mismatch in {case_id} for {field}: got {actual_line[field]}, expected {exp_line[field]}",
                        )

        # Explicit check on commercial half-cent ROUND_HALF_UP cases (Q04, Q13, Q14) and tier boundaries (Q02, Q03, Q05)
        q02 = calculate_quotation(self.valid_cases["Q02"]["input"]["items"])
        self.assertEqual(q02["lines"][0]["discount_percent"], 0)
        self.assertEqual(q02["lines"][0]["discount_cents"], 0)

        q03 = calculate_quotation(self.valid_cases["Q03"]["input"]["items"])
        self.assertEqual(q03["lines"][0]["discount_percent"], 5)
        self.assertEqual(q03["lines"][0]["discount_cents"], 625)
        self.assertEqual(q03["total_cents"], 13075)

        q04 = calculate_quotation(self.valid_cases["Q04"]["input"]["items"])
        self.assertEqual(q04["lines"][0]["discount_cents"], 1238)  # 1237.5 -> 1238

        q05 = calculate_quotation(self.valid_cases["Q05"]["input"]["items"])
        self.assertEqual(q05["lines"][0]["discount_percent"], 10)
        self.assertEqual(q05["lines"][0]["discount_cents"], 2500)

        q13 = calculate_quotation(self.valid_cases["Q13"]["input"]["items"])
        self.assertEqual(q13["lines"][0]["discount_cents"], 3188)  # 3187.5 -> 3188

        q14 = calculate_quotation(self.valid_cases["Q14"]["input"]["items"])
        self.assertEqual(q14["lines"][0]["discount_cents"], 663)   # 662.5 -> 663 (distinguishes HALF_UP from HALF_EVEN 662)

    def test_03_all_valid_cases_q01_to_q14_shipping_and_totals_hp_v1(self) -> None:
        """B2, HP-AC03: All Q01-Q14 goods_net_cents, shipping_cents, and total_cents under HP-V1 (incl. Q06 & Q07)."""
        for case_id in [f"Q{i:02d}" for i in range(1, 15)]:
            with self.subTest(case_id=case_id):
                case = self.valid_cases[case_id]
                result = calculate_quotation(case["input"]["items"])
                exp_v1 = case["expected"]["HP-V1"]

                self.assertEqual(result["currency"], "EUR")
                self.assertEqual(result["rule_version"], "HP-V1")
                self.assertEqual(result["course_notice"], COURSE_NOTICE)
                self.assertEqual(
                    result["goods_net_cents"],
                    exp_v1["goods_net_cents"],
                    f"{case_id} goods_net_cents mismatch",
                )
                self.assertEqual(
                    result["shipping_cents"],
                    exp_v1["shipping_cents"],
                    f"{case_id} shipping_cents mismatch",
                )
                self.assertEqual(
                    result["total_cents"],
                    exp_v1["total_cents"],
                    f"{case_id} total_cents mismatch",
                )

        # Q06: List amount is 50000, but after 10% discount goods_net_cents is 45000 (< 50000) -> shipping = 1200, total = 46200
        q06 = calculate_quotation(self.valid_cases["Q06"]["input"]["items"])
        self.assertEqual(q06["lines"][0]["list_amount_cents"], 50000)
        self.assertEqual(q06["goods_net_cents"], 45000)
        self.assertEqual(q06["shipping_cents"], 1200)
        self.assertEqual(q06["total_cents"], 46200)

        # Q07: At threshold 50000 cents after discount -> free shipping (0 cents), total = 50000
        q07 = calculate_quotation(self.valid_cases["Q07"]["input"]["items"])
        self.assertEqual(q07["goods_net_cents"], 50000)
        self.assertEqual(q07["shipping_cents"], 0)
        self.assertEqual(q07["total_cents"], 50000)

    def test_04_all_invalid_cases_e01_to_e10_rejected_in_python(self) -> None:
        """B3, HP-AC04: All E01-E10 invalid cases raise QuotationValidationError without silent coercion or aggregation."""
        for case_id in [f"E{i:02d}" for i in range(1, 11)]:
            with self.subTest(case_id=case_id):
                case = self.invalid_cases[case_id]
                with self.assertRaises(
                    QuotationValidationError,
                    msg=f"Invalid case {case_id} must raise QuotationValidationError",
                ) as ctx:
                    calculate_quotation(case["input"]["items"])

                self.assertEqual(
                    ctx.exception.reason,
                    case["expected_reason"],
                    f"Reason mismatch for {case_id}: got {ctx.exception.reason!r}, expected {case['expected_reason']!r}",
                )
                self.assertTrue(len(str(ctx.exception).strip()) >= 5)

        # Additional boundary checks: > 3 lines, non-list items, boolean False
        with self.assertRaises(QuotationValidationError) as ctx_lines:
            calculate_quotation(
                [
                    {"sku": "HP-BOX", "quantity": 1},
                    {"sku": "HP-TAPE", "quantity": 1},
                    {"sku": "HP-FILM", "quantity": 1},
                    {"sku": "HP-BOX", "quantity": 2},
                ]
            )
        self.assertEqual(ctx_lines.exception.reason, "too_many_lines")

        with self.assertRaises(QuotationValidationError) as ctx_bool:
            calculate_quotation([{"sku": "HP-BOX", "quantity": False}])
        self.assertEqual(ctx_bool.exception.reason, "quantity_wrong_type")

    def test_05_web_ui_displays_notice_and_validates_in_python_backend(self) -> None:
        """B4, HP-AC05: Web UI renders net notice, calculates multi-line Q12, and forwards E01-E10 to Python."""
        resp_html = self.client.get("/")
        self.assertEqual(resp_html.status_code, 200)
        html_text = resp_html.text
        self.assertIn(COURSE_NOTICE, html_text)
        self.assertIn("HP-BOX", html_text)
        self.assertIn("HP-TAPE", html_text)
        self.assertIn("HP-FILM", html_text)
        # Ensure quantity inputs use type="text" without client-only min="1" lockout
        self.assertNotIn('min="1"', html_text)

        resp_cat = self.client.get("/api/catalogue")
        self.assertEqual(resp_cat.status_code, 200)
        cat_json = resp_cat.json()
        self.assertEqual(len(cat_json["products"]), 3)

        # Multi-line case Q12 via Web API
        q12_case = self.valid_cases["Q12"]
        resp_q12 = self.client.post("/api/quotation", json=q12_case["input"])
        self.assertEqual(resp_q12.status_code, 200)
        q12_data = resp_q12.json()
        self.assertEqual(q12_data["goods_net_cents"], 15875)
        self.assertEqual(q12_data["shipping_cents"], 1200)
        self.assertEqual(q12_data["total_cents"], 17075)
        self.assertEqual(q12_data["course_notice"], COURSE_NOTICE)

        # All E01-E10 invalid inputs sent to POST /api/quotation reach Python and return HTTP 400
        for case_id in [f"E{i:02d}" for i in range(1, 11)]:
            with self.subTest(web_invalid_case=case_id):
                case = self.invalid_cases[case_id]
                resp_err = self.client.post("/api/quotation", json=case["input"])
                self.assertEqual(resp_err.status_code, 400)
                err_body = resp_err.json()
                self.assertIs(err_body["valid"], False)
                self.assertEqual(err_body["reason"], case["expected_reason"])
                self.assertNotIn("total_cents", err_body)

    def test_06_json_export_download_matches_display_and_calculation(self) -> None:
        """B5, HP-AC06: JSON export contains mandatory integer-cent fields and matches calculation & display 100%."""
        for case_id in ("Q01", "Q03", "Q04", "Q06", "Q07", "Q12", "Q13", "Q14"):
            with self.subTest(export_case=case_id):
                case = self.valid_cases[case_id]
                items = case["input"]["items"]

                calc_direct = calculate_quotation(items)
                export_dict = export_quotation_dict(items)
                export_payload = build_quotation_export_payload(calc_direct)
                exported_json_str = export_quotation_json(items)
                self.assertEqual(json.loads(exported_json_str), export_payload)
                resp_display = self.client.post("/api/quotation", json={"items": items})
                resp_export = self.client.post("/api/quotation/export", json={"items": items})

                self.assertEqual(resp_display.status_code, 200)
                self.assertEqual(resp_export.status_code, 200)
                self.assertIn(
                    "hansepack-quotation.json",
                    resp_export.headers.get("content-disposition", ""),
                )

                downloaded_json = json.loads(resp_export.content.decode("utf-8"))
                display_json = resp_display.json()

                # Verify mandatory top-level and line-level fields and integer-cent types match 100%
                self.assertEqual(downloaded_json, export_dict)
                self.assertEqual(display_json, calc_direct)
                for top_key in (
                    "currency",
                    "rule_version",
                    "course_notice",
                    "lines",
                    "goods_net_cents",
                    "shipping_cents",
                    "total_cents",
                ):
                    self.assertIn(top_key, downloaded_json)
                    self.assertEqual(downloaded_json[top_key], calc_direct[top_key])
                    self.assertEqual(downloaded_json[top_key], display_json[top_key])
                self.assertIsInstance(downloaded_json["goods_net_cents"], int)
                self.assertIsInstance(downloaded_json["shipping_cents"], int)
                self.assertIsInstance(downloaded_json["total_cents"], int)

        # Invalid input E01 must also be blocked on JSON export endpoint
        resp_bad_export = self.client.post(
            "/api/quotation/export",
            json=self.invalid_cases["E01"]["input"],
        )
        self.assertEqual(resp_bad_export.status_code, 400)
        self.assertIs(resp_bad_export.json()["valid"], False)


if __name__ == "__main__":
    unittest.main()
