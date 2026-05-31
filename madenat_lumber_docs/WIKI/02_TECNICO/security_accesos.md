# Seguridad y Accesos — Grupos y Permisos

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documentar los grupos de seguridad y permisos de acceso (`ir.model.access`) que controlan quién puede ver y modificar los datos en MADENAT.

---

## Contexto

La seguridad de MADENAT es minimalista: usa solo 2 grupos custom sobre la categoría `MADENAT: Gestión Madera`, y se apoya en grupos estándar de Odoo (`base.group_user`, `stock.group_stock_manager`, `base.group_system`) para los permisos CRUD. No existen reglas de dominio (`ir.rule`).

---

## Categoría de seguridad

| XML ID | Nombre visible |
|---|---|
| `module_category_madenat` | `MADENAT: Gestión Madera` |

---

## Grupos de seguridad

| XML ID | Nombre visible | Hereda de | Usuarios típicos |
|---|---|---|---|
| `group_madenat_cost_auditor` | Auditor de Costos (Felipe) | `base.group_user` | Contabilidad / Auditoría |
| `group_madenat_admin` | Administrador Madenat | `group_madenat_cost_auditor` | Gerencia / Admin |

> **Nota:** `group_madenat_admin` hereda implícitamente los permisos de `group_madenat_cost_auditor`, que a su vez hereda de `base.group_user`.

---

## Permisos de acceso (ir.model.access)

Los permisos se definen en `security/ir.model.access.csv`. No usan grupos custom; se basan en grupos estándar de Odoo:

### Modelo: stock.lot

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` (Todos los usuarios) | ✅ | ✅ | ✅ | ❌ |

### Modelo: lumber.reception

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ❌ |
| `stock.group_stock_manager` | ✅ | ✅ | ✅ | ✅ |

### Modelo: lumber.reception.line

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ✅ |
| `stock.group_stock_manager` | ✅ | ✅ | ✅ | ✅ |

### Modelo: stock.lot.cost.line

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ❌ | ❌ | ❌ |
| `stock.group_stock_manager` | ✅ | ✅ | ✅ | ✅ |

### Modelo: madenat.subproducto

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ❌ |
| `stock.group_stock_manager` | ✅ | ✅ | ✅ | ✅ |

### Modelo: madenat.audit.log

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ❌ | ✅ | ❌ |
| `base.group_system` (Settings/Admin) | ✅ | ✅ | ✅ | ✅ |

### Modelo: madenat.guia.processing

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ❌ |
| `stock.group_stock_manager` | ✅ | ✅ | ✅ | ✅ |

### Modelo: madenat.guia.processing.line

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ✅ |

### Wizard: lumber.reception.mass_update

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ✅ |

### Wizard: madenat.guia.mass_update

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ✅ |

### Modelo: validation.checklist.item

| Grupo | Leer | Escribir | Crear | Eliminar |
|---|---|---|---|---|
| `base.group_user` | ✅ | ✅ | ✅ | ❌ |
| `stock.group_stock_manager` | ✅ | ✅ | ✅ | ✅ |

---

## Reglas de dominio (ir.rule)

**No existen reglas de dominio (`ir.rule`) en madenat_lumber_core.** Todos los usuarios con acceso a un modelo pueden ver todos los registros de ese modelo.

---

## Restricciones conocidas

- `stock.lot` solo permite lectura para usuarios normales; la eliminación está bloqueada (`perm_unlink = 0`).
- `madenat.audit.log` es de solo lectura para usuarios normales; solo admins del sistema (`base.group_system`) pueden modificar o eliminar logs.
- `stock.lot.cost.line` permite solo lectura para usuarios normales; los managers gestionan los costos.
- Los wizards (`mass_update`) tienen permisos completos para todos los usuarios, ya que se ejecutan en contexto controlado.
- Si se necesitan reglas de dominio por usuario o por recepción, deben crearse explícitamente en `madenat_security.xml`.

---

## Evidencia

- Archivo: `custom_addons/madenat_lumber_core/security/madenat_security.xml`
- Archivo: `custom_addons/madenat_lumber_core/security/ir.model.access.csv`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[00_ARQUITECTURA]]
- [[modulo_lumber_core]]
- [[dependencias_modulos]]
- [[herencia_odoo_modelos]]
