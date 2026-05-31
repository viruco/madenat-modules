# Actores y Roles en MADENAT

**Módulo:** madenat_lumber_core
**Categoría:** Negocio
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Definir los actores del sistema, sus responsabilidades y sus niveles de acceso en Odoo.

---

## Actores

### Proveedor (Aserradero)
- Entidad externa. No tiene acceso al sistema.
- Genera la madera que llega en recepciones.
- Referenciado como `res.partner` con tag de proveedor.

### Operador de Bodega
- Registra recepciones físicas.
- Asigna lotes a las entradas.
- Confirma despachos con guía generada.
- **Grupo Odoo:** `stock.group_stock_user`

### Despachador / Transportista
- Entidad externa o interna.
- Referenciado en la guía de despacho.
- No tiene acceso directo al sistema.

### Administrador MADENAT
- Acceso completo al módulo.
- Responsable de configuración, auditoría y reportes.
- **Grupo Odoo:** `base.group_system` + grupos propios MADENAT

### Contador / Finanzas
- Accede a facturas de proveedor y reportes financieros.
- No modifica recepciones ni despachos.
- **Grupo Odoo:** `account.group_account_user`

---

## Restricciones conocidas

- Los grupos de acceso propios de MADENAT deben estar declarados en `security/ir.model.access.csv`.
- Ver [[security_accesos]] para la matriz completa de permisos.

---

## Relacionado

- [[security_accesos]]
- [[00_ARQUITECTURA]]
- [[flujo_recepcion_madera]]
