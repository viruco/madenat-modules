# -*- coding: utf-8 -*-
# FASE 13/2D — Reproducción del defecto de orden/sugerencia de perfil.
# Solo lectura: el shell de Odoo hace rollback al salir.
import base64
import io

from openpyxl import Workbook
from odoo.tests.common import Form
from odoo.addons.madenat_ingestion_engine.services.document_extractor import (
    extract_document,
)

METRIC_HEADER = ["N°", "CODIGOS", "PRODUCTO", "LOTE", "ESPESOR", "ANCHO",
                 "LARGO", "FILAS", "COLUMNAS", "PIEZAS", "VOLUMEN"]


def to_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


METRIC_ROWS = [
    METRIC_HEADER,
    [1, "0000000000001", "MADERA DE PRUEBA", "LOTE-1", 38.1, 170, 4.05,
     25, 6, 150, 3.8862],
    [2, "0000000000002", "MADERA DE PRUEBA", "LOTE-2", 45, 125, 3.6,
     20, 5, 160, 3.24],
]
EXCEL_BYTES = to_xlsx(METRIC_ROWS)
EXCEL_B64 = base64.b64encode(EXCEL_BYTES).decode()
PDF_B64 = base64.b64encode(b"%PDF-1.4 contenido sintetico").decode()
Wiz = env["madenat.lumber.intake.wizard"]

print("=== 0. Detección del fixture sintético ===")
res = extract_document(EXCEL_BYTES, "packing_metrico.xlsx")
print("detected_profile_code =", res.detected_profile_code, "| lines =", len(res.lines))

# Traza de writes: qué se envía al persistir desde el Form
_orig_write = type(Wiz).write
_writes = []


def _write_logged(self, vals):
    _writes.append(sorted(vals))
    return _orig_write(self, vals)


type(Wiz).write = _write_logged


def dump(tag, form, wiz=None):
    print("%-38s profile=%-8r excel=%-22r pdf=%-12r patio=%r state=%r" % (
        tag,
        form.ingestion_profile,
        form.excel_filename,
        form.pdf_filename,
        form.assignment_location_id.display_name or False,
        (wiz.state if wiz else "-"),
    ))


print("\n=== (a) Primero perfil S2S, después documentos ===")
with Form(Wiz) as form:
    dump("a0 form nuevo", form)
    form.ingestion_profile = "f1550"
    dump("a1 tras elegir S2S", form)
    form.excel_file = EXCEL_B64
    dump("a2 tras subir Excel (binario)", form)
    form.excel_filename = "packing_metrico.xlsx"
    dump("a3 tras fijar nombre Excel", form)
    form.pdf_file = PDF_B64
    dump("a4 tras subir PDF (binario)", form)
    form.pdf_filename = "26070.pdf"
    dump("a5 tras fijar nombre PDF", form)
    wiz_a = form.save()
print("(a) PERSISTIDO profile =", wiz_a.ingestion_profile, "| state =", wiz_a.state)

print("\n=== (b) Primero documentos, después perfil S2S ===")
with Form(Wiz) as form:
    form.excel_filename = "packing_metrico.xlsx"
    form.excel_file = EXCEL_B64
    dump("b1 tras Excel", form)
    form.pdf_filename = "26070.pdf"
    form.pdf_file = PDF_B64
    dump("b2 tras PDF", form)
    form.ingestion_profile = "f1550"
    dump("b3 tras elegir S2S", form)
    wiz_b = form.save()
print("(b) PERSISTIDO profile =", wiz_b.ingestion_profile, "| state =", wiz_b.state)

print("\n=== (c) Elegido S2S y se REEMPLAZA un archivo ya cargado ===")
with Form(wiz_b) as form:
    dump("c0 form sobre (b)", form, wiz_b)
    form.excel_file = EXCEL_B64
    dump("c1 tras reemplazar Excel", form, wiz_b)
    form.pdf_filename = "26070_v2.pdf"
    dump("c2 tras renombrar PDF", form, wiz_b)
    wiz_c = form.save()
print("(c) PERSISTIDO profile =", wiz_c.ingestion_profile)

print("\n=== (d) Modalidad Volúmenes: ¿toca el perfil? ===")
with Form(Wiz) as form:
    dump("d0 form nuevo", form)
    form.ingestion_profile = "f1550"
    form.intake_modality = "volume"
    dump("d1 tras pasar a volume", form)
    form.excel_file = EXCEL_B64
    form.excel_filename = "packing_metrico.xlsx"
    dump("d2 tras subir Excel en volume", form)
    wiz_d = form.save()
print("(d) PERSISTIDO profile =", wiz_d.ingestion_profile,
      "| modalidad =", wiz_d.intake_modality,
      "| tipo =", wiz_d.tipo_ingreso)

print("\n=== (e) ¿La lectura vigente se invalida al cambiar documentos? ===")
wiz_e = Wiz.create({
    "intake_modality": "normal",
    "ingestion_profile": "metric",
    "tipo_ingreso": "producto",
    "state": "previewed",
    "excel_file": EXCEL_B64,
    "excel_filename": "packing_metrico.xlsx",
    "pdf_file": PDF_B64,
    "pdf_filename": "26070.pdf",
    "assignment_location_id": env["stock.location"].search(
        [("usage", "=", "internal")], limit=1).id,
    "preview_line_count": 2,
    "preview_total_volume_m3": 7.1262,
})
_writes.clear()
with Form(wiz_e) as form:
    form.excel_file = EXCEL_B64
    form.excel_filename = "otro_packing.xlsx"
print("(e) state tras cambiar el Excel =", wiz_e.state,
      "| preview_line_count =", wiz_e.preview_line_count,
      "| preview_total_volume_m3 =", wiz_e.preview_total_volume_m3)

print("\n=== (f) Writes observados (claves) ===")
for i, keys in enumerate(_writes, 1):
    print("write#%d -> %s" % (i, keys))

print("\n=== (g) Onchange de modalidad vs patio elegido por el operador ===")
patios = env["stock.location"].search([("usage", "=", "internal")])
print("patios internos: %d" % len(patios))
port_patio, _w = env["stock.location"].resolve_patio_by_type("port")
service_patio, _w2 = env["stock.location"].resolve_patio_by_type("service")
print("auto port   =", port_patio.display_name, port_patio.id)
print("auto service=", service_patio.display_name, service_patio.id)
with Form(Wiz) as form:
    dump("g0 form nuevo", form)
    if service_patio:
        form.assignment_location_id = service_patio
        dump("g1 operador elige patio service", form)
    form.intake_modality = "volume"
    dump("g2 cambia modalidad a volume", form)
    form.intake_modality = "normal"
    dump("g3 vuelve a normal", form)

env.cr.rollback()
print("\nROLLBACK OK — sin cambios en la base")
