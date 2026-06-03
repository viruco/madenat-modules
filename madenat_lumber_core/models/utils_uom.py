# -*- coding: utf-8 -*-
"""
UTILIDADES UoM - REGLA DE ORO: Factor MBF_TO_M3 = 2.36
ÚNICA fuente de verdad para conversiones m³ ↔ MBF



Versión: 3.2.0 (2026-04-09) - FUENTE ÚNICA: S2S_WIDTH_LOOKUP + calculate_volume_metric_m3
==========================================================



FACTOR OFICIAL: 1 MBF = 2.36 m³
- Factor exacto NIST: 2.359737216 m³
- Factor industria: 2.36 m³ (error: 0.16%, aceptable)
- Referencia: Woodweb Knowledge Base, NIST SP 811



CORRECCIÓN CRÍTICA (2026-01-27):
- Factor Imperial corregido según Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx
- Cambio: 5085.312 (in²×ft→m³) → 1550.003 (in²×m→m³)
- Razón: El Excel usa METROS directamente, NO pies



INYECCIÓN TÉCNICA (2026-04-05):
- Incorporación de `decimal_inch_to_fraction_str` para soporte "Blanks Clear".
- El UI (Staging) ahora opera como un Espejo Documental.



FUENTE ÚNICA (2026-04-09):
- S2S_WIDTH_LOOKUP: tabla canónica de 16 anchos mm→pulgadas decimales.
  NO duplicar en lumber_reception.py ni en madenat_guia_processing.py.
- calculate_volume_metric_m3(): única función para volumen métrico mm×mm×m/1_000_000.
  NO hardcodear 1_000_000 fuera de esta función.
- calculate_volume_imperial_to_m3: ahora usa r3() internamente (ROUND_HALF_UP).
"""



import logging
import math
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction



_logger = logging.getLogger(__name__)



# ============================================================================
# 🔥 REGLA DE ORO: CONSTANTE ÚNICA
# ============================================================================



# Factor de conversión estándar de industria maderera
# Nota: Factor exacto NIST = 2.359737216, pero industria usa 2.36
# Diferencia: 0.16% (insignificante para operaciones comerciales)
MBF_TO_M3 = Decimal('2.36')  # 1 MBF = 2.36 m³



# Factor inverso pre-calculado para optimización
M3_TO_MBF = Decimal('1') / MBF_TO_M3  # ≈ 0.423728813559322



# Tolerancia aceptable para validaciones (1%)
CONVERSION_TOLERANCE = Decimal('0.01')



# ============================================================================
# 🪞 ESPEJO DOCUMENTAL (Formato Blanks Clear / Imperial)
# ============================================================================


def decimal_inch_to_fraction_str(decimal_value):
    """
    Transforma un decimal en pulgadas (ej. 1.5625) a su representación 
    fraccionaria maderera (ej. "1 9/16") para la UI (Espejo Documental).

    REGLA DE ORO - UX:
    El usuario debe ver en el Staging exactamente lo que viene en el Excel.

    Args:
        decimal_value (float|str): Valor en pulgadas decimales

    Returns:
        str: Fracción formateada o el mismo string si hay error.
    """
    if decimal_value in (None, False, ""):
        return ""

    try:
        val = float(decimal_value)
        if math.isnan(val):
            return ""
        if val <= 0:
            return "0"


        # Limitamos el denominador a 64 (estándar maderero máximo)
        frac = Fraction(val).limit_denominator(64)
        whole = frac.numerator // frac.denominator
        remainder = frac.numerator % frac.denominator

        if remainder == 0:
            return str(whole)
        elif whole == 0:
            return f"{remainder}/{frac.denominator}"
        else:
            return f"{whole} {remainder}/{frac.denominator}"
    except (ValueError, TypeError):
        # Fallback seguro: si mandan string basura, se devuelve tal cual
        return str(decimal_value)


def decimal_inch_to_mm(decimal_value):
    """
    Transforma un decimal en pulgadas (ej. 1.5625) a milímetros exactos 
    para el cálculo de inventario físico. (1 pulgada = 25.4 mm)
    """
    if decimal_value in (None, False, ""):
        return 0.0

    try:
        return float(decimal_value) * 25.4
    except (ValueError, TypeError):
        return 0.0



# ============================================================================
# 🧮 FUNCIONES DE CONVERSIÓN
# ============================================================================



def m3_to_mbf(m3_value):
    """
    Convertir m³ a MBF con precisión controlada.

    REGLA DE ORO - PRECISIÓN:
    Usa Decimal para evitar errores de punto flotante.
    Redondea a 4 decimales (suficiente para facturación).

    Args:
        m3_value (float|Decimal): Volumen en metros cúbicos

    Returns:
        float: Volumen en MBF (redondeado a 4 decimales)

    Examples:
        >>> m3_to_mbf(2.36)
        1.0
        >>> m3_to_mbf(23.6)
        10.0
        >>> m3_to_mbf(0)
        0.0
    """
    if not m3_value:
        return 0.0

    try:
        m3_decimal = Decimal(str(m3_value))
        mbf_result = m3_decimal * M3_TO_MBF  # Usa factor pre-calculado
        return float(mbf_result.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
    except Exception as e:
        _logger.error(f"❌ Error convirtiendo m³ a MBF: {m3_value}, error: {e}")
        return 0.0




def mbf_to_m3(mbf_value):
    """
    Convertir MBF a m³ con precisión controlada.

    REGLA DE ORO - CONSISTENCIA:
    Usa el mismo factor MBF_TO_M3 que el resto del sistema.
    Redondea a 3 decimales (estándar para m³).

    Args:
        mbf_value (float|Decimal): Volumen en MBF

    Returns:
        float: Volumen en metros cúbicos (redondeado a 3 decimales)

    Examples:
        >>> mbf_to_m3(1.0)
        2.36
        >>> mbf_to_m3(10.0)
        23.6
        >>> mbf_to_m3(0)
        0.0
    """
    if not mbf_value:
        return 0.0

    try:
        mbf_decimal = Decimal(str(mbf_value))
        m3_result = mbf_decimal * MBF_TO_M3
        return float(m3_result.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))
    except Exception as e:
        _logger.error(f"❌ Error convirtiendo MBF a m³: {mbf_value}, error: {e}")
        return 0.0




def r3(value):
    """
    Redondear a 3 decimales con ROUND_HALF_UP (estándar para m³).

    Usar en lugar de round(x, 3) para garantizar ROUND_HALF_UP en todo el sistema.
    Python nativo round() usa Banker's Rounding (ROUND_HALF_EVEN).

    Args:
        value (float|Decimal|None): Valor a redondear

    Returns:
        float: Valor redondeado a 3 decimales
    """
    if value is None:
        return 0.0
    try:
        decimal_val = Decimal(str(value))
        return float(decimal_val.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))
    except Exception as e:
        _logger.error(f"❌ Error redondeando r3: {value}, error: {e}")
        return 0.0




def r4(value):
    """
    Redondear a 4 decimales con ROUND_HALF_UP (estándar para MBF y porcentajes).

    Usar en lugar de round(x, 4) para garantizar ROUND_HALF_UP en todo el sistema.

    Args:
        value (float|Decimal|None): Valor a redondear

    Returns:
        float: Valor redondeado a 4 decimales
    """
    if value is None:
        return 0.0
    try:
        decimal_val = Decimal(str(value))
        return float(decimal_val.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
    except Exception as e:
        _logger.error(f"❌ Error redondeando r4: {value}, error: {e}")
        return 0.0




# ============================================================================
# 🧪 VALIDACIÓN Y TESTS
# ============================================================================



def validate_mbf_factor():
    """
    Validar que el factor MBF_TO_M3 sea consistente.

    REGLA DE ORO - TESTING:
    Ejecutar en startup para garantizar integridad del sistema.

    Returns:
        bool: True si todas las validaciones pasan
    """
    # Validación 1: Factor esperado
    expected_factor = Decimal('2.36')
    if MBF_TO_M3 != expected_factor:
        _logger.error(
            f"❌ VIOLACIÓN REGLA DE ORO: MBF_TO_M3 = {MBF_TO_M3}, "
            f"esperado: {expected_factor}"
        )
        return False

    # Validación 2: Round-trip test
    test_m3 = Decimal('10.0')
    test_mbf = test_m3 * M3_TO_MBF
    test_back = test_mbf * MBF_TO_M3

    diff = abs(test_back - test_m3)
    if diff > Decimal('0.001'):
        _logger.error(
            f"❌ CONVERSIÓN INCONSISTENTE: {test_m3} → {test_mbf} → {test_back} "
            f"(diff: {diff})"
        )
        return False

    # Validación 3: Test con valores reales de negocio
    test_cases = [
        (Decimal('1.0'), Decimal('2.36')),    # 1 MBF = 2.36 m³
        (Decimal('10.0'), Decimal('23.6')),   # 10 MBF = 23.6 m³
        (Decimal('100.0'), Decimal('236.0')), # 100 MBF = 236 m³
    ]

    for mbf, expected_m3 in test_cases:
        result_m3 = Decimal(str(mbf_to_m3(float(mbf))))
        if abs(result_m3 - expected_m3) > Decimal('0.001'):
            _logger.error(
                f"❌ TEST FALLÓ: {mbf} MBF → {result_m3} m³ "
                f"(esperado: {expected_m3} m³)"
            )
            return False

    _logger.info("✅ REGLA DE ORO UoM: MBF_TO_M3 = 2.36 validado correctamente")
    _logger.info(f"   Factor inverso: M3_TO_MBF = {M3_TO_MBF}")
    _logger.info(f"   Diferencia vs NIST (2.359737): {((MBF_TO_M3 / Decimal('2.359737') - 1) * 100):.4f}%")

    return True




def format_volume_display(m3_value, show_mbf=True):
    """
    Formatea volumen para display con ambas unidades.

    REGLA DE ORO - UX:
    Mostrar siempre ambas unidades para facilitar comprensión.

    Args:
        m3_value (float): Volumen en m³
        show_mbf (bool): Si True, incluye conversión a MBF

    Returns:
        str: Texto formateado

    Examples:
        >>> format_volume_display(2.36, show_mbf=True)
        '2.360 m³ (1.000 MBF)'
        >>> format_volume_display(23.6, show_mbf=False)
        '23.600 m³'
    """
    if not isinstance(m3_value, (int, float, Decimal)) or float(m3_value) < 0:
        return "0.000 m³"

    m3_rounded = r3(m3_value)
    m3_str = f"{m3_rounded:.3f} m³"

    if show_mbf:
        mbf_value = m3_to_mbf(m3_value)
        return f"{m3_str} ({mbf_value:.3f} MBF)"

    return m3_str




# ==============================================================================
# 🔥 CONSTANTES IMPERIALES Y TABLA S2S (REGLA DE ORO MADENAT)
# ==============================================================================

# ✅ Factor S2S (largo en metros): in² × metros → m³
# ──────────────────────────────────────────────────────────────────────────
# Conversión dimensional exacta para cubicación comercial de embarque.
# 
# Derivación completa:
#   1 pulgada = 25.4 mm (exacto, según NIST)
#   (25.4 mm)² × 1 m / 1,000,000 = 0.00064516 m³  (mm² × m → m³)
#   1 / 0.00064516 = 1550.003096                    (inverso escalado)
# 
# Uso: cubicación comercial de embarque
#   Fórmula: (Esp.pulg × Ancho.pulg × Largo.m × Pzas) / 1550.003096
# 
# Precisión: dimensional completa IEEE 754 — NO es redondeo arbitrario.
# Referencia: NIST (National Institute of Standards and Technology)
#             — 1 pulgada = 25.4 mm exacto.
# ⚠️ NO modificar este valor sin revisar impacto en todas las fórmulas de cubicación.
# ──────────────────────────────────────────────────────────────────────────
INCH_SQ_METERS_TO_M3 = Decimal('1550.003096')

# ──────────────────────────────────────────────────────────────────────────────
# 📐 CONSTANTES CANÓNICAS DE CONVERSIÓN (TD-003.2 — 2026-05-31)
# ──────────────────────────────────────────────────────────────────────────────
# Fuente única de verdad. NO usar literales como 25.4, 0.3048, 12000.0
# fuera de este archivo.
#
# USO:
#   float(CONSTANTE) → en fórmulas volumétricas (no necesitan Decimal)
#   CONSTANTE        → en cálculos de precio/costo (precisión financiera)
# ──────────────────────────────────────────────────────────────────────────────

# Conversión pulgadas ↔ milímetros (definición exacta NIST)
MM_PER_INCH              = Decimal('25.4')         # 1 pulgada = 25.4 mm exactos
INCHES_PER_MM            = Decimal('1') / MM_PER_INCH  # ≈ 0.03937007874015748

# Conversión pies ↔ metros (definición exacta NIST)
FT_TO_M                  = Decimal('0.3048')       # 1 pie = 0.3048 m exactos
M_TO_FT                  = Decimal('1') / FT_TO_M  # ≈ 3.280839895013123

# Divisores de volumen
M3_DIVISOR               = Decimal('1000000')      # mm² → m² (1000×1000)
MBF_DIVISOR              = Decimal('12000')        # Board Feet divisor

# Factores de cálculo
BLANK_CLEAR_FACTOR       = Decimal('5085.312')     # Factor fórmula Blank Clear (largo en PIES)
IMPERIAL_TO_M3_FACTOR_DEPRECATED = BLANK_CLEAR_FACTOR  # alias back-compat

# Deducciones de espesor (Blank Clear)
FACE_DEDUCTION_INCH      = Decimal('0.0625')       # -1/16" deducción por cara

# Ajustes S2S
S2S_WIDTH_ADJUSTMENT_INCH = Decimal('0.125')       # +1/8" ajuste rough → cepillado



# ──────────────────────────────────────────────────────────────────────────────
# TABLA CANÓNICA S2S: mm nominal → pulgadas decimales
# ──────────────────────────────────────────────────────────────────────────────
# Fuente: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx
# ÚNICA fuente de verdad. NO duplicar en lumber_reception.py
# ni en madenat_guia_processing.py.
#
# Uso:
#   w_inch = S2S_WIDTH_LOOKUP.get(int(width_mm), width_mm / 25.4)
#   El fallback (width_mm / 25.4) es explícito y auditado.
#
S2S_WIDTH_LOOKUP: dict = {
    75:  2.625,   # 2 5/8
    85:  2.875,   # 2 7/8
    90:  3.125,   # 3 1/8
    95:  3.375,   # 3 3/8
    100: 3.625,   # 3 5/8
    105: 3.875,   # 3 7/8
    110: 3.875,   # 3 7/8  ← mismo que 105mm (stair step)
    115: 4.375,   # 4 3/8
    120: 4.375,   # 4 3/8  ← mismo que 115mm (stair step)
    125: 4.625,   # 4 5/8
    130: 4.875,   # 4 7/8
    140: 4.875,   # 4 7/8  ← mismo que 130mm (stair step)
    145: 5.375,   # 5 3/8  ← VALOR CRÍTICO Excel
    150: 5.625,   # 5 5/8
    155: 5.875,   # 5 7/8
    170: 170,     # entero (>160mm proveedor reporta como decimal, no fracción)
}



def calculate_volume_metric_m3(
    thickness_mm,
    width_mm,
    length_m,
    pieces,
):
    """
    Calcula volumen métrico en m³.

    REGLA DE ORO - FUENTE ÚNICA:
    Esta es la ÚNICA función autorizada para volumen métrico (mm × mm × m).
    NO hardcodear ``/ 1_000_000`` fuera de esta función.

    Fórmula: (espesor_mm × ancho_mm × largo_m × piezas) / 1_000_000

    Args:
        thickness_mm (float): Espesor en milímetros.
        width_mm     (float): Ancho en milímetros.
        length_m     (float): Largo en metros.
        pieces       (int|float): Cantidad de piezas.

    Returns:
        float: Volumen en m³ (sin redondeo — el caller decide la precisión).

    Raises:
        ValueError: Si algún parámetro es negativo (logeado, retorna 0.0).

    Examples:
        >>> calculate_volume_metric_m3(45, 100, 4.0, 200)
        3.6
        >>> calculate_volume_metric_m3(45, 125, 3.65, 150)
        3.07...
    """
    if not all(v >= 0 for v in (thickness_mm, width_mm, length_m, float(pieces))):
        _logger.warning(
            f"⚠️ Parámetros inválidos en calculate_volume_metric_m3: "
            f"espesor={thickness_mm}mm, ancho={width_mm}mm, "
            f"largo={length_m}m, piezas={pieces}"
        )
        return 0.0
    return (thickness_mm * width_mm * length_m * float(pieces)) / 1_000_000.0



# ==============================================================================
# 🔥 CÁLCULO DE VOLUMEN IMPERIAL → M³ (REGLA DE ORO MADENAT)
# ==============================================================================



def calculate_volume_imperial_to_m3(
    thickness_inch, 
    width_inch, 
    length_m, 
    pieces, 
    apply_s2s_adjustment=True
):
    """
    Calcula volumen en m³ desde dimensiones imperiales con ajuste S2S.

    ✅ FÓRMULA OFICIAL MADENAT (REGLA DE ORO - Corregida 2026-01-27):
        vol_m3 = (espesor_inch × (ancho_inch + 1/8) × largo_m × piezas) / 1550.003

    CORRECCIÓN CRÍTICA:
    - Antes: Usaba largo en PIES y factor 5085.312
    - Ahora: Usa largo en METROS y factor 1550.003
    - Fuente: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx (Regla de Oro)

    Esta es la ÚNICA función autorizada para cálculo de volumen de embarque.
    Cualquier otro método debe ser validado contra esta implementación.

    Args:
        thickness_inch (float): Espesor en pulgadas (ej: 1.5 para 6/4)
        width_inch (float): Ancho en pulgadas (ej: 4.625 para 4 5/8)
        length_m (float): Largo en METROS (ej: 4.0m, NO en pies)
        pieces (int): Cantidad de piezas
        apply_s2s_adjustment (bool): Si aplica ajuste +1/8" en ancho (default: True)
            - True: Para madera cepillada (S2S) - Compensación por pérdida
            - False: Para madera en bruto (rough) - Dimensión real

    Returns:
        float: Volumen en m³ redondeado a 3 decimales con ROUND_HALF_UP (r3).

    Notes:
        Redondeo: usa r3() → ROUND_HALF_UP a 3 decimales (≠ Python round nativo).

    Version: 3.2.0 (2026-04-09) - Usa r3() en lugar de round() nativo
    """
    # Validaciones de entrada
    if not all([thickness_inch > 0, width_inch > 0, length_m > 0, pieces > 0]):
        _logger.warning(
            f"⚠️ Parámetros inválidos en calculate_volume_imperial_to_m3: "
            f"thickness={thickness_inch}\", width={width_inch}\", "
            f"length={length_m}m, pieces={pieces}"
        )
        return 0.0

    try:
        # Convertir a Decimal para precisión
        t_in = Decimal(str(thickness_inch))
        w_in = Decimal(str(width_inch))
        l_m = Decimal(str(length_m))
        pcs = Decimal(str(pieces))

        # Aplicar ajuste S2S si corresponde
        if apply_s2s_adjustment:
            w_adjusted = w_in + S2S_WIDTH_ADJUSTMENT_INCH
        else:
            w_adjusted = w_in

        # ✅ FÓRMULA CORRECTA (según Excel - Regla de Oro):
        # NO convertir largo a pies, usar metros directamente
        vol_m3 = (t_in * w_adjusted * l_m * pcs) / INCH_SQ_METERS_TO_M3

        # ✅ ROUND_HALF_UP via r3() — NO usar round() nativo (Banker's rounding)
        result = r3(vol_m3)

        # Log de auditoría (solo en modo debug)
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(
                f"📐 Volumen calculado: {thickness_inch}\" × {width_inch}\" "
                f"(+{0.125 if apply_s2s_adjustment else 0}\") × {length_m}m × {pieces}pzs "
                f"= {result} m³ (factor: 1550.003)"
            )

        return result

    except Exception as e:
        _logger.error(
            f"❌ Error en calculate_volume_imperial_to_m3: {e}\n"
            f"   Parámetros: t={thickness_inch}, w={width_inch}, l={length_m}, pzs={pieces}"
        )
        return 0.0




def validate_imperial_factor():
    """
    Valida el factor imperial contra casos de prueba del Excel.

    REGLA DE ORO - TESTING:
    Ejecutar en startup para garantizar integridad del cálculo.

    Returns:
        bool: True si todas las validaciones pasan

    Test Cases (del Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx):
        - Fila 1: 6/4" × 2 5/8" × 4.0m × 1pz = 0.011 m³
        - Fila 2: 6/4" × 2 7/8" × 4.0m × 1pz = 0.012 m³
        - Fila 3: 6/4" × 3 5/8" × 4.0m × 1pz = 0.015 m³
    """
    # Casos de prueba extraídos del Excel
    test_cases = [
        # (thickness_inch, width_inch, length_m, pieces, expected_m3)
        (1.5, 2.625, 4.0, 1, 0.011),  # Fila 1 Excel
        (1.5, 2.875, 4.0, 1, 0.012),  # Fila 2 Excel
        (1.5, 3.625, 4.0, 1, 0.015),  # Fila 3 Excel
        (1.5, 4.625, 4.0, 1, 0.018),  # Fila 4 Excel
    ]

    tolerance = 0.001  # Tolerancia de ±0.001 m³

    all_passed = True
    for t_in, w_in, l_m, pcs, expected in test_cases:
        result = calculate_volume_imperial_to_m3(t_in, w_in, l_m, pcs, True)
        diff = abs(result - expected)

        if diff > tolerance:
            _logger.error(
                f"❌ TEST FALLÓ: {t_in}\" × {w_in}\" × {l_m}m × {pcs}pzs\n"
                f"   Esperado: {expected} m³, Obtenido: {result} m³, Diff: {diff} m³"
            )
            all_passed = False

    # ✅ Validar S2S_WIDTH_LOOKUP: entradas críticas
    s2s_checks = {
        145: 5.375,  # VALOR CRÍTICO Excel
        110: 3.875,  # stair step (faltaba en Tabla 2)
        120: 4.375,  # stair step (faltaba en Tabla 2)
        130: 4.875,  # stair step (faltaba en Tabla 2)
    }
    for mm, expected_inch in s2s_checks.items():
        got = S2S_WIDTH_LOOKUP.get(mm)
        if got != expected_inch:
            _logger.error(
                f"❌ S2S_WIDTH_LOOKUP[{mm}mm] = {got}, esperado {expected_inch}"
            )
            all_passed = False

    # ✅ Validar calculate_volume_metric_m3
    metric_result = calculate_volume_metric_m3(45, 100, 4.0, 200)
    if abs(metric_result - 3.6) > 1e-9:
        _logger.error(
            f"❌ calculate_volume_metric_m3(45,100,4.0,200) = {metric_result}, esperado 3.6"
        )
        all_passed = False

    if all_passed:
        _logger.info("✅ REGLA DE ORO IMPERIAL: Factor 1550.003 validado correctamente")
        _logger.info(f"   Ajuste S2S: +{S2S_WIDTH_ADJUSTMENT_INCH}\" (1/8 pulgada)")
        _logger.info(f"   Redondeo: r3() ROUND_HALF_UP a 3 decimales")
        _logger.info(f"   S2S_WIDTH_LOOKUP: {len(S2S_WIDTH_LOOKUP)} entradas validadas")
        _logger.info(f"   Fuente: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx")

    return all_passed


def get_s2s_adjustment(env, width_mm):
    """
    Retorna el ajuste S2S en pulgadas para un ancho dado en mm.

    Delega en el helper centralizado madenat.ingestion.config (Fase 3)
    para la lectura de exclusiones. Fuente única de verdad.

    Args:
        env:      Odoo environment (self.env)
        width_mm: Ancho nominal en milímetros

    Returns:
        Decimal: 0.0 si el ancho está en la lista de exclusiones,
                 Decimal('0.125') en caso contrario.
    """
    # Delegar al helper centralizado (Fase 3 — cierra brecha de lectura directa)
    config = env['madenat.ingestion.config']
    exceptions = config.get_s2s_exclusion_widths()

    # Si el ancho está en la lista negra → sin recargo
    if round(width_mm, 1) in exceptions:
        return Decimal('0.0')

    return Decimal('0.125')


# ============================================================================
# 🚀 AUTO-VALIDACIÓN EN IMPORT
# ============================================================================



# Ejecutar validación automáticamente al importar el módulo
try:
    if not validate_mbf_factor():
        _logger.critical("❌ FACTOR MBF INVÁLIDO - REVISAR utils_uom.py")

    if not validate_imperial_factor():
        _logger.critical("❌ FACTOR IMPERIAL INVÁLIDO - REVISAR utils_uom.py")

except Exception as e:
    _logger.error(f"⚠️ Error en validación de factores UoM: {e}")
