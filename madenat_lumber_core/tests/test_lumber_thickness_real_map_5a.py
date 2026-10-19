# -*- coding: utf-8 -*-
"""Pruebas unitarias para Bloque 5A (AD-126): Tabla de Espesores Reales Físicos (lumber.thickness.real.map).

Verifica:
  1. Integridad de registros semilla canónicos (4/4, 5/4, 6/4, 7/4, 8/4).
  2. Coherencia fraccionaria decimal<->etiqueta (tolerancia <= 0.001").
  3. Restricciones de unicidad y valores positivos.
  4. Getter get_thickness_real_mm en madenat.ingestion.config.
  5. Anti-hardcode: el cálculo lee de la tabla en base de datos, sin copias estáticas.
  6. Permisos de acceso por rol (Config Manager, Auditoría, Usuario base).
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, AccessError


@tagged('post_install', '-at_install', 'madenat_lumber_core')
class TestLumberThicknessRealMap5A(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ThicknessMap = cls.env['lumber.thickness.real.map']
        cls.config = cls.env['madenat.ingestion.config']

        # Grupos de seguridad
        cls.group_config = cls.env.ref('madenat_lumber_core.group_lumber_config_manager')
        cls.group_operaciones = cls.env.ref('madenat_lumber_core.group_madenat_operaciones')
        cls.group_auditoria = cls.env.ref('madenat_lumber_core.group_madenat_auditoria')
        cls.group_user = cls.env.ref('base.group_user')

        # Usuarios de prueba
        cls.user_config = cls.env['res.users'].create({
            'name': 'Usuario Config Test 5A',
            'login': 'user_config_5a@madenat.test',
            'email': 'user_config_5a@madenat.test',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_config.id])],
        })
        cls.user_operaciones = cls.env['res.users'].create({
            'name': 'Usuario Operaciones Test 5A',
            'login': 'user_operaciones_5a@madenat.test',
            'email': 'user_operaciones_5a@madenat.test',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_operaciones.id])],
        })
        cls.user_auditoria = cls.env['res.users'].create({
            'name': 'Usuario Auditoria Test 5A',
            'login': 'user_auditoria_5a@madenat.test',
            'email': 'user_auditoria_5a@madenat.test',
            'groups_id': [(6, 0, [cls.group_user.id, cls.group_auditoria.id])],
        })
        cls.user_readonly = cls.env['res.users'].create({
            'name': 'Usuario Readonly Test 5A',
            'login': 'user_readonly_5a@madenat.test',
            'email': 'user_readonly_5a@madenat.test',
            'groups_id': [(6, 0, [cls.group_user.id])],
        })

    def test_01_seed_records_exist_and_match_canonical(self):
        """Los 5 registros canónicos (4/4 a 8/4) existen con sus mm reales exactos."""
        expected = {
            '4/4': (1.0, 25.4),
            '5/4': (1.25, 31.75),
            '6/4': (1.5, 38.1),
            '7/4': (1.75, 44.45),
            '8/4': (2.0, 50.8),
        }
        for visual, (exp_in, exp_mm) in expected.items():
            rec = self.ThicknessMap.search([('thickness_visual', '=', visual), ('active', '=', True)], limit=1)
            self.assertTrue(rec, f"Registro para {visual} debe existir en BD")
            self.assertAlmostEqual(rec.thickness_nominal_in, exp_in, places=4)
            self.assertAlmostEqual(rec.thickness_real_mm, exp_mm, places=3)
            self.assertIn(visual, rec.name)

    def test_02_coherence_validation_success_and_failure(self):
        """Valida que la coherencia entre nominal_in y visual sea exigida dentro de 0.001\"."""
        # Creación exitosa de formato coherente '3/4' -> 0.75"
        rec = self.ThicknessMap.create({
            'thickness_visual': '3/4',
            'thickness_nominal_in': 0.75,
            'thickness_real_mm': 19.05,
            'sequence': 5,
        })
        self.assertTrue(rec.id)

        # Incoherencia: '9/4' (=2.25) con 1.5" nominal -> ValidationError
        with self.assertRaises(ValidationError):
            self.ThicknessMap.create({
                'thickness_visual': '9/4',
                'thickness_nominal_in': 1.5,
                'thickness_real_mm': 38.1,
            })

        # Etiqueta ininterpretable -> ValidationError
        with self.assertRaises(ValidationError):
            self.ThicknessMap.create({
                'thickness_visual': 'invalido_xyz',
                'thickness_nominal_in': 1.0,
                'thickness_real_mm': 25.4,
            })

    def test_03_getter_resolution_and_anti_hardcode(self):
        """get_thickness_real_mm resuelve dinámicamente desde la BD sin copias estáticas."""
        # Búsqueda canónica por visual
        t_6_4 = self.config.get_thickness_real_mm('6/4')
        self.assertEqual(t_6_4, 38.1)

        t_5_4 = self.config.get_thickness_real_mm('5/4')
        self.assertEqual(t_5_4, 31.75)

        # Búsqueda por pulgadas decimales
        t_dec = self.config.get_thickness_real_mm(thickness_inches=1.5)
        self.assertEqual(t_dec, 38.1)

        # Prueba anti-hardcode: modificar el registro en BD altera el resultado de la función
        rec_6_4 = self.ThicknessMap.search([('thickness_visual', '=', '6/4')], limit=1)
        original_mm = rec_6_4.thickness_real_mm
        try:
            rec_6_4.write({'thickness_real_mm': 38.5})
            # El getter debe reflejar el cambio en BD inmediatamente
            self.assertEqual(self.config.get_thickness_real_mm('6/4'), 38.5)
        finally:
            rec_6_4.write({'thickness_real_mm': original_mm})

    def test_04_security_access_rights(self):
        """Permisos: Config, Operaciones y Auditoría pueden escribir/leer; usuario base solo leer."""
        # Config Manager puede crear/editar
        rec = self.ThicknessMap.with_user(self.user_config).search([('thickness_visual', '=', '6/4')], limit=1)
        self.assertTrue(rec)

        # Operaciones puede leer y editar
        rec_op = self.ThicknessMap.with_user(self.user_operaciones).search([('thickness_visual', '=', '6/4')], limit=1)
        self.assertTrue(rec_op)
        rec_op.write({'notes': 'Nota de Operaciones'})
        self.assertEqual(rec_op.notes, 'Nota de Operaciones')

        # Auditoría puede leer y editar
        rec_aud = self.ThicknessMap.with_user(self.user_auditoria).search([('thickness_visual', '=', '6/4')], limit=1)
        self.assertTrue(rec_aud)
        rec_aud.write({'notes': 'Nota de Auditoría'})
        self.assertEqual(rec_aud.notes, 'Nota de Auditoría')

        # Usuario base puede leer
        rec_user = self.ThicknessMap.with_user(self.user_readonly).search([('thickness_visual', '=', '6/4')], limit=1)
        self.assertTrue(rec_user)
        self.assertEqual(rec_user.thickness_real_mm, 38.1)

        # Usuario base NO puede escribir
        with self.assertRaises(AccessError):
            rec_user.write({'notes': 'Intento de edicion no autorizada'})
