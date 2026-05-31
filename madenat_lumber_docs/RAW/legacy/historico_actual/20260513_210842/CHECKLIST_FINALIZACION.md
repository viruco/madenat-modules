# MADENAT — Checklist Final de Cierre / Retoma

**Versión documental:** 6.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — No marcar como listo para producción mientras persista el bug de instalación

---

## 1. Pre-check de ambiente
- [ ] Contenedores activos
- [ ] Base accesible
- [ ] Ruta del módulo correcta
- [ ] Código sincronizado
- [ ] Documentación canónica actualizada

---

## 2. Pre-check técnico
- [ ] Sin errores de sintaxis
- [ ] Imports resuelven
- [ ] Módulo actualiza sin fallar registry
- [ ] Vistas cargan correctamente
- [ ] No hay `Wrong @depends`

---

## 3. Pruebas mínimas obligatorias
- [ ] T01–T14 cerradas o revalidadas según contexto
- [ ] T29 ft→m validada
- [ ] T30 mm→m validada
- [ ] T31 m→m validada
- [ ] T32 quick-create subproducto validada

---

## 4. Validaciones de negocio
- [ ] Gate 0 sin side effects
- [ ] Gate 1 sin side effects
- [ ] Gate 2 sin side effects
- [ ] Gate 3 como write único
- [ ] Trazabilidad `package_no → lot_name`
- [ ] Snapshot SHA-256 consistente

---

## 5. Riesgos que impiden cierre
- [ ] Bug `lengthinputraw` vs `length_input_raw`
- [ ] Constraint costo positivo
- [ ] Warnings XML críticos
- [ ] Fase financiera sin implementar

---

## 6. Criterio de “listo para continuar”
Se puede retomar desarrollo normal cuando:
- el módulo instala,
- no falla registry,
- la documentación está alineada,
- y el backlog vuelve a priorizar Fase 6.

---

## 7. Criterio de “listo para validar”
Se puede declarar listo para validación funcional cuando:
- T01–T14 siguen firmes,
- T29–T32 están evidenciadas,
- y no quedan bugs de naming en computes ni vistas.
