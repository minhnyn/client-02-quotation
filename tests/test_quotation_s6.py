"""Independent automated product tests for HansePack Session 6 (HP-AC01, HP-AC02 Q01/Q03, HP-AC04 E01).

Verifies deterministic calculation and validation against the unchanged customer fixtures
(data/HansePack_Katalog.json and data/HansePack_Referenzfaelle.json) and standalone CLI execution.
Compatible with both `python -m pytest` and `python -m unittest`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quotation.calculator import QuotationValidationError, calculate_quotation

DATA_DIR = REPO_ROOT / "data"
CATALOGUE_PATH = DATA_DIR / "HansePack_Katalog.json"
REFERENCE_PATH = DATA_DIR / "HansePack_Referenzfaelle.json"

EXPECTED_CATALOGUE_SHA256 = (
    "70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a"
)
EXPECTED_REFERENCE_SHA256 = (
    "7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a"
)


def _load_reference_cases() -> dict:
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


def _get_case(section: str, case_id: str) -> dict:
    data = _load_reference_cases()
    for entry in data[section]:
        if entry["id"] == case_id:
            return entry
    raise KeyError(f"Case {case_id!r} not found in {section!r}")


class TestHansePackSession06Quotation(unittest.TestCase):
    """Independent customer acceptance checks for Session 6."""

    def test_fixture_provenance_sha256(self) -> None:
        """Verify customer catalogue and reference cases remain unchanged byte-for-byte."""
        self.assertTrue(CATALOGUE_PATH.is_file())
        self.assertTrue(REFERENCE_PATH.is_file())
        cat_hash = hashlib.sha256(CATALOGUE_PATH.read_bytes()).hexdigest()
        ref_hash = hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest()
        self.assertEqual(cat_hash, EXPECTED_CATALOGUE_SHA256)
        self.assertEqual(ref_hash, EXPECTED_REFERENCE_SHA256)

        calc_text = (REPO_ROOT / "quotation" / "calculator.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("TODO_FACTORY_GENERATION", calc_text)

    def test_q01_hp_box_quantity_1(self) -> None:
        """HP-AC02 (Q01): HP-BOX x 1 -> goods_net=250, shipping=1200, total=1450 cents."""
        case = _get_case("valid_cases", "Q01")
        result = calculate_quotation(case["input"]["items"])

        expected_v1 = case["expected"]["HP-V1"]
        expected_line = case["expected_lines"][0]

        self.assertEqual(result["currency"], expected_v1["currency"])
        self.assertEqual(result["rule_version"], expected_v1["rule_version"])
        self.assertEqual(
            result["course_notice"],
            "Net amounts – course project, not a binding quotation",
        )
        self.assertEqual(len(result["lines"]), 1)
        line = result["lines"][0]
        for field in (
            "sku",
            "quantity",
            "unit_price_cents",
            "list_amount_cents",
            "discount_percent",
            "discount_cents",
            "net_cents",
        ):
            self.assertEqual(line[field], expected_line[field])

        self.assertEqual(result["goods_net_cents"], expected_v1["goods_net_cents"])
        self.assertEqual(result["shipping_cents"], expected_v1["shipping_cents"])
        self.assertEqual(result["total_cents"], expected_v1["total_cents"])

        # Verify standalone CLI agrees for Q01
        proc = subprocess.run(
            [sys.executable, "main.py", "--sku", "HP-BOX", "--quantity", "1"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        cli_data = json.loads(proc.stdout)
        self.assertEqual(cli_data["goods_net_cents"], 250)
        self.assertEqual(cli_data["shipping_cents"], 1200)
        self.assertEqual(cli_data["total_cents"], 1450)

    def test_q03_hp_box_quantity_50_discount(self) -> None:
        """HP-AC02 (Q03): HP-BOX x 50 -> list=12500, discount=625 (5%), goods_net=11875, shipping=1200, total=13075."""
        case = _get_case("valid_cases", "Q03")
        result = calculate_quotation(case["input"]["items"])

        expected_v1 = case["expected"]["HP-V1"]
        expected_line = case["expected_lines"][0]

        self.assertEqual(result["currency"], expected_v1["currency"])
        self.assertEqual(result["rule_version"], expected_v1["rule_version"])
        self.assertEqual(len(result["lines"]), 1)
        line = result["lines"][0]
        for field in (
            "sku",
            "quantity",
            "unit_price_cents",
            "list_amount_cents",
            "discount_percent",
            "discount_cents",
            "net_cents",
        ):
            self.assertEqual(line[field], expected_line[field])

        self.assertEqual(result["goods_net_cents"], expected_v1["goods_net_cents"])
        self.assertEqual(result["shipping_cents"], expected_v1["shipping_cents"])
        self.assertEqual(result["total_cents"], expected_v1["total_cents"])

        # Verify standalone CLI agrees for Q03
        proc = subprocess.run(
            [sys.executable, "main.py", "--sku", "HP-BOX", "--quantity", "50"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        cli_data = json.loads(proc.stdout)
        self.assertEqual(cli_data["lines"][0]["list_amount_cents"], 12500)
        self.assertEqual(cli_data["lines"][0]["discount_cents"], 625)
        self.assertEqual(cli_data["goods_net_cents"], 11875)
        self.assertEqual(cli_data["shipping_cents"], 1200)
        self.assertEqual(cli_data["total_cents"], 13075)

    def test_e01_quantity_zero_rejected_in_business_logic(self) -> None:
        """HP-AC04 (E01): quantity 0 must raise an understandable validation error and produce no valid quotation."""
        case = _get_case("invalid_cases", "E01")
        with self.assertRaises(QuotationValidationError) as ctx:
            calculate_quotation(case["input"]["items"])

        err_msg = str(ctx.exception)
        self.assertTrue(len(err_msg.strip()) > 0)
        self.assertIn("quantity", err_msg.lower())
        self.assertEqual(ctx.exception.reason, case["expected_reason"])

        # Verify standalone CLI rejects E01 clearly with non-zero exit code
        proc = subprocess.run(
            [sys.executable, "main.py", "--sku", "HP-BOX", "--quantity", "0"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")
        err_json = json.loads(proc.stderr)
        self.assertFalse(err_json["valid"])
        self.assertEqual(err_json["reason"], "quantity_out_of_range")


if __name__ == "__main__":
    unittest.main()
