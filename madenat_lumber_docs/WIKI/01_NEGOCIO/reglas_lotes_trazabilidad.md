# Reglas de Lotes y Trazabilidad

**Módulo:** madenat_lumber_core
**Categoría:** Negocio
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Definir las reglas de negocio que rigen la creación, asignación, movimiento y cierre de lotes de madera en MADENAT.

---

## Contexto

El lote es la unidad central de trazabilidad. Cada lote representa una carga de madera de un proveedor específico, con características propias. El sistema debe poder responder en cualquier momento: ¿dónde está este lote? ¿de dónde vino? ¿a dónde fue?

---

## Reglas vigentes

### Creación
- Todo lote se crea en el momento de recepción.
- El número de lote es único en el sistema.
- El lote hereda proveedor, fecha, especie y dimensión de la recepción.

### Asignación
- Obligatorio en toda recepción de madera.
- Obligatorio en todo despacho.
- Un lote puede dividirse en despachos parciales.

### Movimiento
- Cada movimiento de stock queda registrado en `stock.move.line` con referencia al lote.
- El historial del lote es inmutable una vez validado el movimiento.

### Cierre
- Un lote se cierra cuando su stock disponible llega a cero.
- Lotes cerrados no pueden recibir nuevas asignaciones.

---

## Restricciones conocidas

- No existe transformación de lote: MADENAT no procesa físicamente la madera.
- Los lotes no se fusionan entre sí.
- No se puede modificar el número de lote después de creado.

---

## Evidencia

- Modelo: `stock.lot`, `stock.move`, `stock.move.line`
- Decisión: [[DEC-002_sin_procesamiento_fisico]]

---

## Relacionado

- [[modelo_lotes]]
- [[flujo_recepcion_madera]]
- [[flujo_despacho_embarque]]
- [[00_ARQUITECTURA]]
