# -*- coding: utf-8 -*-
"""Utilidades de prueba para la vigencia de la lectura (FASE 13/2D).

Desde la FASE 13/2D (decisión H2) `action_route_document` exige una lectura
vigente en las TRES modalidades: estado 'previewed' y huella
(`reading_signature`) coherente con los datos actuales. Las pruebas cuyo objeto
es la derivación —no la lectura— pueden marcar el wizard como leído sin
ejecutar el motor de extracción.
"""


def mark_previewed(wizard):
    """Deja el wizard en el estado que produce `action_preview_document()`.

    No ejecuta el motor de extracción: sólo fija 'previewed' y la huella de los
    datos que el wizard tiene en ese momento. Si después se modifican entradas
    de la lectura (archivos, perfil, patio o nivel de detalle), la huella deja
    de coincidir y el ruteo se rechaza: es el comportamiento esperado.
    """
    wizard.write({
        'state': 'previewed',
        'reading_signature': wizard._reading_signature(),
    })
    return wizard
