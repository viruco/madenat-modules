# Implementación — Identidad Visual de Guías Procesados

## Resumen ejecutivo
Se eliminó la ambigüedad visual en la navegación y selectores de `madenat.guia.processing` mediante `_compute_display_name` enriquecido: `FOLIO · PROVEEDOR · FECHA · TIPO · ID`. El folio documental `name` permanece intacto. **6/6 tests PASS (EXIT=0)** y ejemplos reales demuestran que dos registros con folio 19827 se distinguen por `ID`.

## Problema resuelto
El selector superior mostraba `19827` repetido sin discriminación. Con el nuevo compute, cada registro muestra proveedor, fecha, tipo y `ID <id>` (obligatorio al final).

## Alcance y no alcance
- **Sí:** único `_compute_display_name` en el modelo; tests aislados.
- **No:** no se cambió `name`; no se modificó la constraint `UNIQUE(name, partner_id)`; no se implementó deduplicación; no se tocaron parsers, Intake, stock, OC provisional, costeo ni pagos; sin JavaScript/CSS; sin configurar `_rec_name`/`name_get`.

## Campos técnicos confirmados
| Campo | Línea | Tipo |
|---|---|---|
| `name` | 618 | Char "Número de Guía" (folio documental) |
| `date_emission` | 619 | Date "Fecha de Emisión" (required=True → NOT NULL) |
| `partner_id` | 620 | Many2one res.partner |
| `tipo_recepcion` | 605 | Selection: compra→"Compra de Producto (Aserradero)", service→"Servicio Externo (Cepillado/Procesamiento)" |

Sin overrides previos de `_compute_display_name`/`name_get`/`name_search`/`_rec_name`.

## Diseño de display_name
```python
@api.depends('name', 'partner_id', 'partner_id.name', 'date_emission', 'tipo_recepcion')
def _compute_display_name(self):
    # folio[Sin folio] · proveedor[Sin proveedor] · fecha DD/MM/YYYY[Sin fecha] ·
    # tipo(etiqueta real selection)[Sin tipo] · ID <id>  (siempre al final)
```
- Lectura de la etiqueta de tipo desde `self._fields['tipo_recepcion'].selection` (sin dict duplicado).
- `strftime('%d/%m/%Y')` determinista en tests; sin escritura ni `search()` en el compute.

## Archivos modificados
| Archivo | Cambio |
|---|---|
| `madenat_lumber_core/models/madenat_guia_processing.py` | `_compute_display_name` enriquecido (antes de `do_full_processing`) |
| `madenat_lumber_core/tests/test_guia_processing_display_name.py` (nuevo) | 6 tests |
| `madenat_lumber_core/tests/__init__.py` | Registro del nuevo test |

## Casos de prueba
1. `test_display_name_full_identity` — formato completo exacto.
2. `test_display_name_missing_partner` — fragmento `Sin proveedor`.
3. `test_display_name_missing_date` — fecha formateada DD/MM/YYYY (NOT NULL: caso 'Sin fecha' no persistible; protegido por salvaguarda del compute).
4. `test_display_name_missing_business_fields_keeps_id` — termina en `ID <id>`, sin `False`/`None`/código técnico crudo.
5. `test_display_name_same_folio_is_unique_per_record` — dos folios 19827 se distinguen por el segmento ID final.
6. `test_display_name_does_not_change_document_name` — `name` sigue siendo `19827`.

## Resultados de pruebas
| Suite | Comando | Resultado |
|---|---|---|
| `TestGuiaProcessingDisplayName` | `--test-tags /madenat_lumber_core:TestGuiaProcessingDisplayName --stop-after-init --http-port=8899` | **6/6 PASS — EXIT=0** ("0 failed, 0 error(s) of 6 tests") |

Ejemplos reales (shell readonly con rollback):
```
DISPLAY_G1: 19827 · FERRAMENTA SPA TEST · 02/10/2025 · Servicio Externo (Cepillado/Procesamiento) · ID 625
DISPLAY_G2: 19827 · FERRAMENTA SPA TEST 2 · 02/10/2025 · Servicio Externo (Cepillado/Procesamiento) · ID 626
```
Verificación SELECT final: `SELECT id, name FROM madenat_guia_processing WHERE name='19827';` → `543 | 19827` (1 fila; `name` intacto).

## Validación de compatibilidad
- Selector superior y Many2one hacia `madenat.guia.processing` usan la nueva identidad (via `display_name` estándar).
- El árbol/lista sigue mostrando `name` cuando la vista lo pide; no se reemplaza silenciosamente.
- Búsqueda por `name='19827'` sigue encontrando el registro (no se alteró `name`).
- Constraint `UNIQUE(name, partner_id)` sin cambios; sin columnas nuevas (display_name es computed, no almacenado).
- No se detectaron errores de cache/recompute en la creación de prueba.

## Riesgos residuales
- La corrección **no elimina las reingestas duplicadas**: la constraint `UNIQUE(name, partner_id)` sigue permitiendo folios repetidos con partner NULL. Esa deduplicación documental queda fuera de alcance (documentada en `INVESTIGACION_REPETICION_GUIAS_19827_20260821.md`).
- `date_emission` es NOT NULL: el fallback "Sin fecha" del compute es salvaguarda defensiva, no alcanzable por persistencia normal.

## Veredicto
Implementación correcta y verificada: elimina la ambigüedad visual preservando el folio documental y la constraint existente. Sin deduplicación documental (fuera de alcance por decisión).