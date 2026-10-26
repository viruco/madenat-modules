# ENTORNOS DE TRABAJO — MADENAT

Fecha de registro: 2026-10-03
Repositorio de módulos: `git@github.com:viruco/madenat-modules.git`

Este documento separa de forma definitiva el **entorno operativo** (estable,
protegido) del **entorno de desarrollo** (experimental, aislado), para poder
continuar el trabajo PRE-02 / P0-R sin volver a afectar `madenat_test`.

---

## 1. OPERATIVO (PROTEGIDO)

- **Ruta de addons:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`
- **Rama:** `feat/guia-correccion-documental-preservada-20261002`
- **SHA:** `106d0010ec6cc7924046c50029b95ecd10677896` (`106d0010ec`)
- **Base de datos operativa:** `madenat_test`
- **Estado del árbol:** limpio (sin cambios pendientes)
- **Montaje en Odoo:** `custom_addons` → `/mnt/extra-addons` (docker-compose)

> **PROHIBIDO** cambiar de rama en `custom_addons`.
> **PROHIBIDO** probar o ejecutar desarrollo experimental aquí.

---

## 2. DESARROLLO (AISLADO)

- **Ruta del worktree:** `/home/viruco/dev-stack/odoo/odoo-18-ce/madenat_dev_p0r_20261003`
- **Rama:** `feat/p0-r-core-sv-foundation-remediation-20261002`
- **SHA (HEAD esperado):** `bee61e7ee3b829376e261ea37b3f38a9202f2bbd` (`bee61e7ee3`)
- **Commit PRE-02:** `bee61e7` — *fix(core): garantiza cantidades reales en recepción service*
- **Estado del árbol:** limpio (sin cambios pendientes)
- **Uso:** **sólo** para bases de datos temporales **nuevas**.

> **PROHIBIDO** usar `madenat_test` como base para este código experimental.
> Este worktree **no** debe montarse sobre el Odoo operativo ni sobre
> `/mnt/extra-addons` mientras se experimente.

---

## 3. REGLA DE AISLAMIENTO

1. Cada base de datos temporal debe usar su **propia copia / worktree de addons**.
2. **Nunca** usar `madenat_test` con código experimental.
3. El código operativo de `custom_addons` permanece congelado en
   `feat/guia-correccion-documental-preservada-20261002` @ `106d0010ec`.
4. El filestore, los datos, el stock, los usuarios y la auditoría de
   `madenat_test` son intocables desde el área de desarrollo.

---

## 4. EVIDENCIA DE VERIFICACIÓN (2026-10-03)

- `custom_addons`: rama `feat/guia-correccion-documental-preservada-20261002`,
  SHA `106d0010ec...`, árbol limpio. ✔
- Worktree de desarrollo `madenat_dev_p0r_20261003`: rama
  `feat/p0-r-core-sv-foundation-remediation-20261002`, HEAD `bee61e7ee3...`,
  árbol limpio. ✔
- Commit PRE-02 presente en el worktree (`bee61e7`). ✔
- `git diff --check 4aa40113..bee61e7` → sin errores. ✔
- Contenedores: `odoo18_app` Up, `odoo18_db` Up (healthy). ✔
- Montaje `/mnt/extra-addons` → `custom_addons` sin cambios. ✔
- Bases de datos, filestores y contenedores: sin cambios. ✔

**Dictamen:** ENTORNOS SEPARADOS — LISTOS PARA CONTINUAR.
