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

# Origen EXCLUSIVO de la fila de cabecera declarada del detalle documental de
# Volúmenes: refleja los datos declarados de la cabecera de la Guía (piezas,
# RW, RL, espesor) y el VOLUMEN OFICIAL VIGENTE. Como máximo existe UNA fila
# con este origen por Guía.
#
# Regla anti doble conteo: la fila de cabecera NUNCA se suma a los agregados
# del detalle documental (`volume_detail_m3`, `official_vs_detail_diff_m3`,
# conciliación documental) porque su volumen ES el oficial: sumarlo duplicaría
# el volumen de las líneas del PDF/Excel. Los agregados canónicos excluyen esta
# fila por su origen (ver `madenat.guia.processing._compute_volume_detail_m3`).
HEADER_DECLARED_ORIGIN = 'header'

# Descripción por defecto de la fila de cabecera declarada (`origin='header'`).
# Se asigna SOLO al CREARLA (primera pulsación de «Aplicar datos documentales»),
# de modo que el operador tenga desde el inicio un texto claro de qué es esa
# fila. Las actualizaciones posteriores NUNCA pisan `description` ni
# `observation`: pueden haber sido editadas por el operador. La observación
# nace vacía.
HEADER_DECLARED_DESCRIPTION = (
    'Declaración de cabecera (piezas y dimensiones declaradas)')

# Contexto interno del diálogo «Agregar ítem» de la Consola de Ingresos
# (captura HUMANA del detalle declarado de Volumen). Viaja en el
# `ir.actions.act_window` del botón y llega al `create`/`write` de la línea:
#   - `create` fuerza `origin='manual'` y exige guía de Volumen no terminal;
#   - `write` solo admite filas manuales y nunca cambia el origen.
# Se usa una clave de contexto (no un flag de campo) para que el wizard de
# ingesta siga creando evidencia `pdf`/`excel` con su ruta estándar.
DECLARED_MANUAL_ENTRY_CONTEXT = 'madenat_declared_manual_entry'

# Clave de contexto PROPIA del diálogo «Agregar ítem» que transporta la guía
# destino SIN recurrir a `default_guia_id`.
#
# Motivo (AD-declarado): `madenat.lumber.volume.detail.line.guia_id` es el campo
# inverso del One2many no almacenado `declared_piece_line_ids` de la Consola.
# Si el diálogo inyecta `default_guia_id`, el `default_get`/onchange puebla
# `guia_id` y Odoo registra ese One2many (definido en la CONSOLA, no en
# `madenat.guia.processing`) como inverso GLOBAL de `guia_id`; al escribir un
# `guia_id` "nuevo" la caché ejecuta `modified('declared_piece_line_ids')`
# sobre registros de guía y rompe con KeyError. Con esta clave propia el
# formulario del diálogo NO expone ni recibe `guia_id`: el `create` de la línea
# lee la guía real de aquí cuando falta `guia_id`.
DECLARED_GUIA_ID_CONTEXT = 'madenat_declared_guia_id'