# -*- coding: utf-8 -*-
"""Pruebas unitarias para G8 (AD-120 / Bloque 4G):
Edición de lumber.width.s2s.map por interfaz, coherencia decimal/etiqueta,
archivo (active=False) y protección de histórico.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestLumberWidthS2SMapG8(TransactionCase):

    def setUp(self):
        super().setUp()
        self.map_model = self.env['lumber.width.s2s.map']
        self.config = self.env['madenat.ingestion.config']

    def test_01_g8_coherence_validation_valid(self):
        """G8: etiqueta '4 3/8' con decimal 4.375 es coherente (diff 0.0 <= 0.0625)."""
        rec = self.map_model.new({
            'rough_mm': 999,
            's2s_decimal': 4.375,
            's2s_label': '4 3/8',
            'active': True,
        })
        # No debe levantar ValidationError
        rec._check_decimal_label_coherence()

    def test_02_g8_coherence_validation_divergence_fails(self):
        """G8: etiqueta '4 3/8' (4.375) con decimal 4.125 (4 1/8) levanta ValidationError."""
        rec = self.map_model.new({
            'rough_mm': 999,
            's2s_decimal': 4.125,
            's2s_label': '4 3/8',
            'active': True,
        })
        with self.assertRaises(ValidationError) as cm:
            rec._check_decimal_label_coherence()
        self.assertIn("Incoherencia entre etiqueta y decimal S2S", str(cm.exception))

    def test_03_g8_archive_instead_of_delete(self):
        """G8: archivar entrada (active=False) la retira de la resolución activa."""
        rec_100 = self.map_model.search([('rough_mm', '=', 100), ('active', '=', True)], limit=1)
        self.assertTrue(rec_100, "Debe existir registro activo para 100 mm.")
        try:
            rec_100.write({'active': False})
            mapping = self.config.get_width_s2s_map(raise_if_empty=False)
            self.assertNotIn(100, mapping, "Entrada archivada active=False no debe aparecer en mapeo activo.")
        finally:
            rec_100.write({'active': True})

    def test_04_g8_edit_affects_new_calculation(self):
        """G8: editar un registro afecta cálculos nuevos guiados por la tabla."""
        rec_100 = self.map_model.search([('rough_mm', '=', 100), ('active', '=', True)], limit=1)
        orig_decimal = rec_100.s2s_decimal
        orig_label = rec_100.s2s_label
        try:
            # 100 mm nominal: 3.625 + 0.125 = 3.750"
            val_orig = self.config.resolve_export_width(100.0)
            self.assertAlmostEqual(val_orig, 3.750, places=4)

            # Modificar coherente a 3.750 (etiqueta "3 3/4")
            rec_100.write({'s2s_decimal': 3.750, 's2s_label': '3 3/4'})
            val_new = self.config.resolve_export_width(100.0)
            self.assertAlmostEqual(val_new, 3.750 + 0.125, places=4,
                                   msg="Cálculo nuevo debe reflejar el decimal editado en la tabla.")
        finally:
            rec_100.write({'s2s_decimal': orig_decimal, 's2s_label': orig_label})
