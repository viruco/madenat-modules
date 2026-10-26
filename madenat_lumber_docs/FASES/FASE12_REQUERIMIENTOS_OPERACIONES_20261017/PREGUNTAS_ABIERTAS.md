# PREGUNTAS ABIERTAS — E2 Compuerta
**FASE 12 — Requerimientos de Operaciones (Cristhian)**  
**Fecha:** 2026-10-17

---

## Para Cristhian (Operaciones)

### R1 — Volúmenes Guía vs Packing

**[CONFIRMAR-A1]** ¿La regla exacta de comparación?
- Propuesta: comparar a 3 decimales. Si `round(vol_guia, 3) == round(vol_packing, 3)` → sin alerta.
- Caso específico: guía trae "57,84" (2 decimales). ¿Es igual a 57,840? ¿O se redondea el packing a 2 decimales?

**[CONFIRMAR-A2]** ¿El packing prevalece siempre como valor operativo, incluso cuando la diferencia es mayor a 3 decimales?

### R3 — Ancho Export

**[CONFIRMAR-B2]** ¿Cuál es la tabla completa de equivalencias ancho nominal → ancho export?
- Solo tenemos confirmado: **150mm = 5 5/8"** (5.625")
- ¿Qué otros anchos maneja MADENAT? (125mm, 100mm, 175mm, 200mm, otros)
- ¿La equivalencia es la misma que el Excel `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`?

**[CONFIRMAR-B3]** Para anchos no estándar (superiores): ¿el operador ingresa el ancho export manualmente en pulgadas decimales, en fracción, o en mm? ¿Quién tiene permiso para hacerlo (Jefatura o Operaciones)?

### R4 — Visibilidad

**[CONFIRMAR-C1]** Guía 95806: el sistema la tiene asociada al proveedor "S.I.I. - LOS ANGELES", no a "JCE". ¿Es correcto? ¿El proveedor real es diferente?

**[CONFIRMAR-C2]** ¿Se prefiere un filtro rápido en la consola existente ("Ingresos por Volúmenes") o una entrada de menú separada?

### R5 — Patios

**[CONFIRMAR-D1]** **Nombres exactos de los patios:**
- El sistema tiene: MARVAL, PUERTO CORONEL, Bodega Tepornac.
- Cristhian menciona "Patio Servicio Cepillado Ferramenta" y "Patio Marval".
- ¿Qué exactamente entra por cada patio? ¿MARVAL es el mismo que "Patio Marval"?
- ¿"Patio Servicio Cepillado Ferramenta" corresponde a "Bodega Tepornac" o a algo nuevo?
- ¿"PUERTO CORONEL" es el mismo que el patio de embarque o es diferente?

**[CONFIRMAR-D4]** ¿La asignación de patio es automática por proveedor (Arauco → Ferramenta, otros → Marval) o manual siempre?

### R6 — Packings

**[CONFIRMAR-E1]** ¿Los datos originales de BYC 95083 están disponibles (Excel de packing)?
Si no, ¿puede Cristhian o Mauricio proveer una muestra del formato?

**[CONFIRMAR-E2]** ¿La plantilla de packing debe ser en formato métrico (mm/m) o también en imperial (pulgadas/pies)?

---

## Para Mauricio (Dirección / Decisiones de negocio)

### IMP02220 — Guía aplicada sin reparto (bloquea D7632/D7642 en SV00000000841)

**[CONFIRMAR-F2]** ¿Qué se hace con IMP02220?
- **Opción A (Excepción histórica):** documentarla como caso especial en el sistema, sin modificarla. D7632 y D7642 quedan bloqueados históricamente.
- **Opción B (Reversa oficial):** crear una reversa con motivo obligatorio, por Jefatura, desbloquear D7632/D7642 y reimputar correctamente.
- **Impacto:** Opción B requiere implementar la reversa y validar que el saldo del SV quede correcto.

### WP-B — Ancho Export (cambio en _compute_vol_shipment_m3)

**[CONFIRMAR-B4]** El cambio en el cálculo del volumen de embarque afectaría **todos los lotes existentes** (recálculo de `vol_shipment_m3`). ¿Se aprueba ese impacto?
¿Se hace en madenat_test primero con validación manual antes de desplegar al TEST remoto?

### WP-D — Patios (política contable)

**[CONFIRMAR-D3]** ¿El área de Contabilidad debe ser consultada antes de crear o renombrar ubicaciones de inventario? ¿Existe valoración de inventario activa (FIFO/AVCO) que generaría asientos al mover stock entre ubicaciones?

**[CONFIRMAR-D2]** ¿Se renombran las ubicaciones existentes (MARVAL, Bodega Tepornac) o se crean nuevas? Si se crean nuevas, ¿qué pasa con los quants y lotes ya asignados a las actuales?

### Aprobación de paquetes

**[CONFIRMAR-ORDEN]** ¿En qué orden se aprueban los paquetes? Propuesta del agente:
1. WP-C → WP-B (rótulos) → WP-A → WP-F (P1–P5) → WP-B (ancho) → WP-D → WP-E → WP-G

### WP-G — Alineación documental

**[CONFIRMAR-G1]** ¿Se actualiza HOJA_RUTA_EJECUTIVA.md y _CAPSULA_CONTEXTO.md ahora (como parte de WP-G) o se espera a que los paquetes estén implementados?

---

## Para Mauricio + Cristhian (Conjunto)

**[CONFIRMAR-DEPLOY]** ¿Cuándo se programa el despliegue al TEST remoto una vez aprobados los primeros paquetes? Recordar que Mauricio lo actualiza manualmente por SSH.

**[CONFIRMAR-CHECKLIST]** ¿Quedan pendientes checklists manuales de FASE 10/11 (VIEW-01/04) por verificar en el navegador antes de pasar a FASE 12?

---

## Resumen de Preguntas por Urgencia

| ID | Para | Urgencia | Bloquea |
|---|---|---|---|
| CONFIRMAR-F2 | Mauricio | 🔴 Alta | WP-F completo; SV00000000841 |
| CONFIRMAR-D1 | Cristhian | 🔴 Alta | WP-D completo |
| CONFIRMAR-B2 | Cristhian | 🟡 Media | WP-B ancho export |
| CONFIRMAR-A1 | Cristhian | 🟡 Media | WP-A |
| CONFIRMAR-C1 | Cristhian | 🟡 Media | visibilidad guía 95806 |
| CONFIRMAR-D3 | Mauricio | 🟡 Media | WP-D (contabilidad) |
| CONFIRMAR-B4 | Mauricio | 🟡 Media | aprobación impacto de recálculo |
| CONFIRMAR-C2 | Cristhian | 🟢 Baja | diseño UX de WP-C |
| CONFIRMAR-E1 | Cristhian | 🟢 Baja | WP-E (BYC) |
| CONFIRMAR-B3 | Cristhian | 🟢 Baja | UX de ancho manual |
