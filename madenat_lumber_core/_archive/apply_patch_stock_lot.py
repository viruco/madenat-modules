import sys
from pathlib import Path

TARGET = Path("stock_lot.py")
if not TARGET.exists():
    sys.exit("No se encuentra stock_lot.py")

src = TARGET.read_text(encoding="utf-8")
changes = []

# C1 — Expandir import línea 27
old27 = "from .utils_uom import INCH_SQ_METERS_TO_M3"
new27 = "from .utils_uom import INCH_SQ_METERS_TO_M3, get_s2s_adjustment, r3, r4"
if old27 in src:
    src = src.replace(old27, new27, 1)
    changes.append("C1: import línea 27 expandido con get_s2s_adjustment, r3, r4")
else:
    changes.append("WARN C1: import línea 27 no encontrado exacto")

# C2 — Eliminar import inline línea 475
inline = "        from .utils_uom import INCH_SQ_METERS_TO_M3\n"
if inline in src:
    src = src.replace(inline, "", 1)
    changes.append("C2: import inline INCH_SQ_METERS_TO_M3 eliminado")
else:
    changes.append("WARN C2: import inline no encontrado")

# C3 — overmeasure hardcodeado → get_s2s_adjustment
old_over = "            overmeasure = 0.0 if is_std else 0.125"
new_over = "            overmeasure = 0.0 if is_std else float(get_s2s_adjustment(self.env, a_mm))"
if old_over in src:
    src = src.replace(old_over, new_over, 1)
    changes.append("C3: overmeasure 0.125 → get_s2s_adjustment(self.env, a_mm)")
else:
    changes.append("WARN C3: overmeasure hardcodeado no encontrado exacto")

# C4 — 4x round() nativo → r3()
round_replacements = [
    ("calculado = round(vol_gold, 3)",        "calculado = r3(vol_gold)"),
    ("lot.volumen_m3 = round(vol_exacto, 3)", "lot.volumen_m3 = r3(vol_exacto)"),
    ("lot.volumen_m3 = round(lot.volumen_m3, 3)",   "lot.volumen_m3 = r3(lot.volumen_m3)"),
    ("lot.volumen_mbf = round(lot.volumen_mbf, 3) ", "lot.volumen_mbf = r3(lot.volumen_mbf)"),
    ("lot.volumen_mbf = round(lot.volumen_mbf, 3)",  "lot.volumen_mbf = r3(lot.volumen_mbf)"),
]
c4_count = 0
for old, new in round_replacements:
    if old in src:
        src = src.replace(old, new, 1)
        c4_count += 1
changes.append(f"C4: {c4_count}/4 round() → r3()" if c4_count == 4
               else f"WARN C4: solo {c4_count}/4 round() reemplazados — revisar")

TARGET.write_text(src, encoding="utf-8")

print("=" * 50)
print("PATCH stock_lot.py")
print("=" * 50)
for c in changes:
    icon = "⚠️ " if c.startswith("WARN") else "✅"
    print(f"  {icon} {c}")
warns = [c for c in changes if c.startswith("WARN")]
print(f"\n{'🚀' if not warns else '🔧'} {len(changes)-len(warns)} OK / {len(warns)} advertencias")
