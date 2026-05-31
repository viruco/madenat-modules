import re, sys
from pathlib import Path

TARGET = Path("lumber_reception.py")
if not TARGET.exists():
    sys.exit("No se encuentra lumber_reception.py")

src = TARGET.read_text(encoding="utf-8")
changes = []

# C1 — Imports
OLD1 = "from .utils_uom import calculate_volume_imperial_to_m3"
NEW1 = "from .utils_uom import (\n    INCH_SQ_METERS_TO_M3,\n    S2S_WIDTH_LOOKUP,\n    calculate_volume_imperial_to_m3,\n    calculate_volume_metric_m3,\n    get_s2s_adjustment,\n    r3,\n    r4,\n)"
src = src.replace(OLD1, NEW1, 1) ; changes.append("C1a imports bloque")
src = src.replace("from .utils_uom import get_s2s_adjustment\n", "", 1) ; changes.append("C1b import suelto eliminado")

# C2 — Constantes locales
src = src.replace("        FACTOR_1550 = 1550.003\n", "", 1) ; changes.append("C2a FACTOR_1550 eliminado")
src = src.replace("        RECARGO_S2S = 0.125  # 1/8 de pulgada\n", "", 1) ; changes.append("C2b RECARGO_S2S eliminado")

# C3 — RECARGO_S2S en cálculo
OLD3 = "                w_calc = w_in + RECARGO_S2S if w_in > 0 else 0.0"
NEW3 = "                _width_mm = line.width_nominal or line.width or 0.0\n                _s2s = float(get_s2s_adjustment(self.env, _width_mm))\n                w_calc = w_in + _s2s if w_in > 0 else 0.0"
src = src.replace(OLD3, NEW3, 1) ; changes.append("C3 RECARGO_S2S → get_s2s_adjustment")

# C4 — FACTOR_1550 en fórmula
OLD4 = "                        vol_exp = (t_in * w_calc * l_m * qty) / FACTOR_1550"
NEW4 = "                        vol_exp = float(\n                            Decimal(str(t_in))\n                            * Decimal(str(w_calc))\n                            * Decimal(str(l_m))\n                            * Decimal(str(qty))\n                            / INCH_SQ_METERS_TO_M3\n                        )"
src = src.replace(OLD4, NEW4, 1) ; changes.append("C4 FACTOR_1550 → INCH_SQ_METERS_TO_M3")
if "from decimal import" not in src:
    src = src.replace("import logging", "import logging\nfrom decimal import Decimal, ROUND_HALF_UP", 1) ; changes.append("C4b Decimal importado")

# C5 — 4x /1_000_000
src = src.replace("            vol = (line.thickness * line.width * line.length * line.pieces) / 1_000_000.0", "            vol = calculate_volume_metric_m3(\n                line.thickness, line.width, line.length, line.pieces\n            )", 1) ; changes.append("C5a vol /1_000_000")
src = src.replace("            raw_vol = (line.thickness * line.width * l * (line.pieces or 0.0)) / 1000000.0", "            raw_vol = calculate_volume_metric_m3(\n                line.thickness, line.width, l, line.pieces or 0\n            )", 1) ; changes.append("C5b raw_vol /1000000")
src = src.replace("                        vol_exp = (thickness_mm * width_mm * l_m * qty) / 1000000.0", "                        vol_exp = calculate_volume_metric_m3(\n                            thickness_mm, width_mm, l_m, qty\n                        )", 1) ; changes.append("C5c metric /1000000")
src = src.replace("            vol_m3 = (t_calc * w_calc * l_calc * line.pieces) / 1_000_000.0", "            vol_m3 = calculate_volume_metric_m3(t_calc, w_calc, l_calc, line.pieces)", 1) ; changes.append("C5d vol_m3 /1_000_000")

# C6 — round() nativo
src = src.replace("                    else: t_val = round((t_mm / 25.4) * 4) / 4.0", "                    else: t_val = r4((t_mm / 25.4) * 4) / 4.0", 1) ; changes.append("C6a t_val round → r4")
src = src.replace("                rec.volume_variance_percent = round(variance, 4)", "                rec.volume_variance_percent = r4(variance)", 1) ; changes.append("C6b variance_percent → r4")
src = src.replace("                rec.volume_variance_m3 = round(rec.physical_volume_m3 - rec.commercial_volume_m3, 3)", "                rec.volume_variance_m3 = r3(\n                    rec.physical_volume_m3 - rec.commercial_volume_m3\n                )", 1) ; changes.append("C6c variance_m3 → r3")

# C7 — Eliminar _get_s2s_width_float
match = re.search(r"    def _get_s2s_width_float\(self, value_mm\):.*?(?=\n    # ={10,}|\n    def |\n    @)", src, re.DOTALL)
if match:
    src = src[:match.start()] + src[match.end():]
    changes.append("C7 _get_s2s_width_float eliminado")

TARGET.write_text(src, encoding="utf-8")
print("\n".join(f"  ✅ {c}" for c in changes))
print(f"\n🚀 {len(changes)} cambios aplicados")
