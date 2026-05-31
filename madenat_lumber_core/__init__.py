# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

# ✅ VALIDACIÓN CRÍTICA: Dependencias Python Externas
REQUIRED_LIBS = ['pandas', 'pdfplumber', 'openpyxl']
missing_libs = []

for lib in REQUIRED_LIBS:
    try:
        __import__(lib)
    except ImportError:
        missing_libs.append(lib)

if missing_libs:
    error_msg = (
        f"❌ MADENAT Core requiere librerías Python faltantes: {', '.join(missing_libs)}\n"
        f"Instalar con: pip3 install {' '.join(missing_libs)}"
    )
    _logger.error(error_msg)
    raise ImportError(error_msg)

_logger.info("✅ Dependencias Python validadas: %s", ', '.join(REQUIRED_LIBS))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMPORTS DE SUBMÓDULOS (NO IMPORTAR MODELOS DIRECTAMENTE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from . import models
from . import reports
from . import scripts
from . import wizard
