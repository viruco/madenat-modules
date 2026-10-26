# RUNBOOK FASE 12 — Despliegue de Requerimientos de Operaciones (Bloques 1, 2 y 3)

> **Estado:** PREPARADO, **NO ejecutado**. Sin push, sin conexión al remoto, sin despliegue.
> **Origen:** `INFORME_BLOQUE1_WPB_WPC.md` · `INFORME_PRE_BLOQUE3.md`.
> **Alcance del despliegue:**
> - `madenat_lumber_core` (versión **18.0.0.17.0** — WP-B S2S y dimensiones)
> - `madenat_lumber_intake` (versión **18.0.0.17.0** — WP-C e Ingreso / WP-A Conciliación)
> - `madenat_lumber_logistics` (versión **18.0.1.39.0** — WP-B rótulos y WP-F disponibilidad)
> - `madenat_ingestion_engine` (versión **18.0.1.2.0** — WP-E plantilla métrica)
> - Documentación canónica y wiki actualizada.
> **Nada** de `costing` ni del menú de `reports` (11 archivos WIP preservados sin tocar).

---

## 1. Commits a desplegar (rama `feat/guia-correccion-documental-preservada-20261002`)

| Orden | Hash | Contenido | Módulo / Versión |
|:---:|:---:|---|:---:|
| 1 | `55579bd` | WP-C: búsqueda por estado y submenú dedicado «Ingresos por Volúmenes» | `intake` 18.0.0.16.0 |
| 2 | `e189a22` | WP-B rótulos: unificación de «Vol. Compra (m³)», «Vol. Export (m³)» y «Vol. Documental (m³)» | `logistics` 18.0.1.37.0 |
| 3 | `74bf4e8` | Documentación canónica: AD-111 (CANON/04) | — |
| 4 | `967f213` | WP-F P1–P5: control y trazabilidad de disponibilidad en imputación documental SV | `logistics` 18.0.1.38.0 |
| 5 | `b661a44` | WP-E: plantilla estándar `PACKING_METRICO_ASERRADA.xlsx` y guía de llenado | `ingestion` 18.0.1.2.0 |
| 6 | `8ec4ddd` | WP-G: alineación documental, AD-112 canónica y reconciliación D-E0-1 / D-E0-2 | — |
| 7 | `a1ce732` | test: prueba ida y vuelta con datos sintéticos para plantilla PACKING_METRICO_ASERRADA | `ingestion` (test-only) |
| 8 | `2ec4be2` | fix: robustez de notas y acceso a documentos sin disponibilidad en asistente SV | `logistics` 18.0.1.39.0 |
| 9 | `2ba6f4a` | docs: precisión de estado local de Fases 10/11 y formalización de alcance Bloque 3 | — |
| 10 | `036cc9b` | WP-B: tabla canónica S2S en madenat.guia.processing y stock.lot (AD-113) | `core` 18.0.0.17.0 |
| 11 | `c8c8ce6` | WP-A: conciliación guía vs packing con redondeo configurable y estado `ok_rounded` (AD-113) | `intake` 18.0.0.17.0 |
| 12 | `6f6e996` | docs: AD-113 canónica, scripts de simulación y bitácora de decisiones | — |
| 13 | `6822c2a` | fix: compatibilidad de conciliación WP-A con cálculo de guía existente | `intake` (fix) |

---

## 2. Prerrequisitos Críticos del Despliegue

1. **Respaldo previo obligatorio:** Dump de la base de datos destino + `tar` del árbol de código + manifiesto SHA256.
2. **Entorno Python del TEST remoto (`/opt/odoo18-test/venv`):**
   - **Prerrequisito obligatorio:** Verificar que la librería `openpyxl` esté instalada en el venv del TEST remoto:
     ```bash
     /opt/odoo18-test/venv/bin/python -c "import openpyxl; print('openpyxl version:', openpyxl.__version__)"
     ```
   - Si no estuviese instalada, debe incorporarse al venv antes de actualizar `madenat_ingestion_engine`:
     ```bash
     /opt/odoo18-test/venv/bin/pip install openpyxl
     ```
3. **Aislamiento de archivos:** El despliegue debe realizarse desde un commit limpio sin incluir los 11 archivos de WIP de `costing` y `reports`.
4. **Validación de procesos:** Confirmar que no hay instancias de Odoo ejecutando tareas ni pruebas concurrentes en la base de datos destino.

---


### 2.1 Alteración Estructural de Base de Datos (DDL en `madenat_guia_processing`)
> [!IMPORTANT]
> **Modificación de columna en base de datos:** El campo `packing_volume_declared_m3` en el modelo `madenat.guia.processing` (tabla `madenat_guia_processing`) pasa de escala decimal estándar `(16, 3)` a **`(16, 6)`** (`digits=(16, 6)`) para soportar la conciliación de precisión con el packing.
> - Al actualizar `madenat_lumber_intake`, el ORM de Odoo ejecuta automáticamente la sentencia DDL:
>   ```sql
>   ALTER TABLE madenat_guia_processing ALTER COLUMN packing_volume_declared_m3 TYPE numeric(16, 6);
>   ```
> - **Impacto:** Modificación física in-place del tipo de columna. **No recalcula valores almacenados** ni altera los datos preexistentes.

## 3. Procedimiento de Despliegue (LOCAL / REMOTO con autorización expresa)

Actualizar los tres módulos en secuencia controlada, con puerto aislado y sin `-u all`:

```bash
# 1. Actualización de módulos
odoo -d <BD_DESTINO> -u madenat_ingestion_engine,madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics \
  --stop-after-init --http-port=8070 --max-cron-threads=0

# 2. Verificación de regresión dirigida
odoo -d <BD_DESTINO> --test-enable \
  --test-tags=/madenat_ingestion_engine,/madenat_lumber_intake,/madenat_lumber_logistics \
  --stop-after-init --http-port=8070 --max-cron-threads=0
```

**Resultado esperado:**
- `madenat_ingestion_engine`: 0 fallas / 0 errores.
- `madenat_lumber_intake`: 0 fallas / 0 errores.
- `madenat_lumber_logistics`: 4 fallas / 0 errores (exactamente las 4 del baseline).
- **0 fallas nuevas**.

---

## 4. Procedimiento de Rollback

Si ocurriese cualquier anomalía:
1. Detener el servicio Odoo.
2. Restaurar la base de datos desde el dump previo.
3. Restaurar el código a `254e6d3` (HEAD de FASE 11).
4. Reiniciar el servicio y verificar el estado.
