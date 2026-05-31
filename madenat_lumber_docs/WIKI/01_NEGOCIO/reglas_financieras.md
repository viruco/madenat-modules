# Reglas Financieras de MADENAT

**Módulo:** madenat_lumber_core / account
**Categoría:** Negocio
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Definir los gates y restricciones financieras del sistema para garantizar consistencia entre inventario, compras y contabilidad.

---

## Reglas vigentes

### Gate de facturación
- Ninguna factura de proveedor puede ser confirmada sin una OC validada asociada.
- El valor de la factura no puede superar el valor total de la OC en más de un 5% sin aprobación del administrador.

### Valorización de inventario
- MADENAT usa método de valorización FIFO para el inventario de madera.
- El costo unitario se toma del precio de la OC confirmada.

### Reportes financieros
- Los reportes de rentabilidad por lote comparan costo de recepción vs precio de venta del despacho.
- (documentación de reportes pendiente)

### Cierre de período
- No se puede modificar una recepción o despacho cuyo período contable esté cerrado.
- Intentar hacerlo genera error de Odoo nativo.

---

## Restricciones conocidas

- La localización chilena de Odoo 18 CE puede generar conflictos con los asientos automáticos. Verificar en cada actualización de módulo.
- Los reportes de rentabilidad son custom y no usan el módulo de analítica nativo de Odoo.

---

## Relacionado

- [[00_ARQUITECTURA]]
- [[04_DECISION_LOG]]
