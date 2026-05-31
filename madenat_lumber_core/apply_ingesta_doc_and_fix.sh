#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-$(pwd)}"

DOC_CONT="$BASE/docs/02_CONTINUIDAD.md"
DOC_ARCH="$BASE/docs/00_ARQUITECTURA.md"
SUBP="$BASE/models/madenat_subproducto.py"

ts="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BASE/.bak/$ts"

need_file() {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "ERROR: no existe $f"
    exit 1
  fi
}

backup() {
  local f="$1"
  cp "$f" "$BASE/.bak/$ts/$(basename "$f").bak"
}

need_file "$DOC_CONT"
need_file "$DOC_ARCH"
need_file "$SUBP"

echo "==> Base detectada: $BASE"
echo "==> Respaldando archivos"
backup "$DOC_CONT"
backup "$DOC_ARCH"
backup "$SUBP"

echo "==> Corrigiendo models/madenat_subproducto.py"
cat > "$SUBP" <<'PY'
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MadenatSubproducto(models.Model):
    _name = 'madenat.subproducto'
    _description = 'Catálogo de Sub-productos MADENAT'
    _order = 'sequence, name'

    name = fields.Char('Nombre', required=True, help="Ej: BLANK CLEAR, BLANK PANELEADO")
    code = fields.Char('Código', required=True, help="Código corto para reportes")
    description = fields.Text('Descripción')
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean('Activo', default=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código del sub-producto debe ser único'),
        ('name_unique', 'UNIQUE(name)', 'El nombre del sub-producto debe ser único'),
    ]

    @api.constrains('code')
    def check_code_format(self):
        """Validar formato del código."""
        for record in self:
            if record.code and not record.code.replace(' ', '').replace('-', '').isalnum():
                raise ValidationError(
                    _('El código debe contener solo letras, números, espacios y guiones.')
                )
PY

echo "==> Insertando documentación en docs/02_CONTINUIDAD.md"
python3 - <<'PY' "$DOC_CONT"
from pathlib import Path
import sys

path = Path(sys.argv[1])
txt = path.read_text(encoding="utf-8")

block = """
---

## DECISIÓN TÉCNICA 2026-05-13 - INGESTA Y UNIDADES DE LARGO

### Contexto
Se detectó una fuente de confusión funcional al mezclar la selección de perfil de ingesta con la interpretación del campo largo en `lumber.reception.line`.
La ingesta no debe pensarse solo como "métrico vs imperial", sino como perfiles de cálculo con semántica propia.

### Perfiles relevantes confirmados
- `metric`
- `s2s`
- `blanks`
- `f1550`
- `f5085`

### Regla de diseño
- El perfil de ingesta define la semántica del cálculo.
- `metric` usa lógica métrica.
- `s2s` tiene reglas propias de negocio y no debe asumirse equivalente a `metric` sin revisar fórmula.
- `blanks` convive con reglas específicas y debe mantenerse aislado para no contaminar otros cálculos.
- `f1550` y `f5085` son reglas volumétricas específicas ya validadas en la matriz de pruebas.
- Antes de introducir cambios al campo largo o a nuevas unidades, se debe mapear primero qué fórmula usa cada perfil.

### Consecuencia práctica
No implementar cambios de `length`, `length_m`, `length_raw`, `length_uom` o selector de unidades sin:
1. revisar el perfil de ingesta real usado por la línea;
2. identificar la fórmula aplicable;
3. validar convivencia con `Standard Blanks`;
4. actualizar tests y documentación.

### Estado
Pendiente de implementación controlada.
Decisión aprobada: documentar primero y luego aplicar solución mínima.
"""

if "## DECISIÓN TÉCNICA 2026-05-13 - INGESTA Y UNIDADES DE LARGO" not in txt:
    txt = txt.rstrip() + "\n" + block + "\n"
    path.write_text(txt, encoding="utf-8")
PY

echo "==> Insertando nota de arquitectura en docs/00_ARQUITECTURA.md"
python3 - <<'PY' "$DOC_ARCH"
from pathlib import Path
import sys

path = Path(sys.argv[1])
txt = path.read_text(encoding="utf-8")

insert = """

## Nota 2026-05-13 - Perfiles de ingesta y largo

- La interpretación del campo largo en staging depende del perfil de ingesta.
- `metric`, `s2s`, `blanks`, `f1550` y `f5085` no deben tratarse como equivalentes.
- Cualquier cambio en unidades de largo debe nacer desde el mapeo de perfiles y fórmulas, no desde la UI.
- La convivencia `Standard Blanks` y otras reglas ya fue validada en tests y no debe contaminarse por refactors apresurados.
"""

if "## Nota 2026-05-13 - Perfiles de ingesta y largo" not in txt:
    txt = txt.rstrip() + "\n" + insert + "\n"
    path.write_text(txt, encoding="utf-8")
PY

echo "==> Limpiando pycache local"
find "$BASE" -type d -name "__pycache__" -exec rm -rf {} +

echo
echo "OK"
echo "Base: $BASE"
echo "Backups: $BASE/.bak/$ts"
echo "Archivos tocados:"
echo " - $SUBP"
echo " - $DOC_CONT"
echo " - $DOC_ARCH"