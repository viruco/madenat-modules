# PLAN FASE 12 — E2 Compuerta de Aprobación
**FASE 12 — Requerimientos de Operaciones (Cristhian)**  
**Fecha:** 2026-10-17 | **Agente:** Antigravity  
**⛔ DETENIDO — Requiere aprobación paquete a paquete por Mauricio**

---

## 0. Criterio de Aprobación

Este documento es la **compuerta E2**. No se implementa ningún paquete hasta que Mauricio
apruebe explícitamente, paquete a paquete. La aprobación debe indicar: alcance, archivos
autorizados a modificar, y si hay decisiones previas de Cristhian/Mauricio requeridas.

---

## 1. Prioridades Sugeridas (orden para aprobación)

| Prioridad | Paquete | Requisito | Fundamento |
|---|---|---|---|
| 1 | **WP-C** | R4 | Visibilidad inmediata; costo mínimo; solo UI |
| 2 | **WP-B** (rótulos) | R2 | Solo XML; sin lógica; riesgo mínimo |
| 3 | **WP-A** | R1 | Lógica mínima en Python; bien acotada |
| 4 | **WP-F** (P1–P5) | R7 | Bloquea productividad operativa; requiere confirmación IMP02220 |
| 5 | **WP-B** (ancho export) | R3 | Requiere [CONFIRMAR] tabla completa |
| 6 | **WP-D** | R5 | Requiere [CONFIRMAR] nombres y política contable |
| 7 | **WP-E** | R6 | Entregable no-código (plantilla + guía) |
| 8 | **WP-G** | R8 | Documental; sin riesgo |

---

## 2. Paquete WP-C — Visibilidad de Ingresos por Volúmenes e Inventarios

### Alcance
- Filtro preconfigurado "Ingresos por Volúmenes" en la consola de intake.
- Vista de inventario (stock.lot o stock.quant) agrupada por ubicación.
- Entrada de menú "Ingresos por Volúmenes" (opcional, pendiente de validación de diseño).

### Archivos a tocar
| Archivo | Módulo | Tipo de cambio |
|---|---|---|
| `views/intake_console_views.xml` | `madenat_lumber_intake` | Agregar `<filter>` por `ingestion_type = 'volume'` |
| `views/intake_menus.xml` | `madenat_lumber_intake` | Opcional: nuevo submenú |
| `__manifest__.py` | `madenat_lumber_intake` | Bump de versión |
| Nuevo vista stock.lot/quant por patio | `madenat_lumber_core` o `logistics` | Nueva vista XML |

### Diseño mínimo
```xml
<!-- En intake_console_views.xml, en el search panel -->
<filter string="Ingresos por Volúmenes" name="filter_volume"
        domain="[('ingestion_type', '=', 'volume')]"/>
```

### Pruebas requeridas
- T-C1: Filtro "Ingresos por Volúmenes" muestra guías 4495589 y 95806, excluye recepciones tipo `product`.
- T-C2: Vista de inventario por patio lista quants agrupados por `location_id.complete_name`.
- Regresión: 0 nuevas fallas en suite completa.

### Riesgos
- Bajo. Solo vistas XML; sin lógica de negocio.

### Esfuerzo: **S** (½ día)

### Decisiones requeridas
- [CONFIRMAR-C1] ¿El partner de guía 95806 es correcto (S.I.I.)? ¿O se corrige a "JCE"?
- [CONFIRMAR-C2] ¿Se crea una entrada de menú separada o solo un filtro en la consola existente?

---

## 3. Paquete WP-B — Pantalla de Embarque: Rótulos, Vol. Compra y Ancho Export

### Sub-paquete B1: Rótulos (alcance mínimo, sin lógica)

**Archivos:**
- `lumber_container_views.xml` → cambiar rótulos de columnas Vol. para claridad.
- `lumber_export_shipment_views.xml` → ídem.

**Rótulos propuestos:**
| Campo | Rótulo actual | Rótulo propuesto |
|---|---|---|
| `volume_purchase_m3` (por lote) | "Vol. Físico" | "Vol. Compra (m³)" |
| `vol_shipment_m3` (por lote) | "Vol. Emb." | "Vol. Export (m³)" |
| `total_volume_purchase_m3` | "Vol. Nominal (m³)" | "Vol. Compra Total (m³)" |
| `total_vol_shipment_m3` | "Vol. Exportación (m³)" | "Vol. Export Total (m³)" |

**Esfuerzo: S** (2 horas)

### Sub-paquete B2: Ancho Export — uso de tabla rough→S2S

**Problema confirmado:** `_compute_vol_shipment_m3()` en `stock_lot.py:470` calcula
`a_in = ancho_mm / 25.4 + 0.125` en vez de usar la tabla `lumber.width.s2s.map`.
Para 150mm: da 6.03" en vez de 5.625" (5 5/8").

**Cambio mínimo propuesto en `stock_lot.py`:**
```python
# En _compute_vol_shipment_m3(), reemplazar:
a_in = lot.ancho_mm / MM_PER_INCH
overmeasure = float(get_s2s_adjustment(self.env, lot.ancho_mm))
# Por:
s2s_result = self.env['lumber.width.s2s.map'].search(
    [('rough_mm', '=', round(lot.ancho_mm))], limit=1)
if s2s_result:
    a_in = s2s_result.s2s_decimal
    overmeasure = 0.0
else:
    a_in = lot.ancho_mm / MM_PER_INCH
    overmeasure = float(get_s2s_adjustment(self.env, lot.ancho_mm))
```

**Archivos:** `madenat_lumber_core/models/stock_lot.py`

**Esfuerzo: M** (1 día — requiere TDD y análisis de impacto completo)

**Decisiones requeridas:**
- [CONFIRMAR-B1] ¿Rótulos exactos aprobados por Cristhian?
- [CONFIRMAR-B2] ¿Se aprueba B2 (ancho export)? Requiere tabla completa de equivalencias. Solo 150mm=5 5/8" está confirmado. ¿Qué otros anchos existen?
- [CONFIRMAR-B3] ¿La opción manual (ancho export personalizable) requiere formulario separado o campo editable en el lote?

**Riesgos B2:**
- `_compute_vol_shipment_m3()` afecta todos los embarques existentes. El recálculo podría cambiar volúmenes en lotes ya en embarque → impacto contable. Requiere análisis de M-3 (compute_sudo).
- Los datos de `lumber.width.s2s.map` deben estar sembrados correctamente antes de activar.

---

## 4. Paquete WP-A — Volúmenes Guía vs Packing

### Alcance
- Agregar la lógica de comparación a 3 decimales.
- Nuevo valor `ok_rounded` en `conciliation_status`.
- El packing (`volume_detail_m3`) prevalece como valor operativo.

### Archivos a tocar
| Archivo | Módulo |
|---|---|
| `madenat_lumber_core/models/madenat_guia_processing.py` | Lógica de conciliación |
| `madenat_lumber_core/__manifest__.py` | Bump de versión |

### Diseño mínimo
```python
# En _compute_conciliation_status() (o donde esté la lógica):
diff_3dec = round(official_volume_m3, 3) - round(volume_detail_m3, 3)
if abs(diff_3dec) < 0.001:
    return 'ok_rounded'  # diferencia solo de decimales → sin alerta
```

### Pruebas
- T-A1: Guía 57.8400 vs packing 57.839556 → `ok_rounded`.
- T-A2: Guía 57.84 (2 decimales) vs packing 57.839556 → `ok_rounded` si round(57.84,3)==round(57.839,3).
- T-A3: Diferencia real (>0.001 m³) → sigue siendo `needs_manual_review`.

### Decisiones requeridas
- [CONFIRMAR-A1] ¿La regla exacta cuando la guía trae 2 decimales? ¿57,84 == 57,840?
- [CONFIRMAR-A2] ¿El packing prevalece siempre o solo cuando `ok_rounded`?

**Esfuerzo: S** (½ día con TDD)

---

## 5. Paquete WP-F — Rebaja y Tarjas (P1–P5 + IMP02220)

### Alcance
- P1: Filtrar etiquetas seleccionables a disponibles en el wizard.
- P2: Limitar "Seleccionar todas" a disponibles.
- P3: Sección de solo lectura para no disponibles.
- P4: Resumen coherente.
- P5: Mensaje nominativo de etiquetas bloqueantes.
- IMP02220: presentar opciones, no implementar.

### Archivos a tocar (P1–P5)
| Archivo | Módulo |
|---|---|
| `wizards/madenat_sv_imputation_wizard.py` | `madenat_lumber_logistics` |
| `wizards/madenat_sv_imputation_wizard_views.xml` | `madenat_lumber_logistics` |
| `__manifest__.py` | `madenat_lumber_logistics` |

### Riesgo
- Alto: el wizard de imputación es crítico. Cambios aquí afectan el ciclo de vida de la rebaja (AD-110, I1–I6). Requiere análisis completo de `I2_ACTIVE_STATES` antes de filtrar.

**Esfuerzo: M** (2 días con TDD)

### Decisiones requeridas
- [CONFIRMAR-F1] ¿Se aprueba trabajar en P1–P5 del wizard SV?
- [CONFIRMAR-F2] ¿Qué hace Mauricio con IMP02220? (Opción A: excepción histórica, Opción B: reversa oficial)

---

## 6. Paquete WP-D — Patios

### Alcance
- Crear/renombrar ubicaciones para "Patio Servicio Cepillado Ferramenta" y "Patio Marval".
- Ubicación por defecto según modalidad de ingreso.
- Vistas e informes por patio.

### Archivos a tocar
| Archivo | Módulo |
|---|---|
| `data/<nuevo_patios_data>.xml` | `madenat_lumber_core` (noupdate=True) |
| `madenat_lumber_core/__manifest__.py` | bump versión + nuevo data file |
| Opcional: `models/madenat_guia_processing.py` | lógica de ubicación por modalidad |

**Esfuerzo: M** (1–2 días)

### Decisiones requeridas
- [CONFIRMAR-D1] **Nombres exactos** de los patios (Cristhian debe confirmar).
- [CONFIRMAR-D2] ¿Se renombran las ubicaciones existentes (MARVAL, Bodega Tepornac) o se crean nuevas? ¿Qué pasa con los quants/lotes existentes?
- [CONFIRMAR-D3] ¿Política contable? (con Contabilidad — implicación de valoración de inventario).
- [CONFIRMAR-D4] ¿La ubicación por defecto varía por proveedor, por tipo de guía, o solo por `tipo_recepcion`?

---

## 7. Paquete WP-E — Plantilla de Packing

### Alcance
- Plantilla XLSX de `PACKING_METRICO_ASERRADA` con instrucciones.
- Guía de llenado (documento).
- Pruebas sintéticas.

**Esfuerzo: S** (½ día — no requiere cambio de código)

### Decisiones requeridas
- [CONFIRMAR-E1] ¿BYC 95083 tiene datos originales disponibles? Si no, se necesita que Cristhian los provea.
- [CONFIRMAR-E2] ¿La plantilla debe incluir la opción imperial (Blanks Clear) o solo la métrica?

---

## 8. Paquete WP-G — Alineación Documental

### Alcance
- Actualizar `HOJA_RUTA_EJECUTIVA.md` y `_CAPSULA_CONTEXTO.md` al estado FASE 12.
- Agregar FASE 12 al `CANON/05_BACKLOG.md` y `CANON/04_DECISION_LOG.md` (AD-111 para la primera decisión de FASE 12).
- Runbook de despliegue al TEST.

**Esfuerzo: S** (1 día — solo documentación)

---

## 9. Dependencias entre Paquetes

```
WP-C (filtro) → independiente (puede ir primero)
WP-B (rótulos) → independiente
WP-A → necesita [CONFIRMAR-A1] de Cristhian
WP-B (ancho) → necesita [CONFIRMAR-B2] y análisis M-3
WP-F → necesita [CONFIRMAR-F2] (IMP02220) + aprobación P1–P5
WP-D → necesita [CONFIRMAR-D1/D2/D3] (Cristhian + Contabilidad)
WP-E → puede ir en paralelo con cualquier paquete
WP-G → puede ir en paralelo, preferible al final
```

---

## 10. Resumen de Esfuerzo

| Paquete | Esfuerzo | Riesgo | Requiere CONFIRMAR |
|---|---|---|---|
| WP-C | S | Bajo | C1, C2 |
| WP-B rótulos | S | Mínimo | B1 |
| WP-A | S | Bajo | A1, A2 |
| WP-F P1–P5 | M | Alto | F1, F2 |
| WP-B ancho | M | Medio-Alto | B2, B3 |
| WP-D | M | Medio | D1–D4 |
| WP-E | S | Mínimo | E1, E2 |
| WP-G | S | Mínimo | — |

---

## 11. Checklist de Aprobación por Mauricio

Para cada paquete que Mauricio apruebe, confirmar:
- [ ] Alcance acotado entendido
- [ ] Archivos a tocar autorizados
- [ ] Preguntas [CONFIRMAR] respondidas
- [ ] Decisiones de negocio resueltas (especialmente IMP02220 y patios)
- [ ] Orden de actualización para madenat_test respetado: shipping_core → core → logistics → intake

---

**⛔ AGENTE DETENIDO. En espera de aprobación explícita de Mauricio, paquete a paquete.**
