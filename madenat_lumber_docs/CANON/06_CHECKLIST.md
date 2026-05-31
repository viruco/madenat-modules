# MADENAT — Checklist Operativo Consolidado

**Versión documental:** 4.1.0
**Fecha de actualización:** 2026-05-23
**Estado:** ACTIVO — Guía unificada de sesión, validación y cierre.

---

## 1. Inicio de sesión y Pre-check
- [ ] Leer `02_CONTINUIDAD.md`
- [ ] Confirmar task activa del backlog
- [ ] Confirmar BD, rama, contenedores y módulo
- [ ] Verificar si el foco es documentación, bugfix o validación
- [ ] No abrir más de un frente mayor
- [ ] Confirmar código sincronizado y documentación canónica actualizada

---

## 2. Restricciones técnicas
- [ ] Odoo 18 CE
- [ ] XML con `<list>`
- [ ] Sin SQL raw
- [ ] Sin fallback silencioso para tipo de cambio
- [ ] Sin writes en Gate 0, 1 y 2
- [ ] `length` debe permanecer en metros como fuente de verdad
- [ ] Sin errores de sintaxis o imports que no resuelven
- [ ] Módulo actualiza sin fallar registry (Cero `Wrong @depends`)

---

## 3. Flujo packing y Negocio
- [ ] Validar recepción física y Gate 0 (sin side effects)
- [ ] Validar Gate 1 y staging (sin side effects)
- [ ] Validar Gate 2 (sin side effects)
- [ ] Validar Gate 3 (write único)
- [ ] Validar auditoría y snapshot SHA-256
- [ ] Validar trazabilidad `package_no → lot_name`

---

## 4. Cálculos y unidades
- [ ] Revisar m3 físico, compra, embarque y MBF
- [ ] Revisar tolerancias
- [ ] Revisar naming de largo (lengthinputraw / lengthuom)
- [ ] Revisar conversión `mm/ft/m → length`

---

## 5. Pruebas Mínimas Obligatorias
- [ ] T01–T14 cerradas o revalidadas según contexto
- [ ] T29 ft→m (Evidencia registrada)
- [ ] T30 mm→m validada
- [ ] T31 m→m validada
- [ ] T32 quick-create subproducto validada
- [ ] Actualizar continuidad si cambia el estado real

---

## 6. Criterios de Avance (Gates de Desarrollo)
- **Listo para continuar:** El módulo instala, no falla registry, la documentación está alineada, y el backlog vuelve a priorizar Fase 6.
- **Listo para validar:** T01–T14 siguen firmes, T29–T32 están evidenciadas, y no quedan bugs de naming en computes ni vistas.

---

## 7. Cierre de sesión
- [ ] Actualizar continuidad
- [ ] Actualizar backlog
- [ ] Actualizar decision log si cambió una regla
- [ ] Dejar próximos 3 pasos explícitos
- [ ] Dejar punto exacto de retoma