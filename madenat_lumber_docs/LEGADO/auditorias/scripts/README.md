# Scripts de auditoría sueltos (legado) — raíz del stack

**Versión documental:** 1.0.0
**Fecha:** 2026-10-26
**Origen:** consolidación documental FASE 2, etapa E5 (D4).

Estos 11 scripts vivían sueltos en la raíz de `/home/viruco/dev-stack/odoo/odoo-18-ce/` (fuera del
repositorio git). Se copian aquí, versionados, sin modificar su contenido (sha256 verificado contra
`../../FASES/00_MANIFIESTO_CONSOLIDACION_ANTES.csv`, etapa `E5`: 11/11 idénticos).
Los originales **siguen en la raíz** hasta que se autorice su borrado en el punto de control C1.

| Script | Propósito (tomado de su cabecera) |
|---|---|
| `_check_19846.py` | Check 19846 data directamente vía psycopg2 contra la BD de Odoo. |
| `_check_19846.sh` | Envoltorio de shell para el check anterior. |
| `_check_line_number.py` | Localiza `_create_lots_from_packing` en `lumber_reception.py`. |
| `_test_regex.py` | Prueba la regex exacta de `madenat_guia_processing.py` contra muestras. |
| `audit_check.sh` | Auditoría de la columna `lot_reception_date`, salida a `audit_check_output.txt`. |
| `audit_lot_date_v2.py` | Auditoría de `lot_reception_date` v2 (vía subprocess). |
| `audit_run.sh` | Auditoría de XML IDs, salida a `audit_output.txt`. |
| `audit_trazabilidad.sh` | Auditoría de trazabilidad de lotes, salida a `audit_trazabilidad_output.txt`. |
| `run_audit.py` | Ejecuta la auditoría SQL y guarda resultados en `audit_result.txt`. |
| `run_audit_trazabilidad.py` | Auditoría de trazabilidad de lotes (v2.0, sin `lumber_reception_id` legacy). |
| `validate_production.sh` | Validación pre-producción de `madenat_lumber_core`. |

> **Aviso:** estos scripts conservan rutas absolutas `/home/viruco/...` y nombres de archivo de salida
> relativos a la raíz del stack. Se conservan como evidencia histórica; no se han adaptado.

## Excepciones que NO se movieron (decisión E5)

| Script | Motivo |
|---|---|
| `run_tests.sh` | Citado por `CANON/11_FASE_E_VALIDACION.md:542` como «script de CI pipeline unificado» del flujo de validación pre-merge/pre-deploy; moverlo rompería la cita y el hábito de invocación desde la raíz. |
| `deploy_production.sh` | Es el paso de despliegue a producción de `madenat_lumber_core` (junto con `validate_production.sh`); se mantiene en la raíz por ser punto de entrada operativo, no evidencia de auditoría. |
