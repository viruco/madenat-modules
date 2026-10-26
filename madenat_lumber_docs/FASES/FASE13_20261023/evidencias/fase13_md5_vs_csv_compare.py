#!/usr/bin/env python3
"""Comparacion SOLO LECTURA: CSV congelado (evidencias 2B) vs volcado vivo de madenat_test.

No escribe en la BD ni en el repositorio: lee dos CSV congelados del propio directorio
`evidencias/` y reporta diferencias por registro y por columna. Las rutas son relativas
al archivo (consolidacion FASE 2/E3), por lo que el script funciona en cualquier clon.
"""
import csv
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

PAIRS = [
    (
        "lumber_reception_line",
        os.path.join(BASE, "reception_lines.csv"),
        os.path.join(BASE, "live_lines_raw.csv"),
        [
            "id", "lot_name", "export_calculation_rule", "thickness_nominal",
            "width_nominal", "length_nominal", "pieces", "vol_purchase_m3",
            "vol_shipment_m3", "vol_mbf", "board_feet",
        ],
    ),
    (
        "stock_lot",
        os.path.join(BASE, "stock_lots.csv"),
        os.path.join(BASE, "live_lots_raw.csv"),
        [
            "id", "name", "espesor_mm", "ancho_mm", "largo_m", "piezas",
            "volumen_m3", "vol_shipment_m3", "volumen_mbf",
            "volume_purchase_m3", "reception_id",
        ],
    ),
]


def read_csv(path, has_header):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.reader(fh) if r]
    if has_header:
        header, rows = rows[0], rows[1:]
    else:
        header = None
    return header, rows


def compare(model, frozen_path, live_path, columns):
    header, frozen = read_csv(frozen_path, True)
    _, live = read_csv(live_path, False)
    print(f"\n=== {model} ===")
    print(f"registros congelado={len(frozen)} vivo={len(live)} "
          f"cabecera_ok={header == columns}")
    frozen_ids = [r[0] for r in frozen]
    live_ids = [r[0] for r in live]
    print(f"ids: faltan_en_vivo={sorted(set(frozen_ids) - set(live_ids))} "
          f"nuevos_en_vivo={sorted(set(live_ids) - set(frozen_ids))} "
          f"mismo_orden={frozen_ids == live_ids}")
    print(f"{'columna':<24}{'iguales':>9}{'distintas':>11}  primeras diferencias")
    total_diff = 0
    for idx, col in enumerate(columns):
        same = 0
        diffs = []
        for fr, lr in zip(frozen, live):
            if fr[idx] == lr[idx]:
                same += 1
            else:
                diffs.append(f"id={fr[0]} {fr[idx]!r}->{lr[idx]!r}")
        total_diff += len(diffs)
        sample = ", ".join(diffs[:3]) if diffs else "-"
        print(f"{col:<24}{same:>9}{len(diffs):>11}  {sample}")
    print(f"TOTAL celdas distintas: {total_diff} de {len(frozen) * len(columns)}")
    return total_diff


def main():
    total = 0
    for model, frozen, live, columns in PAIRS:
        total += compare(model, frozen, live, columns)
    print(f"\nRESULTADO GLOBAL: {total} celdas distintas")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
