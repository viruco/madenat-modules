"""
ARCHIVADO: _cleanup_orphan_moves() — lumber_reception.py:3056-3118
Fecha de archivado: 2026-07-06
Motivo: Código muerto confirmado — 0 callers en producción.
        Los 3 métodos de cleanup_orphan_moves contienen el FIX 2026-07-01
        (protección quantity > 0) y son ~90% idénticos.
        Este método fue definido para "reutilización y testeo independiente"
        pero nunca fue invocado. La funcionalidad real se usa a través de
        reception_service.cleanup_orphan_moves() llamado desde unlink().
Commit checkpoint (rollback): 56ef4179eecb6409b0e70ff35b0ad15337dcf69d
Ver: AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md (Corrección Post-Investigación)
"""
# ── CÓDIGO ORIGINAL ARCHIVADO ─────────────────────────────────────────────

    def _cleanup_orphan_moves(self):
        """
        🧹 Elimina stock.moves huérfanos (sin picking) generados por esta recepción.
        Método separado para reutilización y testeo independiente.
        """
        # 🔒 TD-001: Guardia de grupo antes de eliminar stock.moves
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(
                "No tienes permisos para eliminar movimientos de stock huérfanos.\n"
                "Se requiere el grupo 'Inventario / Administrador'."
            )
        names = self.mapped('name')
        moves = self.env['stock.move'].sudo().search([
            ('origin', 'in', names),
            ('picking_id', '=', False),
        ])
        if not moves:
            return

        _logger.info(
            "🧹 MADENAT cleanup: %d stock.moves huérfanos encontrados para guías: %s",
            len(moves), names
        )

        # 🛡️ FIX 2026-07-01: Protección de moves con cantidad recolectada (quantity > 0).
        # Odoo bloquea nativamente el unlink de stock.move/stock.move.line que ya tienen
        # cantidad recolectada. En vez de forzar y causar UserError, marcamos esos moves
        # como "HUERFANO-PROTEGIDO-" y los dejamos para revisión manual de Inventario.
        # Causa raíz: action_reopen_to_draft() FASE 3 desvincula pickings 'done'
        # cambiando su 'origin' pero sin cancelarlos, generando moves huérfanos con quantity>0.
        protected_moves = moves.filtered(
            lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids)
        )
        cleanable_moves = moves - protected_moves

        if protected_moves:
            for pm in protected_moves:
                pm.origin = f"HUERFANO-PROTEGIDO-{pm.origin or ''}"
            _logger.warning(
                "🛡️ %d stock.move(s) con cantidad recolectada NO fueron eliminados "
                "(protegidos por integridad de Odoo). Marcados como huérfanos protegidos: %s",
                len(protected_moves), protected_moves.mapped('name'),
            )
            self[:1].message_post(
                body=(
                    "🛡️ <strong>Integridad de Inventario:</strong> "
                    f"{len(protected_moves)} movimiento(s) con cantidad ya recolectada "
                    "no se pudieron eliminar y quedaron marcados para revisión manual del "
                    "equipo de Inventario. Moves: "
                    f"{', '.join(protected_moves.mapped('name'))}"
                )
            )

        if not cleanable_moves:
            _logger.info(
                "🛡️ Todos los moves huérfanos están protegidos (tienen cantidad recolectada). "
                "No se eliminará ninguno."
            )
            return

        cleanable_moves.sudo().mapped('move_line_ids').unlink()
        cleanable_moves.sudo().write({'state': 'draft'})
        cleanable_moves.sudo().unlink()
