{
    'name': 'MADENAT Ingestion Engine',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Motor de extracción y normalización de documentos de '
                'ingreso de madera (Excel/PDF), independiente del destino '
                'de negocio (Recepción Directa o Guía de Procesamiento).',
    'description': """
Motor de Ingesta MADENAT
=========================

Extrae y normaliza los datos declarados en documentos de ingreso de madera
(Excel/PDF) hacia un contrato único de cabecera y líneas, sin decidir
clasificación de negocio, sin calcular costos y sin escribir en stock.

Este módulo es aditivo: no reemplaza ni modifica lumber.reception ni
madenat.guia.processing. Ver README.md para alcance completo, no-objetivos
y plan de integración futura.
""",
    'author': 'MADENAT',
    'license': 'LGPL-3',
    'depends': ['base', 'madenat_lumber_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/ingestion_document_sequence.xml',
        'views/ingestion_column_profile_views.xml',
        'views/ingestion_document_views.xml',
        'views/ingestion_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
