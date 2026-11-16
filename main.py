"""Standalone CLI entry point for the HansePack quotation calculator.

Runs deterministically without any Software Factory or LLM dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from quotation.calculator import QuotationValidationError, calculate_quotation


def _parse_items_argument(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.items_json is not None:
        raw = args.items_json
        candidate_path = Path(raw)
        if candidate_path.is_file():
            raw = candidate_path.read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise QuotationValidationError(
                f"Invalid JSON input for --items-json: {exc}",
                reason="invalid_json",
            ) from exc
        if isinstance(parsed, dict) and "items" in parsed:
            parsed = parsed["items"]
        if not isinstance(parsed, list):
            raise QuotationValidationError(
                "Input items must be a JSON array of {sku, quantity} objects.",
                reason="invalid_items_structure",
            )
        return parsed

    if args.sku is not None and args.quantity is not None:
        return [{"sku": args.sku, "quantity": args.quantity}]

    raise QuotationValidationError(
        "Provide either --sku and --quantity, or --items-json.",
        reason="missing_input",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HansePack quotation calculator (standalone Python runtime, HP-V1)."
    )
    parser.add_argument("--sku", help="Product SKU (e.g. HP-BOX)")
    parser.add_argument(
        "--quantity",
        type=int,
        help="Integer quantity between 1 and 10000",
    )
    parser.add_argument(
        "--items-json",
        help="JSON array string (or path to JSON file) of {sku, quantity} line items",
    )
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=None,
        help="Optional path to HansePack_Katalog.json",
    )
    parser.add_argument(
        "--rule-version",
        default="HP-V1",
        help="Shipping rule version (default: HP-V1)",
    )
    args = parser.parse_args(argv)

    try:
        items = _parse_items_argument(args)
        quotation = calculate_quotation(
            items,
            catalogue_path=args.catalogue,
            rule_version=args.rule_version,
        )
    except QuotationValidationError as exc:
        err_payload = {
            "valid": False,
            "error": str(exc),
            "reason": exc.reason,
        }
        print(json.dumps(err_payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(quotation, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
