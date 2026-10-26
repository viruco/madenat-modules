# H1 / H2 / H3 — Diseño mínimo (FASE 4)

## H1 — Motivo obligatorio en la vía directa

**Archivo:** `madenat_lumber_core/models/madenat_guia_processing.py` (`unlink()`).

```python
reason = (self.env.context.get(self._GUIA_DELETE_REASON_CTX) or '').strip()
if not reason:
    raise UserError(_('Para eliminar la guía %(name)s debe indicar un MOTIVO. Use la acción de '
                      'eliminación con motivo (Consola de Ingreso de Madera → Ciclo de vida de la guía '
                      '→ Modo A, con motivo) en lugar del borrado directo.') % {'name': self[:1].name or ''})
if not self.env.context.get(self._GUIA_DELETE_LOGGED_CTX):
    for rec in self:
        rec._guia_log_deletion(reason)
```

- **Vía nativa (botón de lista/formulario):** no aporta contexto ⇒ **bloqueada con mensaje**. Decisión: la opción
  que **menos cambia las vistas** (cero cambios en XML/JS).
- **Vías legítimas:** asistente de ciclo de vida (`_run_delete_definitive`, `_run_controlled_purge`) y
  **reclasificación AD-73** (`action_confirm_reclassify`) aportan motivo de negocio propio.
- **Bypass test-only** intacto: `_sv_test_cleanup_allowed` (marcador + `--test-enable` real + BD de test).

## H2 — Rol autorizado

```python
GUIA_DELETE_GROUPS = ('madenat_lumber_core.group_madenat_jefatura_operaciones', 'base.group_system')

def _guia_delete_group_ok(self):
    user = self.env.user
    return any(user.has_group(g) for g in self.GUIA_DELETE_GROUPS)
```

Consumida por `unlink()` (paso 1b, tras el estado y **antes** del pre-chequeo de dependencias y de `super()`),
por `_cleanup_orphan_moves_guia()` (sustituye la guarda TD-001) y por
`intake_guide_lifecycle_wizard._delete_access_blocker()` (UX). **No** se amplían permisos de stock ni se crean
grupos. La constante `GROUP_STOCK_MANAGER` del asistente queda sin uso y se retira.

Efecto medido: la guarda de rol se evalúa **antes** de `super().unlink()`, por lo que un usuario sin jefatura ni
ACL recibe un `UserError` de negocio (antes: `AccessError` de `ir.model.access`). Documentado y ajustado en
`test_guia_delete_acl.test_03/test_05` y en `test_guia_delete_guards.test_i`.

## H3 — Bitácora APPEND-ONLY (H-SEC-5 mínimo)

```python
def _audit_mutation_allowed(self):
    token = self.env.context.get('madenat_sv_test_cleanup_token')
    marker = self.env['madenat.sv.internal.marker'].sudo()
    if not token or not marker._sv_test_enable_strict():
        return False
    return bool(marker.search_count([('token', '=', token)]))

def write(self, vals):  # y unlink()
    if self._audit_mutation_allowed():
        return super().write(vals)
    raise UserError(_('La bitácora de auditoría (madenat.audit.log) es APPEND-ONLY: …'))
```

- **ACL** (`security/ir.model.access.csv`): `access_madenat_audit_log_manager` `1,1,1,1` → **`1,0,1,0`**.
- **Limpieza test-only del ledger** (`madenat_sv_internal._sv_test_cleanup_token`): el borrado de la bitácora
  pasa a `audit.with_context(**cleanup_ctx).unlink()` (mismo patrón inerte). Los marcadores del token aún existen
  en ese punto del flujo ⇒ el token está «vivo» y la excepción es válida.
- **FK `ondelete='set null'`** de `guia_processing_id`: Odoo la anula por SQL interno, por lo que **no** dispara
  la guarda de escritura (verificado: eliminar guías con bitácora asociada sigue funcionando).
- **No se tocan registros existentes**; la migración no requiere datos ni scripts.
- **Límite honesto:** SQL directo y DBA siguen pudiendo alterar. Defensa propuesta (no implementada): trigger
  `BEFORE UPDATE/DELETE` sobre `madenat_audit_log`, o hash encadenado por fila (`audit_hash` ya existe como campo).
