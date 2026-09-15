# -*- coding: utf-8 -*-
"""Tests de instalación del modelo `madenat.ingestion.column.profile`.

El test del placeholder `NotImplementedError` fue retirado en Fase 2: la
función `extract_document()` ya está implementada (ver
`test_document_extractor.py`).
"""

from odoo.tests.common import TransactionCase


class TestIngestionColumnProfileModel(TransactionCase):
    """Verificación del modelo esqueleto de perfiles de columnas."""

    def test_column_profile_model_installable(self):
        """Verifica que el modelo de perfil de columnas se instale correctamente."""
        profile = self.env['madenat.ingestion.column.profile'].create({
            'name': 'Perfil de prueba',
        })
        self.assertTrue(profile.id, 'El perfil debe tener ID después de crearse')
        self.assertEqual(
            profile.sequence,
            10,
            'El sequence por defecto debe ser 10'
        )
        self.assertTrue(
            profile.active,
            'El perfil debe estar activo por defecto'
        )

    def test_column_profile_default_values(self):
        """Verifica que los valores por defecto del modelo sean correctos."""
        profile = self.env['madenat.ingestion.column.profile'].create({
            'name': 'Prueba de defaults',
        })
        self.assertEqual(profile.sequence, 10)
        self.assertTrue(profile.active)
        self.assertFalse(profile.notes or '', 'notes debe estar vacío por defecto')

    def test_column_profile_can_be_deactivated(self):
        """Verifica que los perfiles se pueden desactivar."""
        profile = self.env['madenat.ingestion.column.profile'].create({
            'name': 'Perfil activo',
            'active': True,
        })
        self.assertTrue(profile.active)
        profile.active = False
        self.assertFalse(profile.active)
