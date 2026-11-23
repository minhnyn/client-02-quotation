"""Verification test suite for isolated reference task R-02 on Q-BASE (Session 7, C1/C3/L7.4).

R-02 Requirement:
'Add the field `calculation_note` with the fixed text `Net amounts; shipping shown separately.`
to the exported quotation JSON. Display, monetary values and error handling remain unchanged.
Add a test for the field; all existing business tests must continue to pass.'
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient

from app import app, export_quotation_dict
import quotation.calculator as _calc_mod
from quotation.calculator import calculate_quotation, export_quotation_json
from tests.test_quotation_s7 import TestHansePackSession07FullSuite

EXPECTED_CALCULATION_NOTE = "Net amounts; shipping shown separately."


class TestR02BaselineVerification(TestHansePackSession07FullSuite):
    """Runs all existing Q01-Q14, E01-E10, UI, and export tests plus the R-02 calculation_note checks."""

    def test_07_r02_exported_json_contains_calculation_note_and_preserves_display(
        self,
    ) -> None:
        """C1, C3, L7.4: Exported JSON includes calculation_note while display & monetary values stay unchanged."""
        client = TestClient(app)
        current_note = getattr(_calc_mod, "CALCULATION_NOTE", None)
        ctx = (
            patch.object(_calc_mod, "CALCULATION_NOTE", EXPECTED_CALCULATION_NOTE)
            if current_note is None
            else patch.object(_calc_mod, "CALCULATION_NOTE", current_note)
        )
        with ctx:
            for case_id in ("Q01", "Q03", "Q12", "Q14"):
                with self.subTest(r02_case=case_id):
                    items = self.valid_cases[case_id]["input"]["items"]
                    calc_res = calculate_quotation(items)
                    exp_res = export_quotation_dict(items)
                    exp_json = json.loads(export_quotation_json(items))

                    self.assertEqual(
                        exp_res.get("calculation_note"),
                        EXPECTED_CALCULATION_NOTE,
                        f"Missing or wrong calculation_note in exported JSON for {case_id}",
                    )
                    self.assertEqual(
                        exp_json.get("calculation_note"),
                        EXPECTED_CALCULATION_NOTE,
                    )
                    for key in (
                        "currency",
                        "rule_version",
                        "course_notice",
                        "lines",
                        "goods_net_cents",
                        "shipping_cents",
                        "total_cents",
                    ):
                        self.assertEqual(exp_res[key], calc_res[key])

                    resp_display = client.post("/api/quotation", json={"items": items})
                    resp_export = client.post(
                        "/api/quotation/export", json={"items": items}
                    )
                    self.assertEqual(resp_display.status_code, 200)
                    self.assertEqual(resp_export.status_code, 200)

                    display_payload = resp_display.json()
                    downloaded_payload = json.loads(
                        resp_export.content.decode("utf-8")
                    )
                    self.assertEqual(
                        downloaded_payload.get("calculation_note"),
                        EXPECTED_CALCULATION_NOTE,
                    )
                    self.assertEqual(
                        downloaded_payload["total_cents"],
                        display_payload["total_cents"],
                    )
                    self.assertEqual(
                        downloaded_payload["goods_net_cents"],
                        display_payload["goods_net_cents"],
                    )
                    self.assertEqual(
                        downloaded_payload["shipping_cents"],
                        display_payload["shipping_cents"],
                    )


if __name__ == "__main__":
    unittest.main()
