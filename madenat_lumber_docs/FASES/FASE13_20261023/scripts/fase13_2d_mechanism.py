# -*- coding: utf-8 -*-
# FASE 13/2D — Validación del MECANISMO del diff (sin aplicar código al módulo).
# Todo ocurre en memoria/monkeypatch; al final se hace rollback explícito.
import base64
import hashlib
import io
from unittest.mock import patch

from openpyxl import Workbook
from odoo.exceptions import UserError
from odoo.tests.common import Form
from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    extract_document,
)

METRIC_HEADER = ["N°", "CODIGOS", "PRODUCTO", "LOTE", "ESPESOR", "ANCHO",
                 "LARGO", "FILAS", "COLUMNAS", "PIEZAS", "VOLUMEN"]
METRIC_ROWS = [
    METRIC_HEADER,
    [1, "0000000000001", "MADERA DE PRUEBA", "LOTE-1", 38.1, 170, 4.05,
     25, 6, 150, 3.8862],
    [2, "0000000000002", "MADERA DE PRUEBA", "LOTE-2", 45, 125, 3.6,
     20, 5, 160, 3.24],
]
wb = Workbook()
ws = wb.active
for row in METRIC_ROWS:
    ws.append(row)
buf = io.BytesIO()
wb.save(buf)
EXCEL_BYTES = buf.getvalue()
EXCEL_B64 = base64.b64encode(EXCEL_BYTES).decode()
PDF_B64 = base64.b64encode(b"%PDF-1.4 contenido sintetico").decode()

# Variante con otro contenido (reemplazo real de archivo) para E2.
wb2 = Workbook()
ws2 = wb2.active
for row in [METRIC_HEADER,
            [1, "0000000000003", "MADERA DE PRUEBA", "LOTE-9", 50, 150, 3.2,
             10, 4, 120, 2.88]]:
    ws2.append(row)
buf2 = io.BytesIO()
wb2.save(buf2)
EXCEL_BYTES_V2 = buf2.getvalue()
EXCEL_B64_V2 = base64.b64encode(EXCEL_BYTES_V2).decode()

Wiz = env["madenat.lumber.intake.wizard"]
Reception = env["lumber.reception"]
Patio = env["stock.location"].search([("usage", "=", "internal")], limit=1)
print("patio usado:", Patio.display_name, Patio.id)
print("fixture:", extract_document(EXCEL_BYTES, "packing_metrico.xlsx")
      .detected_profile_code)


def base_vals(**extra):
    vals = {
        "intake_modality": "normal",
        "tipo_ingreso": "producto",
        "ingestion_profile": "metric",
        "excel_file": EXCEL_B64,
        "excel_filename": "packing_metrico.xlsx",
        "pdf_file": PDF_B64,
        "pdf_filename": "26070.pdf",
        "assignment_location_id": Patio.id,
    }
    vals.update(extra)
    return vals


def new_previewed(**extra):
    vals = base_vals(state="previewed", preview_line_count=2,
                     preview_total_volume_m3=7.1262, preview_guide_no="26070")
    vals.update(extra)
    return Wiz.create(vals)


# ─────────────────────────────────────────────────────────────────────────
# E1 — ¿El onchange de sugerencia RE-ENTRA en los onchange de ingestion_profile?
# ─────────────────────────────────────────────────────────────────────────
print("\n=== E1 — bucle recursivo de onchange (servidor) ===")
spec = Wiz.get_views([(False, "form")])["models"][Wiz._name]["fields"]
calls = []


def _marker_onchange(self):
    calls.append(self.ingestion_profile)


Wiz._onchange_methods.setdefault("ingestion_profile", []).append(_marker_onchange)
vals = base_vals(ingestion_profile="f1550")     # el operador eligió S2S
res = Wiz.onchange(vals, ["excel_file"], spec)["value"]
print("E1a el operador eligió f1550 y sube el Excel -> resultado:",
      res.get("ingestion_profile"))
print("    onchange(ingestion_profile) re-entró con:", calls)
calls.clear()

# E1b — misma detección, pero con la guarda de procedencia (emulada con un
# campo existente: tipo_ingreso_auto_detectado == 'elegido por el operador').
_registered = Wiz._onchange_methods["excel_file"]
_real_suggest = [m for m in _registered
                 if m.__name__ == "_onchange_suggest_ingestion_profile"]


def _guarded_suggest(self):
    for rec in self:
        if rec.intake_modality == "volume" or not rec.excel_file:
            continue
        detected = extract_document(
            base64.b64decode(rec.excel_file),
            rec.excel_filename or "packing.xlsx").detected_profile_code
        suggested = "metric" if detected == "packing_metrico_aserrada" else None
        if not suggested:
            continue
        chosen = rec.tipo_detalle_granel == "linea_por_linea"   # 'chosen' emulado
        if not chosen:
            rec.ingestion_profile = suggested


Wiz._onchange_methods["excel_file"] = [
    m for m in _registered if m.__name__ != "_onchange_suggest_ingestion_profile"
] + [_guarded_suggest]
for chosen in (False, True):
    out = Wiz.onchange(
        base_vals(ingestion_profile="f1550",
                  tipo_detalle_granel="linea_por_linea" if chosen
                  else "agregado"),
        ["excel_file"], spec)["value"]
    print("E1b procedencia 'chosen'=%s -> ingestion_profile = %r"
          % (chosen, out.get("ingestion_profile")))
    calls.clear()
Wiz._onchange_methods["excel_file"] = _registered
Wiz._onchange_methods["ingestion_profile"].remove(_marker_onchange)


# ─────────────────────────────────────────────────────────────────────────
# E2 — Lectura vieja: ¿se puede derivar hoy? y ¿lo detecta una huella md5?
# ─────────────────────────────────────────────────────────────────────────
print("\n=== E2 — lectura vieja: ruta actual vs huella ===")


def signature(wiz):
    h = hashlib.md5()
    for part in (wiz.intake_modality, wiz.ingestion_profile,
                 wiz.assignment_location_id.id, wiz.tipo_detalle_granel,
                 wiz.excel_filename or "", wiz.pdf_filename or "",
                 wiz.excel_file or "", wiz.pdf_file or ""):
        h.update(str(part).encode("utf-8"))
    return h.hexdigest()


sigs = {}
wiz_a = new_previewed()
sigs[wiz_a.id] = signature(wiz_a)          # se sella al leer
before = Reception.search_count([])
wiz_a.write({"excel_file": EXCEL_B64_V2,
             "excel_filename": "packing_REEMPLAZADO.xlsx"})   # sin onchange
print("state tras reemplazar el archivo:", wiz_a.state,
      "| huella cambió:", sigs[wiz_a.id] != signature(wiz_a))
with patch.object(type(Reception), "action_process_documents", return_value=True):
    try:
        wiz_a.action_route_document()
        print("RUTA PERMITIDA con lectura vieja. receptiones creadas:",
              Reception.search_count([]) - before)
    except UserError as error:
        print("RUTA BLOQUEADA:", error)

wiz_l = new_previewed()
wiz_l_sign = signature(wiz_l)
wiz_l.write({"pdf_filename": "26070_v2.pdf"})     # sólo el nombre
print("sólo cambia el nombre del PDF -> huella cambió:",
      wiz_l_sign != signature(wiz_l))

orig_guard = type(Wiz)._guard_route_document


def guard_with_signature(self):
    orig_guard(self)
    if self.state == "previewed" and sigs.get(self.id) \
            and sigs[self.id] != signature(self):
        raise UserError("Los datos cambiaron después de leer el documento. "
                        "Vuelva a leer antes de continuar.")


type(Wiz)._guard_route_document = guard_with_signature
wiz_b = new_previewed()
sigs[wiz_b.id] = signature(wiz_b)
wiz_b.write({"excel_filename": "packing_REEMPLAZADO_2.xlsx"})
before = Reception.search_count([])
with patch.object(type(Reception), "action_process_documents", return_value=True):
    try:
        wiz_b.action_route_document()
        print("ERROR: la ruta NO se bloqueó con huella distinta")
    except UserError as error:
        print("CON GUARDA -> BLOQUEADO:", error)
print("receptiones creadas con guarda:", Reception.search_count([]) - before)

with patch.object(type(Reception), "action_process_documents", return_value=True):
    wiz_c = new_previewed()
    sigs[wiz_c.id] = signature(wiz_c)
    wiz_c.action_route_document()
    print("lectura vigente -> ruta permitida, state =", wiz_c.state,
          "| target =", wiz_c.target_res_id)
type(Wiz)._guard_route_document = orig_guard

# ─────────────────────────────────────────────────────────────────────────
# E3 — Invalidez sólo por onchange: ¿persiste un campo readonly (state)?
# ─────────────────────────────────────────────────────────────────────────
print("\n=== E3 — onchange que pone state='draft' en un campo readonly ===")


def _invalidate_onchange(self):
    for rec in self:
        if rec.state == "previewed":
            rec.state = "draft"
            rec.preview_line_count = 0


Wiz._onchange_methods.setdefault("excel_filename", []).append(
    _invalidate_onchange)
wiz_d = new_previewed()
with Form(wiz_d) as form:
    form.excel_filename = "packing_D.xlsx"
    print("en el Form: state =", form.state,
          "| preview_line_count =", form.preview_line_count)
wiz_d.invalidate_recordset()
print("PERSISTIDO tras Form.save implícito: state =", wiz_d.state,
      "| preview_line_count =", wiz_d.preview_line_count)
Wiz._onchange_methods["excel_filename"].remove(_invalidate_onchange)

# ─────────────────────────────────────────────────────────────────────────
# E4 — Invalidación en write(): verdad de servidor (cubre RPC y Form)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== E4 — invalidación a nivel de write() ===")
SENSITIVE = {"intake_modality", "excel_file", "excel_filename", "pdf_file",
             "pdf_filename", "ingestion_profile", "assignment_location_id"}
CLEAR = {
    "state": "draft", "preview_data": False, "preview_line_count": 0,
    "preview_total_volume_m3": 0.0, "preview_guide_no": False,
    "preview_warnings": False, "preview_has_detail": False,
    "preview_document_lines": False, "preview_line_volume_m3": 0.0,
    "preview_guide_date": False, "preview_supplier": False, "preview_oc": False,
    "preview_origin": False, "preview_exchange_rate": 0.0,
    "preview_total_packages": 0, "detalle_aplicado": False,
    "detalle_motivo": False, "reading_warning": False,
    "has_reading_warning": False, "profile_warning_message": False,
    "confirm_profile_mismatch": False, "error_message": False,
}
orig_write = type(Wiz).write


def write_invalidating(self, vals):
    stale = False
    for rec in self.filtered(lambda r: r.state == "previewed"):
        for key in SENSITIVE.intersection(vals):
            current = rec[key]
            current = current.id if hasattr(current, "id") else current
            if vals[key] != current:
                stale = True
                break
    if stale:
        merged = dict(vals)
        for key, value in CLEAR.items():
            merged.setdefault(key, value)
        vals = merged
    return orig_write(self, vals)


type(Wiz).write = write_invalidating
wiz_e = new_previewed()
wiz_e.write({"excel_filename": "packing_E.xlsx"})
print("write directo -> state =", wiz_e.state,
      "| preview_line_count =", wiz_e.preview_line_count,
      "| archivos conservados:", bool(wiz_e.excel_file), bool(wiz_e.pdf_file))

wiz_e2 = new_previewed()
wiz_e2.write({"excel_file": wiz_e2.excel_file,
              "excel_filename": wiz_e2.excel_filename})
print("re-guardar el MISMO archivo -> state =", wiz_e2.state,
      "(no se invalida por ruido del cliente)")

wiz_f = new_previewed()
with Form(wiz_f) as form:
    form.excel_filename = "packing_F.xlsx"
    form.save()
wiz_f.invalidate_recordset()
print("Form.save() -> state =", wiz_f.state,
      "| preview_line_count =", wiz_f.preview_line_count)

wiz_g = new_previewed()
with patch.object(type(Reception), "action_process_documents", return_value=True):
    wiz_g.write({"excel_filename": "packing_G.xlsx"})
    try:
        wiz_g.action_route_document()
        print("ERROR: derivó con lectura invalidada")
    except UserError as error:
        print("tras invalidar -> BLOQUEADO:", error)

wiz_h = Wiz.create(base_vals(state="draft"))
wiz_h.action_preview_document()
print("preview normal -> state =", wiz_h.state,
      "| líneas =", wiz_h.preview_line_count)
wiz_i = Wiz.create(base_vals(state="draft", intake_modality="volume"))
wiz_i.action_preview_document()
print("preview volume -> state =", wiz_i.state)
type(Wiz).write = orig_write

# ─────────────────────────────────────────────────────────────────────────
# E5 — Procesado: ¿'Leer documento' deja state='previewed'? (hueco del diff)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== E5 — Procesado tras Leer documento ===")
outcome = {"tipo": "procesado", "analyzed": [], "advisory": False}
with patch.object(type(Wiz), "_classify_normal_document",
                  return_value=outcome):
    wiz_j = Wiz.create(base_vals(state="draft", tipo_ingreso="procesado"))
    wiz_j.action_preview_document()
    print("procesado -> state =", wiz_j.state,
          "| tipo_ingreso =", wiz_j.tipo_ingreso)
    try:
        wiz_j._guard_route_document()
        print("guarda de ruta para procesado en state='draft': NO BLOQUEA")
    except UserError as error:
        print("guarda de ruta para procesado: BLOQUEA ->", error)

wiz_k = Wiz.create(base_vals(state="draft", intake_modality="volume",
                            tipo_ingreso="granel"))
try:
    wiz_k._guard_route_document()
    print("guarda de ruta para volume en state='draft': NO BLOQUEA")
except UserError as error:
    print("guarda de ruta para volume: BLOQUEA ->", error)

env.cr.rollback()
print("\nROLLBACK OK — base sin cambios")

