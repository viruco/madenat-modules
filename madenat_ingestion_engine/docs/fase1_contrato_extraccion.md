# Fase 1 — Diseño del Contrato Real de Extracción

- **Módulo:** `madenat_ingestion_engine`
- **Fecha de la sesión:** 2026-09-01
- **Etapa:** Investigación y diseño de contrato (evidencia). No se implementó `extract_document()`.

> **Declaración explícita:** Este documento es diseño de contrato. **No se implementó `extract_document()` en esta sesión.** No se agregaron campos al modelo `madenat.ingestion.column.profile`; no se modificó ningún `.py`, `.xml`, `.csv` ni `__manifest__.py`.

---

## 0. Archivos de muestra inspeccionados

**Excel (packing, `.xls`)** — 8 archivos (`excel_packing/`):

1. `muestra_excel_01.xls`
2. `muestra_excel_02.xls`
3. `muestra_excel_03.xls`
4. `muestra_excel_04.xls`
5. `muestra_excel_05.xls`
6. `muestra_excel_06.xls`
7. `muestra_excel_07.xls`
8. `muestra_excel_08.xls`

**PDF (guía de despacho DTE SII)** — 9 archivos (`guias_pdf/`):

1. `muestra_pdf_01.pdf`
2. `muestra_pdf_02.pdf`
3. `muestra_pdf_03.pdf`
4. `muestra_pdf_04.pdf`
5. `muestra_pdf_05.pdf`
6. `muestra_pdf_06.pdf`
7. `muestra_pdf_07.pdf`
8. `muestra_pdf_08.pdf`
9. `muestra_pdf_09.pdf`

> Nota: los nombres originales de los archivos de muestra (algunos basados en tamaños de archivo y otros en folios de guía) fueron anonimizados a `muestra_*` para no exponer folios reales. El número de guía real vive dentro del contenido del documento, no en el nombre del archivo.

### Archivos que NO pudieron leerse

Ninguno. Los 8 Excel (formato OLE2 `.xls`) se leyeron con `xlrd`; los 9 PDF se leyeron con `pdfplumber` (extracción de texto, no OCR; son DTE con capa de texto).

---

## 4.1 Cabecera observada en PDFs de guía

Los 9 PDF son **Guías de Despacho electrónicas DTE** con estructura SII estándar. Campos de cabecera observados:

| Etiqueta observada en PDF | Archivo(s) | Variantes de redacción | Campo canónico propuesto |
|---|---|---|---|
| `Nº 00000` (folio de ejemplo) | todas las muestras PDF | `Nº {folio}` (el código también admite `GUÍA DE DESPACHO ELECTRÓNICA Nº:`) | `guide_number` |
| `{comuna}, DD de MM de AAAA (ejemplo)` | todas las muestras PDF | `{comuna}, {día} de {mes} de {año}` | `guide_date` |
| `R.U.T.: XX.XXX.XXX-X` + `Proveedor Ejemplo Ltda.` (emisor) | todas las muestras PDF | `R.U.T.: {rut}` + razón social en líneas contiguas | `supplier_rut`, `supplier_name` |
| `Señor(es): Cliente Ejemplo S.A.` + `R.U.T.: YY.YYY.YYY-Y` (receptor) | todas las muestras PDF | `Señor(es) :{nombre}` / `R.U.T. :{rut}` | `customer_name`, `customer_rut` |
| `Orden: OC-EJEMPLO-001` / `Referencia: en ORDEN DE COMPRA: Nro. OC-EJEMPLO-001 del DD-MM-AAAA (ejemplo)` | todas las muestras PDF | `Orden :{oc}` / `Referencia : en ORDEN DE COMPRA : Nro. {oc}` | `oc_reference` |
| `Transportista: Transportista Ejemplo` / `RUT Transportista: ZZ.ZZZ.ZZZ-Z` | todas las muestras PDF | `Transportista : {nombre}` / `RUT Transportista : {rut}` | `carrier_name`, `carrier_rut` |
| `Patente: AA-BB-11 (ejemplo)` / `Patente Carro: CC-DD-22 (ejemplo)` | todas las muestras PDF | `Patente : ...` / `Patente Carro : ...` | `license_plate` |
| `Neto: $ N.NNN.NNN (ejemplo)` | todas las muestras PDF | `Neto: $ {monto}` | `net_total` |
| `19% I.V.A. $ N.NNN.NNN (ejemplo)` | todas las muestras PDF | `19% I.V.A. $ {monto}` | `tax_total` |
| `Total : $ N.NNN.NNN (ejemplo)` | todas las muestras PDF | `Total : $ {monto}` | `total` |
| `Código U.M Cantidad Descripción Precio Unit. Valor` + línea `{código} M3 {cantidad} ...` | todas las muestras PDF | línea de detalle DTE (no es packing) | `total_volume_m3` (derivado) |
| `Tipo de Cambio` | no visible en el texto muestreado; sí en código (`rate_usd` / `exchange_rate`) | — | `exchange_rate` |

## 4.2 Columnas observadas en Excel de packing

Se identifican **dos formatos de Excel** con el mismo esqueleto de columnas de packing pero unidades distintas:

- **Formato A — métrico "madera seca cepillada"** (`muestra_excel_01.xls` … `muestra_excel_04.xls`, `muestra_excel_06.xls`, `muestra_excel_07.xls`).
- **Formato B — imperial "blanks clear"** (`muestra_excel_05.xls`, `muestra_excel_08.xls`).

La hoja de packing usa **cabecera de dos filas** (nombre + unidad):

| Columna observada en Excel | Archivo(s) | Variantes de redacción | Campo canónico propuesto |
|---|---|---|---|
| `N°` / `PQTE.` (número de paquete) | todos | `N° PQTE.` (dos filas: `N°` + `PQTE.`) | `package_no` |
| `CODIGOS` | todos | `CODIGOS` (plural); valores numéricos 13 díg. (A) o alfanuméricos `A1M...` (B) | `product_code` |
| `PRODUCTO` | todos | `PRODUCTO` | `product_name` |
| `ESPESOR` (sub `mm.`) | todos | `ESPESOR mm.`; valor en **mm** (A) o **pulgadas** (B, p. ej. `1.5625`) | `thickness_mm` (normalizado) |
| `ANCHO` (sub `mm`) | todos | `ANCHO mm`; valor en **mm** (A) o **pulgadas** (B, `3.625`) | `width_mm` (normalizado) |
| `LARGO` (sub `mm`) | todos | `LARGO mm`; valor ambiguo: `4.0` (A, probablemente metros) / `16.0` (B, pies) | `length_m` (normalizado) |
| `FILAS` | todos | `FILAS` | `rows` |
| `COLUMNAS` | todos | `COLUMNAS` | `columns` |
| `PIEZAS` | todos | `PIEZAS` | `pieces` |
| `VOLUMEN` (sub `M3`) | todos | `VOLUMEN M3` | `volume_m3` |
| `M.B.F.` | solo formato A (muestras Excel métricas) | `M.B.F.` | `mbf` |
| (extra, por línea) `{etiqueta destino}` | solo `muestra_excel_08.xls` (formato B) | columna de destino/etiqueta sin cabecera estándar | `destination_label` (pendiente de confirmación) |

**Metadatos de cabecera embebidos en el propio Excel** (no son columnas de línea, pero sí campos de cabecera del contrato):

| Etiqueta observada en Excel | Variantes | Campo canónico propuesto |
|---|---|---|
| `CLIENTE` / `{comuna destino}` | `CLIENTE` (A) / `{comuna destino}` (B, destino) | `customer_name` / `destination` |
| `FECHA` | valor como serial de fecha (p. ej. `NNNNN.0`) | `guide_date` |
| `ORDEN COMPRA` | `OC-EJEMPLO-001`, `OC-EJEMPLO-002` | `oc_reference` |
| `GUIA DESPACHO` | valor como float (`00000.0`) | `guide_number` |
| `DESTINO` | `DESTINO-EJEMPLO` | `destination` |
| `CHOFER` | nombre | `carrier_name` |
| `PATENTE` | `AA-BB-11 (ejemplo)` | `license_plate` |
| `RUT`, `FONO`, `TRANS` (solo formato B) | — | sin uso directo en contrato (pendiente) |

## 4.3 Contraste contra evidencia de código ya confirmada

Fuentes de código confirmadas:

- `madenat_lumber_core/models/reception_parser.py` → `parse_excel` (alias de columnas líneas 224-233, salida líneas 469-486), `parse_dispatch_guide` (salida líneas 663-675).
- `madenat_lumber_core/models/madenat_guia_processing.py` → `_parse_dispatch_pdf` (salida líneas 2403-2418), `_parse_packing_excel` / `_parse_excel_data_core` (mapeo de columnas líneas 2692-2723, salida de línea líneas 2769-2781).

Leyenda de clasificación:

- **COINCIDE** → mismo significado, ya existe en al menos un dominio.
- **VARIANTE** → mismo significado, distinto nombre/formato entre dominios.
- **NUEVO** → no cubierto por ningún dominio actual.
- **SIN EVIDENCIA** → presente en muestras pero sin confirmación de extracción en código.

### Cabecera

| Campo canónico | Recepción (`lumber.reception`) | Guía (`madenat.guia.processing`) | Clasificación |
|---|---|---|---|
| `guide_number` | `guide_no` (parse_dispatch_guide) | `numero_guia` (parse_dispatch_pdf) | VARIANTE (mismo concepto, distinto nombre) |
| `guide_date` | `guide_date` | `fecha_emision` | VARIANTE |
| `supplier_rut` | `supplier_rut` | `rut_emisor` | VARIANTE |
| `supplier_name` | `supplier_name_detected` | `nombre_emisor` | VARIANTE |
| `customer_rut` | — (no extraído) | — (no extraído) | NUEVO |
| `customer_name` | — (no extraído) | — (no extraído) | NUEVO |
| `oc_reference` | `po_ref` | `orden_compra` | VARIANTE |
| `carrier_name` | — (no extraído) | — (no extraído) | NUEVO |
| `carrier_rut` | — (no extraído) | — (no extraído) | NUEVO |
| `license_plate` | — (no extraído) | — (no extraído) | NUEVO |
| `net_total` | `net_total` | `additional_cost` (subtotal neto) | VARIANTE |
| `tax_total` | `iva` (hardcodeado a 0.0) | — (no separado) | SIN EVIDENCIA (parcial) |
| `total` | `total` | — (no retornado) | VARIANTE |
| `exchange_rate` | `exchange_rate` | `rate_usd` | VARIANTE |
| `total_volume_m3` | `total_volume` | `volumen_comercial` | VARIANTE |

### Líneas (packing)

| Campo canónico | Recepción | Guía | Clasificación |
|---|---|---|---|
| `package_no` | `package_no` | `N° LOTE` (mapeo débil: el Excel usa `N° PQTE.`, no `LOTE`) | VARIANTE |
| `product_code` | `product_code` | `Codigo Interno` | VARIANTE |
| `product_name` | `product_name` | `product_name` | COINCIDE |
| `thickness_mm` | `thickness_mm` | `Espesor` (físico) | VARIANTE |
| `width_mm` | `width_mm` | `Ancho` (físico) | VARIANTE |
| `length_m` | `length_m` | `Largo` | VARIANTE |
| `pieces` | `pieces` | `Cantidad` | VARIANTE |
| `volume_m3` | `volume_m3` | `Volumen` | VARIANTE |
| `rows` (FILAS) | — | — | NUEVO |
| `columns` (COLUMNAS) | — | — | NUEVO |
| `mbf` (M.B.F.) | — (deriva a `total_volume_mbf`) | — (deriva a `total_volumen_mbf`) | NUEVO (columna fuente no extraída; el valor se deriva) |

> **Hallazgo clave:** ninguno de los dos parsers extrae hoy `FILAS`, `COLUMNAS` ni la columna `M.B.F.` tal cual viene en el Excel; ambos calculan el MBF a partir del volumen (`/ 2.36`). El contrato propuesto los expone como columnas fuente para no perder información.

## 4.4 Propuesta de contrato (DISEÑO)

```python
# Esqueleto conceptual — NO implementar en esta sesión.
DocumentExtractionResult.header = {
    # Identidad documental
    "guide_number":   str | None,   # Nº guía (normalizado a str, sin ".0")
    "guide_date":     str | None,   # ISO 8601 "YYYY-MM-DD"
    # Emisor / proveedor
    "supplier_rut":   str | None,
    "supplier_name":  str | None,
    # Receptor / cliente
    "customer_rut":   str | None,
    "customer_name":  str | None,
    # Negocio documental
    "oc_reference":   str | None,   # OC/MC normalizada
    "carrier_name":   str | None,
    "carrier_rut":    str | None,
    "license_plate":  str | None,
    # Montos
    "net_total":      float | None,
    "tax_total":      float | None,
    "total":          float | None,
    "exchange_rate":  float | None,
    # Volumen agregado (si la guía lo declara)
    "total_volume_m3": float | None,
}

DocumentExtractionResult.lines = [
    {
        "package_no":   str,          # "1", "2", ... (puede ser derivado)
        "product_code": str,
        "product_name": str,
        "thickness_mm": float | None, # normalizado a mm
        "width_mm":     float | None, # normalizado a mm
        "length_m":     float | None, # normalizado a m
        "rows":         int | None,   # FILAS
        "columns":      int | None,   # COLUMNAS
        "pieces":       int,
        "volume_m3":    float,
        "mbf":          float | None, # M.B.F. (columna fuente)
        "source_units": dict | None,  # unidades originales (auditoría)
    },
]
```

Cada campo, con tipo / obligatoriedad / evidencia / normalización:

| Campo | Tipo | Oblig. | Evidencia | Normalización requerida |
|---|---|---|---|---|
| `guide_number` | texto | opcional | PDF (`Nº`) + Excel (`GUIA DESPACHO`) | quitar `.0` cuando viene como float; unificar `Nº`/`N°`/`Nro.` |
| `guide_date` | fecha (ISO) | opcional | PDF (`{día} de {mes} de {año}`) + Excel (serial) | meses en español; convertir serial Excel → fecha |
| `supplier_rut` | texto | opcional | PDF | normalizar `XX.XXX.XXX-X` (conservar guion) |
| `supplier_name` | texto | opcional | PDF | recortar mayúsculas/espacios |
| `customer_rut` | texto | opcional | PDF (`Señor(es)` + RUT) | ídem supplier_rut |
| `customer_name` | texto | opcional | PDF | ídem |
| `oc_reference` | texto | opcional | PDF (`Orden`/`Referencia`) + Excel (`ORDEN COMPRA`) | `OC-EJEMPLO-001` vs `OC-EJEMPLO-002`; conservar prefijo OC/MC |
| `carrier_name` | texto | opcional | PDF (`Transportista`) + Excel (`CHOFER`) | — |
| `carrier_rut` | texto | opcional | PDF (`RUT Transportista`) | — |
| `license_plate` | texto | opcional | PDF (`Patente`) + Excel (`PATENTE`) | separar patente/carro |
| `net_total` | monto | opcional | PDF | separador de miles `.` y decimal `,` → float |
| `tax_total` | monto | opcional | PDF | ídem |
| `total` | monto | opcional | PDF | ídem |
| `exchange_rate` | número | opcional | PDF/código | — |
| `total_volume_m3` | número | opcional | PDF (línea DTE `Cantidad`) | coma decimal |
| `package_no` | texto | opcional | Excel (`N° PQTE.`) | `1.0` → `1` |
| `product_code` | texto | opcional | Excel (`CODIGOS`) | conservar ceros a la izquierda; mayúsculas para alfanuméricos |
| `product_name` | texto | opcional | Excel (`PRODUCTO`) | mayúsculas/recortar |
| `thickness_mm` | número | opcional | Excel (`ESPESOR`) | **unidad**: mm directo (A) vs pulgadas→mm (B, ×25.4) |
| `width_mm` | número | opcional | Excel (`ANCHO`) | ídem |
| `length_m` | número | opcional | Excel (`LARGO`) | **unidad ambigua**: m (A), pies→m (B, ×0.3048) |
| `rows` | entero | opcional | Excel (`FILAS`) | `25.0` → `25` |
| `columns` | entero | opcional | Excel (`COLUMNAS`) | ídem |
| `pieces` | entero | opcional | Excel (`PIEZAS`) | ídem |
| `volume_m3` | número | recomendado | Excel (`VOLUMEN M3`) | coma decimal |
| `mbf` | número | opcional | Excel (`M.B.F.`) | — |
| `source_units` | dict | opcional | Excel | registrar unidad original detectada (mm/pulg/pies/m) |

## 4.5 Propuesta de perfiles de columna

Base para `madenat.ingestion.column.profile` (diseño; NO crear registros en esta sesión):

| Perfil propuesto | Señal de identificación observada | Archivos que lo representan |
|---|---|---|
| `packing_metrico_aserrada` | Cabecera con `CLIENTE`/`FECHA`/`ORDEN COMPRA`/`GUIA DESPACHO`/`DESTINO`; columnas `ESPESOR(mm)`/`ANCHO(mm)`/`LARGO(mm)` con valores en mm; código numérico de 13 dígitos; columna `M.B.F.` | `muestra_excel_01.xls` … `muestra_excel_04.xls`, `muestra_excel_06.xls`, `muestra_excel_07.xls` |
| `packing_imperial_blanks` | Título `VOLUMEN DE COMPRA` (en vez de `PACKING LIST`); destino `{comuna destino}` (en vez de `CLIENTE`); columnas `ESPESOR`/`ANCHO` en pulgadas (valores `1.5625`, `3.625`) y `LARGO` en pies (`16.0`); código alfanumérico `A1M...`; columnas extra `RUT`/`FONO`/`TRANS` | `muestra_excel_05.xls`, `muestra_excel_08.xls` |

Notas de diseño:

- Los dos perfiles comparten el esqueleto de columnas `N° PQTE. / CODIGOS / PRODUCTO / ESPESOR / ANCHO / LARGO / FILAS / COLUMNAS / PIEZAS / VOLUMEN`; difieren en **unidades** y en **columnas de metadatos**.
- El perfil debe registrar, además del mapeo de columnas, la **unidad de medida** de `ESPESOR`, `ANCHO`, `LARGO` (mm / pulgadas / pies / metros), porque la variación real observada no está en el nombre de columna sino en el valor.
- La cabecera del PDF (guía DTE SII) **no se modela como perfil de columnas**; es un formato de documento de texto con etiquetas fijas (`Nº`, `Señor(es)`, `Orden`, `Transportista`, `Neto`, `Total`). Su extracción es por regex/patrón, no por mapeo de columnas.

---

## Notas finales

- La evidencia confirma que **el contrato debe ser agnóstico de unidad**: los mismos nombres de columna (`ESPESOR`, `ANCHO`, `LARGO`) significan mm vs pulgadas vs pies según el perfil de ingreso.
- El "N° LOTE" referido en el CANON (BT-05 / forward-fill) **no aparece como columna literal** en ninguna muestra; lo que aparece es `N° PQTE.` (número de paquete). El "lote" se deriva (por código o por paquete). Esto debe quedar explícito en la Fase 2.
- **[Actualización — sesión de investigación "N° LOTE", 2026-09-01]** Conclusión: **C** (con matices A y D). En el flujo de Guía de Procesamiento, "N° LOTE" es un identificador **interno** —clave `'N° LOTE'` del dict del parser (línea 2771) → campo `lot_name` de la línea (`lot_name: lote_fisico or code`, línea 1216) → parámetro `lot_name` de `_create_or_get_lot()` (línea 3570)—, no una columna literal del Excel muestreado. `_parse_excel_data_core()` lo deriva con **forward-fill** sobre la variable `curr_lote` (líneas 2726-2749): lee una columna cuyo encabezado contiene "lote" (`col_map['lote']`, línea 2714-2715) y, si no existe tal columna (caso de las 17 muestras, que usan `N° PQTE.`), lo **sintetiza** como `"LOTE-{Código Interno}"`. Por tanto, en las muestras reales "N° LOTE" NO se deriva de "N° PQTE." (el parser de guía no mapea `N°`/`PQTE.`/`paquete`), sino que se genera a partir del código. En Recepción, el concepto equivalente es `package_no`, que SÍ mapea `N°`/`paquete`/`lote` (reception_parser.py líneas 224-233) y elimina filas sin lote explícito (dropna), a diferencia del forward-fill de guía.
- Los montos y RUT citados en este documento son solo de estructura; no se deben usar como datos de producción.

## Fase 1B — Tabla de patrones a adoptar (diseño de reglas)

- **Fecha:** 2026-09-01
- **Alcance:** decisión de diseño patrón-por-patrón, previa a implementar `extract_document()` (Fase 2). No se implementó nada; solo lectura de `reception_parser.py`, `madenat_guia_processing.py`, `lumber_ingestion_format.py`, `ingestion_gate.py` y CANON.

### Veredicto de la hipótesis de trabajo

**CONFIRMADA con una corrección.**

- ✅ La filosofía de **no descartar filas** (forward-fill + síntesis) de `madenat_guia_processing.py` es más adecuada para un motor universal que el `dropna` de `reception_parser.py` (CANON AD-51, `04_DECISION_LOG.md:1149`: el dropna "elimina filas sin lote explícito").
- ✅ `reception_parser.py` aporta arquitectura superior: dispatcher centralizado (`AbstractModel`, líneas 13-15) + formato configurable (`lumber.ingestion.format`, 4 perfiles).
- ⚠️ **Corrección:** la "detección dinámica de columnas" robusta es de **recepción** (scoring de alias, líneas 246-267), no de guía (substring, líneas 2703-2723). Y "menor acoplamiento a `self.env`" es solo **parcial**: ambos usan `self.env` (reception 6 usos; guía en `_validar_y_enriquecer_lineas`).

### Pregunta crítica: ¿el `dropna` es una decisión deliberada?

**PARCIAL.** Es deliberado —hay comentario `# 3. Eliminar filas que quedaron sin lote, piezas o volumen` (`reception_parser.py:318`)—, pero es **silencioso** (no cuenta las filas eliminadas) y **no controlado aguas abajo**: `_log_excel_omissions` (`lumber_reception.py:2960`) es código muerto (sin call-site) y `Gate1DocumentReconciliation` (`ingestion_gate.py:140-165`) no verifica conteo de filas. No es un Gate de calidad.

### Tabla de patrones a adoptar

| # | Patrón | reception_parser | madenat_guia_processing | Adoptar de | Justificación (evidencia) |
|---|---|---|---|---|---|
| P1 | Detección de columnas | scoring alias (238-267) | substring (2703-2723) | **Reception** | scoring tolera más variantes que substring |
| P2 | Configuración de formato/perfil | `lumber.ingestion.format` (32-97, 193-272) | hardcode `col_map` | **Reception** | precedente de `madenat.ingestion.column.profile` |
| P3 | Filas incompletas/vacías | `dropna` (319) + filtro `>0` (322) | forward-fill `curr_lote` (2726-2749) | **Guía** | CANON AD-51: conservar huérfanas |
| P4 | Síntesis de identificador | — | `"LOTE-{code}"` (2748-2749) | **Guía** | evita pérdida de filas sin lote |
| P5 | Reporte de omisiones | `_log_excel_omissions` muerto (2960) | `_register_lot_audit('omission')` vivo (2900-2928) | **Guía** | auditoría viva de líneas descartadas |
| P6 | Manejo de errores | UserError + warnings/fila (324-325, 490-492) | UserError sin cabecera (2700) | **Combinado** | catastrófico→UserError; fila→warnings+auditoría |
| P7 | Arquitectura / `self.env` | dispatcher AbstractModel (13-15); 6 usos `self.env` | disperso en modelo; `self.env` en helpers | **Reception** (dispatcher) + **diseño nuevo** (config por parámetro) | ninguno es puro 100%; Fase 1 exige funciones puras |
| P8 | Detección de formato | `_detect_format` (360-371) | — | **Reception** | distingue métrico vs imperial |
| P9 | Estructura de salida | `{lines, total_volume_m3, mbf, logs, warnings}` (496-502) | `{lineas, ...}` / `{numero_guia, ...}` disperso | **Diseño nuevo** | unificar en `DocumentExtractionResult` (header+lines+warnings) |
| P10 | Múltiples hojas | `sheet_name=0` (188, 211) | `wb.active` / 1ª hoja (2683-2687) | **Ninguno** (ambos 1ª hoja) | declarar política de hojas explícitamente |
| P11 | Librerías | pandas + openpyxl + pdfplumber | pandas/openpyxl + pdfplumber | **Ambos** (coinciden) | ya validado en paridad P7 |

**Fin del documento de diseño (Fase 1 + 1B).**

---

## Corrección post-Fase 2 (2026-09-01)

Los campos `thickness_mm`, `width_mm`, `length_m` del contrato original
se reemplazan por `thickness_value_raw`/`thickness_unit`,
`width_value_raw`/`width_unit`, `length_value_raw`/`length_unit`, para
preservar fielmente la unidad declarada por el proveedor sin conversión
forzada, alineado con AD-51 punto 4 de madenat_lumber_core.

Se confirma que `product_name_original` es un campo de trazabilidad sin
resolución de catálogo, alineado con AD-ING-001/AD-ING-002. La
resolución de product_id/subproducto_id queda diferida a una integración
futura.




