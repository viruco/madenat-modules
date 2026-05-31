#!/usr/bin/env bash
set -euo pipefail

BASE="$(pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
BAK="$BASE/.bak/$TS"
mkdir -p "$BAK"

LUMBER_RECEPTION="$BASE/models/lumber_reception.py"
WIZARD_MODEL="$BASE/wizard/lumber_reception_mass_update.py"
TEST_LENGTH="$BASE/tests/test_length_uom_and_subproducto.py"

for f in "$LUMBER_RECEPTION" "$WIZARD_MODEL" "$TEST_LENGTH"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: no existe $f"
    exit 1
  fi
  cp "$f" "$BAK/"
done

python3 <<'PY'
from pathlib import Path

base = Path.cwd()
lumber = base / "models" / "lumber_reception.py"

text = lumber.read_text(encoding="utf-8")

if "def _compute_lengthm(" in text:
    print("OK: _compute_lengthm ya existe, no se duplica.")
else:
    if "lengthm = fields.Float(" in text:
        print("OK: campo lengthm ya existe, faltan métodos o ya fueron agregados.")
    else:
        anchor = "    lengthinputraw = fields.Float("
        idx = text.find(anchor)
        if idx == -1:
            raise SystemExit("No encontré ancla lengthinputraw en models/lumber_reception.py")

        end = text.find("\n\n", idx)
        if end == -1:
            raise SystemExit("No pude determinar fin de bloque de lengthinputraw")

        insertion = """

    lengthm = fields.Float(
        string='Largo convertido m',
        compute='_compute_lengthm',
        store=True,
        digits=(10, 4),
        help='Largo normalizado a metros para cálculos y validaciones.'
    )"""
        text = text[:end] + insertion + text[end:]

    compute_anchor = "    boardfeet = fields.Float("
    pos = text.find(compute_anchor)
    if pos == -1:
        raise SystemExit("No encontré ancla boardfeet en models/lumber_reception.py")

    methods = """
    @api.depends('lengthinputraw', 'lengthuom', 'length')
    def _compute_lengthm(self):
        for rec in self:
            raw = rec.lengthinputraw if rec.lengthinputraw not in (False, None) else 0.0
            if raw:
                if rec.lengthuom == 'ft':
                    rec.lengthm = round(raw * 0.3048, 6)
                elif rec.lengthuom == 'mm':
                    rec.lengthm = round(raw * 0.001, 6)
                else:
                    rec.lengthm = raw
            else:
                rec.lengthm = rec.length or 0.0

    @api.onchange('lengthinputraw', 'lengthuom')
    def _onchange_length_input_to_length(self):
        for rec in self:
            if rec.lengthinputraw:
                if rec.lengthuom == 'ft':
                    rec.length = round(rec.lengthinputraw * 0.3048, 6)
                elif rec.lengthuom == 'mm':
                    rec.length = round(rec.lengthinputraw * 0.001, 6)
                else:
                    rec.length = rec.lengthinputraw

"""
    text = text[:pos] + methods + text[pos:]
    lumber.write_text(text, encoding="utf-8")
    print("OK: models/lumber_reception.py actualizado.")

print("PATCH_DONE")
PY

find "$BASE" -type d -name "__pycache__" -exec rm -rf {} + >/dev/null 2>&1 || true

echo "OK"
echo "Backups en: $BAK"
