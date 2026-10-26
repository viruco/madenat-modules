# CHECKLIST DE VERIFICACIÓN MANUAL — BLOQUE 1 (MAURICIO)
**FASE 12 — Requerimientos de Operaciones (Cristhian)**  
**Fecha:** 2026-10-17 | **Estado:** Esperando Verificación Visual de Mauricio en Odoo

---

## Instrucciones para Mauricio
Por favor, ingrese a la instancia local de Odoo (`http://localhost:8069`) con un usuario del grupo **Operaciones** o **Administrador** y verifique los siguientes 5 puntos visuales antes de autorizar el paso al Bloque 2.

---

### [ ] 1. Menú "Ingresos por Volúmenes" (WP-C)
- [ ] Navegar a: `MADENAT Lumber → Operaciones → Abastecimiento → Gestión de Entradas`.
- [ ] Verificar que bajo "Ingreso de Madera" aparece la opción **"Ingresos por Volúmenes"**.
- [ ] Hacer clic en "Ingresos por Volúmenes": debe abrir la consola mostrando por defecto activo el filtro **"Ingresos por Volúmenes"** (solo guías de tipo volumen).

---

### [ ] 2. Búsqueda y Filtros en la Consola (WP-C)
- [ ] En la barra de búsqueda de "Ingresos por Volúmenes" o "Ingreso de Madera":
  - [ ] Escribir el número de una guía (ej. `95806` o `4495589`) y presionar Enter: debe filtrar correctamente por **Guía**.
  - [ ] Escribir un estado (ej. `verified` o `Verificado` o `Borrador`) y seleccionar la opción "Estado": debe filtrar correctamente por **Estado**.
  - [ ] Escribir un nombre de proveedor y filtrar: debe funcionar limpiamente.

---

### [ ] 3. Rótulos en la Vista de Contenedor (WP-B)
- [ ] Navegar a: `MADENAT Lumber → Logística → Contenedores`.
- [ ] **Vista Lista:** Verificar que las columnas de volumen se titulan:
  - [ ] **"Vol. Export (m³)"**
  - [ ] **"Vol. Compra (m³)"**
  - [ ] **"Vol. MBF"**
- [ ] **Vista Formulario (abrir un contenedor):**
  - [ ] En la sección "Volúmenes y Rendimiento", verificar los rótulos: **"Vol. Export (m³)"** y **"Vol. Compra (m³)"**.
  - [ ] En la pestaña **"Lotes Asignados"**, verificar que las columnas para cada etiqueta dicen:
    - [ ] **"Vol. Compra (m³)"** (muestra el volumen de compra por etiqueta).
    - [ ] **"Vol. Export (m³)"** (muestra el volumen comercial de exportación).
    - [ ] Ya NO aparecen los textos confusos "Vol. Físico" ni "Vol. Emb.".

---

### [ ] 4. Rótulos en la Vista de Embarques (WP-B)
- [ ] Navegar a: `MADENAT Lumber → Logística → Embarques de Exportación`.
- [ ] **Vista Lista:** Verificar que la columna de volumen se titula **"Vol. Export (m³)"** (antes decía "m³ Embarque").
- [ ] **Vista Formulario (abrir un embarque):**
  - [ ] En "Totales y KPIs", verificar: **"Vol. Export (m³)"** y **"Vol. Compra (m³)"**.
  - [ ] En la pestaña **"Contenedores"**, verificar columnas: **"Vol. Compra (m³)"** y **"Vol. Export (m³)"**.
  - [ ] En la pestaña **"🔍 Auditoría de Cálculo (Pulgadas)"**, verificar: **"Vol. Compra (m³)"** y **"Vol. Export (m³)"**.
- [ ] **Vista Pivot (Análisis de Embarques):**
  - [ ] Verificar que las medidas se titulan **"Vol. Compra (m³)"** y **"Vol. Export (m³)"**.

---

### [ ] 5. Distinción de Volumen Documental SV (WP-B)
- [ ] Navegar a: `MADENAT Lumber → Logística → Imputaciones documentales SV` (o vista de Etiquetas SV).
- [ ] Verificar que la columna y campo de volumen documental está explícitamente rotulado como **"Vol. Documental (m³)"**.

---

## ⛔ CHECKPOINT
Al finalizar esta revisión, confirme si la verificación visual es satisfactoria para proceder con el **Bloque 2** (WP-F P1–P5, WP-E y WP-G).
