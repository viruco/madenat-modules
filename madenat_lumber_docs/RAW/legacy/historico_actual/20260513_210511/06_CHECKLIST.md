# MADENAT — Checklist Operativo
**Versión:** 3.1.0  
**Fecha:** 2026-04-08

***

## 1. Inicio de sesión
- [ ] Leer el panel de continuidad.
- [ ] Confirmar la task activa del backlog.
- [ ] Confirmar si la arquitectura cambió o sigue congelada.
- [ ] Confirmar ambiente, base de datos, rama y módulo.
- [ ] No abrir más de un frente mayor.

***

## 2. Restricciones técnicas
- [ ] Odoo 18 CE.
- [ ] XML con `<list>`.
- [ ] Sin SQL Raw.
- [ ] Sin fallback `or 1.0` para T/C.
- [ ] Sin writes en Gate 0, 1 y 2.

***

## 3. Flujo packing
- [ ] Validar recepción física.
- [ ] Validar staging / espejo.
- [ ] Validar análisis comercial.
- [ ] Validar exportación.
- [ ] Validar bodega.
- [ ] Validar auditoría.

***

## 4. Cálculos
- [ ] Revisar m3 físico.
- [ ] Revisar m3 compra.
- [ ] Revisar m3 embarque.
- [ ] Revisar MBF.
- [ ] Revisar tolerancias.

***

## 5. Pruebas
- [ ] Registrar caso en tests.
- [ ] Ejecutar prueba.
- [ ] Guardar evidencia.
- [ ] Marcar estado.
- [ ] Anotar hallazgos.

***

## 6. Cierre de sesión
- [ ] Actualizar continuidad.
- [ ] Actualizar backlog.
- [ ] Actualizar decision log si cambió una regla.
- [ ] Definir próximos 3 pasos.
- [ ] Dejar checkpoint de retoma.