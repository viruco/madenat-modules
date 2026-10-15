# -*- coding: utf-8 -*-
"""AUD-ETQ-08 (2026-10-12): coherencia de dependencias de los campos calculados
de la consola de Ingreso de Madera (`madenat.lumber.intake.console`).

La consola es una vista SQL de SOLO LECTURA (`_auto=False`): sus campos
calculados proyectan el registro origen. La dependencia NO debe referenciar el
proxy Many2many VIRTUAL `volume_detail_line_ids` (compute+inverse, store=False,
NO buscable), que producía el aviso de Odoo ``should be searchable`` para cada
campo calculado por ``_compute_review_metrics``.

Contrato bajo prueba (sin re-ejecutar la carga del registry, que ya se validó en
el arranque):

* la dependencia canónica son los campos de IDENTIDAD del origen;
* el proxy virtual conserva su naturaleza (no se le añadió un ``search``
  ficticio, ni se cambió su ``store``, ni se eliminó semántica).
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'madenat', 'madenat_lumber_intake')
class TestIntakeConsoleComputeDepends(TransactionCase):

    CONSOLE = 'madenat.lumber.intake.console'
    # Campos calculados por `_compute_review_metrics` (los advertidos).
    METRIC_FIELDS = (
        'total_volume_m3', 'official_volume_m3', 'volume_detail_m3',
        'volumen_suma_detalle', 'volumen_fuente', 'volume_excel_m3',
        'official_volume_source', 'official_vs_detail_diff_m3',
        'supplier_documental_name', 'supplier_documental_rut',
        'supplier_resolution_status', 'volume_operational_source',
        'conciliation_status', 'volumen_pdf_m3',
    )

    def test_aud_etq_08_depends_sin_proxy_virtual(self):
        Console = self.env[self.CONSOLE]
        for name in self.METRIC_FIELDS:
            field = Console._fields[name]
            self.assertEqual(
                field.compute, '_compute_review_metrics',
                '%s ya no usa el compute de métricas' % name)
            # Odoo 18: la dependencia efectiva se resuelve sobre el método
            # (`get_depends`), no sobre un atributo `depends` del campo.
            deps, _ctx = field.get_depends(Console)
            for dep in deps:
                self.assertNotIn(
                    'volume_detail_line_ids', dep,
                    '%s depende del proxy virtual no buscable: %s'
                    % (name, dep))
            # La dependencia de identidad del origen debe estar presente.
            self.assertIn('source_res_id', deps,
                          '%s debe depender del origen' % name)

    def test_aud_etq_08_proxy_virtual_inalterado(self):
        """El proxy conserva compute+inverse y store=False (sin search ficticio)."""
        field = self.env[self.CONSOLE]._fields['volume_detail_line_ids']
        self.assertFalse(field.store, 'El proxy virtual no debe almacenarse')
        self.assertTrue(field.compute, 'El proxy debe seguir siendo calculado')
        self.assertTrue(field.inverse, 'El proxy debe conservar su inverse')
        self.assertFalse(
            getattr(field, 'search', None),
            'No se debe implementar un search ficticio')
