# -*- coding: utf-8 -*-
"""Constantes canónicas del módulo madenat_lumber_intake.

Fuente única de verdad para valores compartidos entre modelos. No es un
modelo ORM; solo define constantes módulo-level importables.
"""

# Offset canónico para madenat.guia.processing en la vista de consola.
# Regla: Procesado usa CONSOLE_ID_OFFSET + id; lumber.reception usa id sin
# offset (ver README sección 7). Evita colisión entre las dos fuentes de la
# vista UNION ALL madenat_lumber_intake_console.
CONSOLE_ID_OFFSET = 900000000