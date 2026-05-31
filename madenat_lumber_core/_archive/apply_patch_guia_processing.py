import re, sys
from pathlib import Path

TARGET = Path("madenat_guia_processing.py")
if not TARGET.exists():
    sys.exit("No se encuentra madenat_guia_processing.py")

src = TARGET.read_text(encoding="utf-8")
changes = []

# C1 — Import línea 18 suelta → eliminar
old18 = "from .utils_uom import get_s2s_adjustment\n"
if old18 in src:
    src = src.replace(old18, "", 1)
    changes.append("C1a: import línea 18 eliminado")

# C1b — Expandir import línea 63
old63 = "from .utils_uom import MBF_TO_M3, m3_to_mbf, mbf_to_m3, r3, r4"
new63 = "from .utils_uom import (\n    INCH_SQ_METERS_TO_M3,\n    MBF_TO_M3,\n    S2S_WIDTH_LOOKUP,\n    calculate_volume_metric_m3,\n    get_s2s_adjustment,\n    m3_to_mbf,\n    mbf_to_m3,\n    r3,\n    r4,\n)"
if old63 in src:
    src = src.replace(old63, new63, 1)
    changes.append("C1b: import línea 63 expandido")
else:
    changes.append("WARN C1b: import línea 63 no encontrado exacto")

# C1c — 5 imports inline (con y sin espacio trailing)
for pattern in [
    "        from .utils_uom import get_s2s_adjustment\n",
    "        from .utils_uom import get_s2s_adjustment \n",
]:
    count = src.count(pattern)
    if count:
        src = src.replace(pattern, "")
        changes.append(f"C1c: {count} import(s) inline eliminado(s)")

# C2a — FACTOR_METROS local
for old in ["        FACTOR_METROS = 1550.003\n", "        FACTOR_METROS = 1550.003096\n"]:
    if old in src:
        src = src.replace(old, "", 1)
        changes.append("C2a: FACTOR_METROS local eliminado")

# C2b — 2x fórmulas con / 1550.003 directo
old_formula = "vol_m3 = (pzas * e_pulg * a_pulg * l_m) / 1550.003"
new_formula = ("vol_m3 = float(\n"
               "                            Decimal(str(pzas))\n"
               "                            * Decimal(str(e_pulg))\n"
               "                            * Decimal(str(a_pulg))\n"
               "                            * Decimal(str(l_m))\n"
               "                            / INCH_SQ_METERS_TO_M3\n"
               "                        )")
count = src.count(old_formula)
if count:
    src = src.replace(old_formula, new_formula)
    changes.append(f"C2b: {count}x / 1550.003 → INCH_SQ_METERS_TO_M3 Decimal")
else:
    changes.append("WARN C2b: fórmula / 1550.003 no encontrada")

# C2c — Decimal importado
if "from decimal import" not in src:
    src = src.replace("import logging", "import logging\nfrom decimal import Decimal, ROUND_HALF_UP", 1)
    changes.append("C2c: from decimal import Decimal agregado")

# C3 — 5x / 1_000_000 → calculate_volume_metric_m3
m3_replacements = [
    (
        "rec.vol_purchase_m3 = esp * anc * largo * rec.pieces / 1_000_000.0",
        "rec.vol_purchase_m3 = calculate_volume_metric_m3(esp, anc, largo, rec.pieces)"
    ),
    (
        "rec.vol_purchase_m3 = esp * anc * largo * rec.pieces / 1000000.0",
        "rec.vol_purchase_m3 = calculate_volume_metric_m3(esp, anc, largo, rec.pieces)"
    ),
    (
        "rec.vol_physical_m3 = rec.espesor_mm * rec.ancho_mm * rec.largo_m * rec.pieces / 1_000_000.0",
        "rec.vol_physical_m3 = calculate_volume_metric_m3(rec.espesor_mm, rec.ancho_mm, rec.largo_m, rec.pieces)"
    ),
    (
        "rec.vol_physical_m3 = rec.espesor_mm * rec.ancho_mm * rec.largo_m * rec.pieces / 1000000.0",
        "rec.vol_physical_m3 = calculate_volume_metric_m3(rec.espesor_mm, rec.ancho_mm, rec.largo_m, rec.pieces)"
    ),
    (
        "vol_m3 = (pzas * e_mm * a_mm * l_m) / 1000000.0",
        "vol_m3 = calculate_volume_metric_m3(e_mm, a_mm, l_m, pzas)"
    ),
    (
        "vol_m3 = (pzas * e_mm * a_mm * l_m) / 1_000_000.0",
        "vol_m3 = calculate_volume_metric_m3(e_mm, a_mm, l_m, pzas)"
    ),
]
c3_count = 0
for old, new in m3_replacements:
    if old in src:
        src = src.replace(old, new)
        c3_count += 1
if c3_count:
    changes.append(f"C3: {c3_count}x / 1_000_000 → calculate_volume_metric_m3")
else:
    changes.append("WARN C3: /1_000_000 no encontrados con texto exacto — ver grep manual")

# C4 — round() volumen → r3  (NO tocar round de fracciones)
old_round = "calculated_vol = round(vol, 3)"
if old_round in src:
    src = src.replace(old_round, "calculated_vol = r3(vol)", 1)
    changes.append("C4: calculated_vol = round(vol,3) → r3(vol)")
else:
    changes.append("WARN C4: calculated_vol = round(vol,3) no encontrado")

# C5 — comparación Decimal==float
old_cmp = "get_s2s_adjustment(self.env, physical_mm) == 0.0"
if old_cmp in src:
    src = src.replace(old_cmp, "float(get_s2s_adjustment(self.env, physical_mm)) == 0.0", 1)
    changes.append("C5: comparación Decimal==float corregida")

TARGET.write_text(src, encoding="utf-8")

print("=" * 55)
print("PATCH madenat_guia_processing.py")
print("=" * 55)
for c in changes:
    icon = "⚠️ " if c.startswith("WARN") else "✅"
    print(f"  {icon} {c}")
warns = [c for c in changes if c.startswith("WARN")]
print(f"\n{'🚀' if not warns else '🔧'} {len(changes)-len(warns)} OK / {len(warns)} advertencias")
