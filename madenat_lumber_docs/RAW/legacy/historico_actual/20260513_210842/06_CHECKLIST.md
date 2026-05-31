# MADENAT — Checklist Operativo

**Versión documental:** 4.0.0  
**Fecha de actualización:** 2026-05-13

---

## 1. Inicio de sesión
- [ ] Leer `02_CONTINUIDAD.md`
- [ ] Confirmar task activa del backlog
- [ ] Confirmar BD, rama, contenedores y módulo
- [ ] Verificar si el foco es documentación, bugfix o validación
- [ ] No abrir más de un frente mayor

---

## 2. Restricciones técnicas
- [ ] Odoo 18 CE
- [ ] XML con `<list>`
- [ ] Sin SQL raw
- [ ] Sin fallback silencioso para tipo de cambio
- [ ] Sin writes en Gate 0, 1 y 2
- [ ] `length` debe permanecer en metros como fuente de verdad

---

## 3. Flujo packing
- [ ] Validar recepción física
- [ ] Validar Gate 0
- [ ] Validar Gate 1
- [ ] Validar staging
- [ ] Validar Gate 2
- [ ] Validar cálculo de exportación
- [ ] Validar Gate 3
- [ ] Validar auditoría

---

## 4. Cálculos y unidades
- [ ] Revisar m3 físico
- [ ] Revisar m3 compra
- [ ] Revisar m3 embarque
- [ ] Revisar MBF
- [ ] Revisar tolerancias
- [ ] Revisar naming de largo
- [ ] Revisar conversión `mm/ft/m → length`

---

## 5. Validación del bug actual
- [ ] Buscar `lengthinputraw`
- [ ] Buscar `length_input_raw`
- [ ] Buscar `lengthuom`
- [ ] Buscar `length_uom`
- [ ] Revisar `_compute_lengthm`
- [ ] Confirmar instalación limpia del módulo

---

## 6. Pruebas
- [ ] Registrar caso
- [ ] Ejecutar prueba
- [ ] Guardar evidencia
- [ ] Marcar estado
- [ ] Anotar hallazgos
- [ ] Actualizar continuidad si cambia el estado real

---

## 7. Cierre de sesión
- [ ] Actualizar continuidad
- [ ] Actualizar backlog
- [ ] Actualizar decision log si cambió una regla
- [ ] Dejar próximos 3 pasos
- [ ] Dejar punto exacto de retoma
