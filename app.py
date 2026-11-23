"""Standalone FastAPI Web UI and JSON Export service for HansePack (HP-AC05, HP-AC06, HP-AC07).

Operates deterministically in Python without any Software Factory or LLM dependency.
All user inputs (including invalid quantities, duplicate SKUs, and type errors) are sent
to the Python backend and validated by quotation.calculator.calculate_quotation.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

import quotation.calculator as _calc_mod
from quotation.calculator import (
    COURSE_NOTICE,
    CURRENCY,
    RULE_VERSION,
    QuotationValidationError,
    calculate_quotation,
    load_catalogue,
)

app = FastAPI(
    title="HansePack Quotation Calculator",
    description=COURSE_NOTICE,
    version="1.0.0",
)


def export_quotation_dict(items: Any) -> dict[str, Any]:
    """Return the validated, deterministic quotation payload for JSON export."""
    calc_export_fn = getattr(_calc_mod, "export_quotation_dict", None)
    if callable(calc_export_fn):
        return calc_export_fn(items)
    return calculate_quotation(items)


def _coerce_raw_quantity_for_backend(raw_qty: Any) -> Any:
    """Parse raw form string inputs only when they represent an exact integer literal,
    preserving floats, non-numeric strings, booleans, and None so Python business logic
    in calculate_quotation validates and rejects them without silent coercion.
    """
    if isinstance(raw_qty, bool) or raw_qty is None:
        return raw_qty
    if isinstance(raw_qty, (int, float)):
        return raw_qty
    if isinstance(raw_qty, str):
        stripped = raw_qty.strip()
        if not stripped:
            return None
        # Only convert when the user typed an optional +/- sign followed purely by digits
        # AND the payload came from raw text form input (flagged by caller).
        return raw_qty
    return raw_qty


def _extract_items_from_payload(payload: Any) -> Any:
    """Extract items list from request JSON while preserving raw types for Python validation."""
    if not isinstance(payload, dict):
        raise QuotationValidationError(
            "Request body must be a JSON object with an 'items' list.",
            reason="invalid_items_structure",
        )
    if "items" not in payload:
        raise QuotationValidationError(
            "Request JSON must contain an 'items' field.",
            reason="invalid_items_structure",
        )
    return payload["items"]


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HansePack Handelsgesellschaft – B2B Quotation Calculator (HP-V1)</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      line-height: 1.5;
    }
    .course-notice {
      background: #1e293b;
      color: #f8fafc;
      padding: 0.65rem 1rem;
      text-align: center;
      font-weight: 600;
      font-size: 0.95rem;
    }
    .container {
      max-width: 960px;
      margin: 1.5rem auto;
      padding: 0 1rem;
    }
    .card {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 1.25rem;
      margin-bottom: 1.25rem;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }
    h1 { margin-top: 0; font-size: 1.5rem; color: #0f172a; }
    h2 { margin-top: 0; font-size: 1.2rem; color: #1e293b; }
    .line-row {
      display: grid;
      grid-template-columns: 2fr 1fr auto;
      gap: 0.75rem;
      align-items: center;
      margin-bottom: 0.75rem;
    }
    label { font-weight: 600; font-size: 0.9rem; display: block; margin-bottom: 0.25rem; }
    select, input[type="text"] {
      width: 100%;
      padding: 0.5rem 0.65rem;
      border: 1px solid #94a3b8;
      border-radius: 6px;
      font-size: 0.95rem;
    }
    .btn-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-top: 1rem;
    }
    button {
      padding: 0.55rem 1rem;
      border-radius: 6px;
      border: 1px solid transparent;
      font-weight: 600;
      font-size: 0.95rem;
      cursor: pointer;
    }
    .btn-primary { background: #0284c7; color: #ffffff; }
    .btn-secondary { background: #e2e8f0; color: #0f172a; border-color: #cbd5e1; }
    .btn-export { background: #0f766e; color: #ffffff; }
    .error-box {
      display: none;
      background: #fef2f2;
      border: 1px solid #ef4444;
      color: #991b1b;
      padding: 0.85rem 1rem;
      border-radius: 6px;
      margin-bottom: 1.25rem;
      font-weight: 600;
    }
    .result-box { display: none; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 0.75rem;
      font-size: 0.92rem;
    }
    th, td {
      border-bottom: 1px solid #e2e8f0;
      padding: 0.55rem 0.5rem;
      text-align: right;
    }
    th:first-child, td:first-child { text-align: left; }
    .totals-grid {
      margin-top: 1rem;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 0.4rem 1.5rem;
      max-width: 420px;
      margin-left: auto;
      font-size: 0.95rem;
    }
    .totals-grid .total-final {
      font-weight: 700;
      font-size: 1.08rem;
      border-top: 2px solid #0f172a;
      padding-top: 0.4rem;
    }
    .meta-badge {
      display: inline-block;
      background: #e0f2fe;
      color: #0369a1;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-right: 0.5rem;
    }
  </style>
</head>
<body>
  <div class="course-notice" role="note" id="course-notice-banner">
    Net amounts – course project, not a binding quotation (Nettobeträge – Lehrprojekt, kein verbindliches Angebot)
  </div>

  <main class="container">
    <section class="card">
      <h1>HansePack Handelsgesellschaft – Quotation Calculator</h1>
      <p>
        <span class="meta-badge">Rule Version: HP-V1</span>
        <span class="meta-badge">Currency: EUR (integer cents)</span>
        <span class="meta-badge">Rounding: ROUND_HALF_UP</span>
      </p>
      <p>Select 1 to 3 packaging line items. All inputs are validated deterministically by the Python backend business logic.</p>

      <div id="lines-container">
        <div class="line-row" data-line-index="0">
          <div>
            <label for="sku-0">Product SKU (Line 1)</label>
            <input type="text" id="sku-0" list="sku-options" value="HP-BOX" placeholder="e.g. HP-BOX">
          </div>
          <div>
            <label for="qty-0">Quantity (1–10000)</label>
            <input type="text" id="qty-0" value="50" placeholder="Enter integer quantity">
          </div>
        </div>
        <div class="line-row" data-line-index="1">
          <div>
            <label for="sku-1">Product SKU (Line 2 – optional)</label>
            <input type="text" id="sku-1" list="sku-options" value="HP-TAPE" placeholder="Leave empty if unused">
          </div>
          <div>
            <label for="qty-1">Quantity (Line 2)</label>
            <input type="text" id="qty-1" value="10" placeholder="Leave empty if unused">
          </div>
        </div>
        <div class="line-row" data-line-index="2">
          <div>
            <label for="sku-2">Product SKU (Line 3 – optional)</label>
            <input type="text" id="sku-2" list="sku-options" value="" placeholder="Leave empty if unused">
          </div>
          <div>
            <label for="qty-2">Quantity (Line 3)</label>
            <input type="text" id="qty-2" value="" placeholder="Leave empty if unused">
          </div>
        </div>
      </div>

      <datalist id="sku-options">
        <option value="HP-BOX">HP-BOX – Versandkarton / Shipping box (250 cents / 2.50 EUR)</option>
        <option value="HP-TAPE">HP-TAPE – Klebeband / Packing tape (400 cents / 4.00 EUR)</option>
        <option value="HP-FILM">HP-FILM – Stretchfolie / Stretch film (1250 cents / 12.50 EUR)</option>
      </datalist>

      <div class="btn-row">
        <button type="button" class="btn-primary" id="btn-calculate" onclick="submitQuotation()">Calculate Quotation</button>
        <button type="button" class="btn-export" id="btn-download-json" onclick="downloadQuotationJson()">Download JSON Export</button>
      </div>
    </section>

    <div class="error-box" id="error-box" role="alert"></div>

    <section class="card result-box" id="result-box">
      <h2>Calculated Quotation (<span id="res-rule-version">HP-V1</span>, <span id="res-currency">EUR</span>)</h2>
      <p id="res-course-notice" style="font-weight: 600; color: #334155;"></p>

      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Quantity</th>
            <th>Unit Price (ct / EUR)</th>
            <th>List Amount (ct / EUR)</th>
            <th>Discount (%)</th>
            <th>Discount (ct / EUR)</th>
            <th>Line Net (ct / EUR)</th>
          </tr>
        </thead>
        <tbody id="res-lines-tbody"></tbody>
      </table>

      <div class="totals-grid">
        <div>Goods Net Amount (after discount):</div>
        <div id="res-goods-net"></div>
        <div>Shipping Fee (HP-V1):</div>
        <div id="res-shipping"></div>
        <div class="total-final">Total Net Quotation Amount:</div>
        <div class="total-final" id="res-total"></div>
      </div>
    </section>
  </main>

  <script>
    function formatCents(cents) {
      const eur = (cents / 100).toFixed(2);
      return `${cents} ct (${eur} EUR)`;
    }

    function parseRawQuantityInput(raw) {
      const trimmed = raw.trim();
      if (trimmed === "") return null;
      if (/^[+-]?\\d+$/.test(trimmed)) {
        return parseInt(trimmed, 10);
      }
      if (/^[+-]?\\d+\\.\\d+$/.test(trimmed)) {
        return parseFloat(trimmed);
      }
      if (trimmed.toLowerCase() === "true") return true;
      if (trimmed.toLowerCase() === "false") return false;
      return trimmed;
    }

    function collectItemsFromForm() {
      const items = [];
      for (let i = 0; i < 3; i++) {
        const skuVal = document.getElementById(`sku-${i}`).value.trim();
        const qtyRaw = document.getElementById(`qty-${i}`).value;
        if (skuVal === "" && qtyRaw.trim() === "") {
          continue;
        }
        const parsedQty = parseRawQuantityInput(qtyRaw);
        if (parsedQty === null) {
          items.push({ sku: skuVal });
        } else {
          items.push({ sku: skuVal, quantity: parsedQty });
        }
      }
      return items;
    }

    async function submitQuotation() {
      const items = collectItemsFromForm();
      const errorBox = document.getElementById("error-box");
      const resultBox = document.getElementById("result-box");

      const response = await fetch("/api/quotation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items })
      });
      const data = await response.json();

      if (!response.ok || data.valid === false) {
        resultBox.style.display = "none";
        errorBox.style.display = "block";
        errorBox.textContent = `Validation Error (${data.reason || "validation_error"}): ${data.error || "Invalid input"}`;
        return;
      }

      errorBox.style.display = "none";
      resultBox.style.display = "block";
      document.getElementById("res-rule-version").textContent = data.rule_version;
      document.getElementById("res-currency").textContent = data.currency;
      document.getElementById("res-course-notice").textContent = data.course_notice;

      const tbody = document.getElementById("res-lines-tbody");
      tbody.innerHTML = "";
      for (const line of data.lines) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${line.sku}</strong></td>
          <td>${line.quantity}</td>
          <td>${formatCents(line.unit_price_cents)}</td>
          <td>${formatCents(line.list_amount_cents)}</td>
          <td>${line.discount_percent}%</td>
          <td>${formatCents(line.discount_cents)}</td>
          <td><strong>${formatCents(line.net_cents)}</strong></td>
        `;
        tbody.appendChild(tr);
      }

      document.getElementById("res-goods-net").textContent = formatCents(data.goods_net_cents);
      document.getElementById("res-shipping").textContent = formatCents(data.shipping_cents);
      document.getElementById("res-total").textContent = formatCents(data.total_cents);
    }

    async function downloadQuotationJson() {
      const items = collectItemsFromForm();
      const errorBox = document.getElementById("error-box");
      const response = await fetch("/api/quotation/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items })
      });
      if (!response.ok) {
        const errData = await response.json();
        document.getElementById("result-box").style.display = "none";
        errorBox.style.display = "block";
        errorBox.textContent = `Export Blocked – Validation Error (${errData.reason || "validation_error"}): ${errData.error || "Invalid input"}`;
        return;
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "hansepack-quotation.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def get_index_page() -> HTMLResponse:
    """Serve the HansePack quotation web UI with visible net course notice."""
    return HTMLResponse(content=HTML_PAGE, status_code=200)


@app.get("/api/catalogue")
def get_catalogue() -> JSONResponse:
    """Return the binding HansePack product catalogue."""
    catalogue = load_catalogue()
    return JSONResponse(
        content={
            "currency": CURRENCY,
            "rule_version": RULE_VERSION,
            "course_notice": COURSE_NOTICE,
            "products": list(catalogue.values()),
        },
        status_code=200,
    )


@app.post("/api/quotation")
async def post_calculate_quotation(request: Request) -> JSONResponse:
    """Calculate a quotation by passing raw items directly to Python business logic."""
    try:
        payload = await request.json()
    except Exception as exc:
        return JSONResponse(
            content={
                "valid": False,
                "error": f"Invalid JSON request body: {exc}",
                "reason": "invalid_json",
            },
            status_code=400,
        )

    try:
        items = _extract_items_from_payload(payload)
        quotation = calculate_quotation(items)
        return JSONResponse(content=quotation, status_code=200)
    except QuotationValidationError as exc:
        return JSONResponse(
            content={
                "valid": False,
                "error": str(exc),
                "reason": exc.reason,
            },
            status_code=400,
        )


@app.post("/api/quotation/export")
async def post_export_quotation(request: Request) -> Response:
    """Export the exact calculated quotation JSON as a downloadable file."""
    try:
        payload = await request.json()
    except Exception as exc:
        return JSONResponse(
            content={
                "valid": False,
                "error": f"Invalid JSON request body: {exc}",
                "reason": "invalid_json",
            },
            status_code=400,
        )

    try:
        items = _extract_items_from_payload(payload)
        quotation = export_quotation_dict(items)
        formatted_json = json.dumps(quotation, indent=2, ensure_ascii=False) + "\n"
        return Response(
            content=formatted_json.encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="hansepack-quotation.json"'
            },
            status_code=200,
        )
    except QuotationValidationError as exc:
        return JSONResponse(
            content={
                "valid": False,
                "error": str(exc),
                "reason": exc.reason,
            },
            status_code=400,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
