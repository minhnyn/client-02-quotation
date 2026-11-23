"""Standalone HansePack UI. All business validation stays in calculator.py."""
import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from quotation.calculator import QuotationValidationError, calculate_quotation

app = FastAPI(title="HansePack quotation", version="HP-V1")

PAGE = r'''<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HansePack Angebotsrechner</title>
<style>
*{box-sizing:border-box}body{font:17px/1.5 system-ui,sans-serif;margin:0;background:#f2f5f7;color:#172d3b}
main{max-width:1050px;margin:auto;padding:28px 20px}h1{line-height:1.15}section,form{background:white;padding:24px;border-radius:12px;margin:20px 0}
.notice{border-left:4px solid #176859;padding:12px;background:#e5f2ee}.line{display:flex;gap:14px;align-items:end;margin:16px 0}.line label{flex:1}
input{display:block;width:100%;padding:10px;border:1px solid #667984;border-radius:5px;font:inherit}
button{font:inherit;cursor:pointer;padding:10px 16px;border:1px solid #176859;border-radius:5px;background:#176859;color:white;margin:4px 0}
button.secondary{background:white;color:#176859}button:disabled{opacity:.5;cursor:default}:focus-visible{outline:3px solid #d57a00;outline-offset:3px}
#error{color:#8c1820;background:#ffeded;padding:12px}table{border-collapse:collapse;width:100%;white-space:nowrap}th,td{text-align:right;padding:10px;border-bottom:1px solid #ccd6dc}th:first-child,td:first-child{text-align:left}
.scroll{overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}dl{display:grid;grid-template-columns:1fr auto;gap:8px}dd{margin:0;font-weight:bold}
[hidden]{display:none!important}@media(max-width:600px){.line{flex-wrap:wrap}.line label{flex-basis:100%}main{padding:15px}section,form{padding:16px}}
</style></head><body><main>
<h1>HansePack Angebotsrechner</h1>
<p class="notice">Net amounts – course project, not a binding quotation</p>
<p>1–3 Positionen · HP-V1 · EUR · Mengen von 1 bis 10000</p>
<form id="quotation-form" novalidate>
<h2>Positionen eingeben</h2>
<p>SKU auswählen oder eingeben. Fehlerhafte Eingaben werden vom Server geprüft.</p>
<datalist id="skus"><option value="HP-BOX">Versandkarton</option><option value="HP-TAPE">Klebeband</option><option value="HP-FILM">Stretchfolie</option></datalist>
<div id="lines"></div>
<button type="button" id="add" class="secondary">Position hinzufügen</button>
<button type="submit" id="calculate">Angebot berechnen</button>
</form>
<p id="error" role="alert" hidden></p>
<section id="result" aria-live="polite" hidden>
<h2>Berechnetes Angebot</h2><p id="metadata"></p>
<div class="scroll" tabindex="0" aria-label="Positionswerte"><table>
<thead><tr><th>SKU</th><th>Menge</th><th>Einzelpreis ct</th><th>Listenwert ct</th><th>Rabatt %</th><th>Rabatt ct</th><th>Netto ct</th></tr></thead><tbody id="values"></tbody></table></div>
<dl><dt>Warenwert nach Rabatt</dt><dd id="goods"></dd><dt>Versand</dt><dd id="shipping"></dd><dt>Gesamtbetrag netto</dt><dd id="total"></dd></dl>
<button type="button" id="export" disabled>JSON herunterladen</button>
<details><summary>Berechnetes JSON anzeigen</summary><pre id="json"></pre></details>
</section>
<noscript>Bitte JavaScript aktivieren, um das Formular und den Download zu verwenden.</noscript>
</main><script>
const form = document.querySelector('#quotation-form');
const lines = document.querySelector('#lines');
const error = document.querySelector('#error');
const result = document.querySelector('#result');
const download = document.querySelector('#export');
let revision = 0, savedInput = null, savedResult = null;
function invalidate(){ revision++; savedInput=null; savedResult=null; result.hidden=true; download.disabled=true; error.hidden=true; }
function addLine(){
  if(lines.children.length>=3)return;
  const row=document.createElement('div');row.className='line';
  row.innerHTML='<label>SKU<input class="sku" list="skus" value="HP-BOX"></label><label>Menge<input class="quantity" type="text" inputmode="decimal" value="1"></label><button class="secondary" type="button">Entfernen</button>';
  row.querySelector('button').onclick=()=>{row.remove();refresh();invalidate();};
  lines.append(row);refresh();invalidate();
}
function refresh(){document.querySelector('#add').disabled=lines.children.length>=3;for(const row of lines.children)row.querySelector('button').disabled=lines.children.length<=1;}
function quantity(raw){
  // Encode integer form entries as JSON numbers; never truncate decimals or parse prefixes.
  if(/^-?(0|[1-9]\d*)$/.test(raw) && Number.isSafeInteger(Number(raw)))return Number(raw);
  if(/^-?(0|[1-9]\d*)\.\d+$/.test(raw) && !Number.isInteger(Number(raw)))return Number(raw);
  return raw;
}
function input(){return {items:[...lines.children].map(row=>({sku:row.querySelector('.sku').value,quantity:quantity(row.querySelector('.quantity').value)}))};}
function showError(message){error.textContent=message;error.hidden=false;}
async function request(url,payload){
  const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const text=await response.text();let data;try{data=JSON.parse(text);}catch{throw new Error('Ungültige Serverantwort. Bitte erneut versuchen.');}
  if(!response.ok)throw new Error(data.error?.message || 'Die Anfrage konnte nicht verarbeitet werden.');
  return {text,data};
}
function money(cents){return `${cents} ct (${(cents/100).toFixed(2)} EUR)`;}
function display(data){
  document.querySelector('#metadata').textContent=`${data.rule_version} · ${data.currency} · Alle Positionsbeträge in Cent`;
  const body=document.querySelector('#values');body.replaceChildren();
  for(const line of data.lines){const row=document.createElement('tr');for(const key of ['sku','quantity','unit_price_cents','list_amount_cents','discount_percent','discount_cents','net_cents']){const cell=document.createElement('td');cell.textContent=line[key];row.append(cell);}body.append(row);}
  for(const [id,key] of [['goods','goods_net_cents'],['shipping','shipping_cents'],['total','total_cents']])document.getElementById(id).textContent=money(data[key]);
  document.querySelector('#json').textContent=JSON.stringify(data,null,2);result.hidden=false;download.disabled=false;
}
form.addEventListener('input',invalidate);
document.querySelector('#add').onclick=addLine;
form.onsubmit=async event=>{event.preventDefault();invalidate();const current=revision,payload=input();try{const response=await request('/api/quotation',payload);if(current!==revision)return;savedInput=payload;savedResult=response.data;display(response.data);}catch(e){if(current===revision)showError(e.message);}};
download.onclick=async()=>{if(!savedInput)return;const current=revision;download.disabled=true;try{const response=await request('/api/quotation/export',savedInput);if(current!==revision)return;if(JSON.stringify(response.data)!==JSON.stringify(savedResult))throw new Error('Das Ergebnis hat sich geändert. Bitte erneut berechnen.');const url=URL.createObjectURL(new Blob([response.text],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='hansepack-quotation.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){if(current===revision)showError(e.message);}finally{if(current===revision)download.disabled=false;}};
addLine();
</script></body></html>'''


@app.get("/", response_class=HTMLResponse)
def homepage():
    return PAGE


async def quotation_response(request: Request, *, export: bool = False):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": {"reason": "invalid_json", "message": "Request body must be valid JSON."}}, status_code=400)
    # No Pydantic coercion: the calculator receives the original JSON types.
    items = payload.get("items") if isinstance(payload, dict) else None
    try:
        quotation = calculate_quotation(items)
    except QuotationValidationError as exc:
        return JSONResponse({"error": {"reason": exc.reason, "message": str(exc)}}, status_code=400)
    headers = {"Cache-Control": "no-store"}
    if export:
        headers["Content-Disposition"] = 'attachment; filename="hansepack-quotation.json"'
    return JSONResponse(quotation, headers=headers)


@app.post("/api/quotation")
async def calculate(request: Request):
    return await quotation_response(request)


@app.post("/api/quotation/export")
async def export(request: Request):
    return await quotation_response(request, export=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
