#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cuarentena reversible de carpetas de fase — FASE 4 (2026-10-26).

Mueve carpetas de la raíz del stack a `.pendiente_borrado_20261026/` con
`os.rename` (mismo sistema de archivos: no copia, no borra). Antes de cada
movimiento verifica cuatro condiciones y ABORTA esa carpeta si alguna falla:

  1. el `.tar.gz` de D7 existe, no está vacío y su sha256 coincide con el CSV;
  2. el contenido del `.tar.gz` coincide con el original (rutas y bytes);
  3. ningún proceso del host tiene abiertos archivos de la carpeta;
  4. la carpeta no es origen de un bind mount de un contenedor Docker.

Modos:
  (por defecto) --dry-run   no mueve nada; verifica y muestra el plan.
  --ejecutar                ejecuta los movimientos y escribe el diario.
  --revertir                devuelve al origen lo registrado en el diario.

Uso:
  python3 00_CUARENTENA_20261026.py                     # simulación A+B
  python3 00_CUARENTENA_20261026.py --tanda A           # solo tanda A
  python3 00_CUARENTENA_20261026.py --ejecutar --tanda A
  python3 00_CUARENTENA_20261026.py --revertir --ejecutar
  python3 00_CUARENTENA_20261026.py --excluir appointment_crm

Salida: una línea por carpeta (APTA / EXCLUIDA / ERROR + motivo) y un resumen.
Código de salida: 0 si todo verificó; 2 si alguna carpeta quedó bloqueada.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

RAIZ = "/home/viruco/dev-stack/odoo/odoo-18-ce"
CUARENTENA = os.path.join(RAIZ, ".pendiente_borrado_20261026")
BACKUPS = "/home/viruco/dev-stack/backups/consolidacion_20261026"
CSV_D7 = os.path.join(
    RAIZ, "custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/"
          "evidencias/SHA256_BACKUPS_CONSOLIDACION.csv")
DIARIO = os.path.join(CUARENTENA, "_diario.jsonl")

# Excluidas por evidencia (FASE 4, punto 2): NUNCA se mueven.
EXCLUIDAS_FIJAS = {
    "config": "dependencia viva: bind mount ./config -> /etc/odoo en "
              "docker-compose.yml y --config /etc/odoo/odoo.conf en odoo18_app",
}

# Aprobadas pero condicionadas a un arreglo pendiente (se excluyen salvo
# --incluir-postergadas).
POSTERGADAS = {
    "FASE12_REQUERIMIENTOS_OPERACIONES_20261017":
        "run_regression.sh:11 escribe sus logs aquí (fix propuesto, no "
        "aplicado); moverla haría que el script recree la carpeta en la ruta "
        "vieja",
}

# Tanda A — no citadas en CANON/, WIKI/ ni RAW/ (59 carpetas, 484.9 MB).
TANDA_A = [
    "FIX_GUIA_DUP_FINAL_20261007_171740", "FIX_GUIA_DUP_CIERRE_20261007_170340",
    "FIX_GUIA_DUP_20261007_164415", "incident_recovery_audit",
    "REDISENO_REGISTRAR_REBAJA_20261010", "IMPL_SV_REBAJA_OPERATIVA_20261010",
    "FIX_SV_SELECCIONAR_TODAS_20261010", "FIX_ACL_GUIA_20261007_1630",
    "FASE5_COMMITS_20261015", "FIX_DELETE_INTAKE_20261007_145130",
    "oracle_f31_20261003_165538", "madenat_dev_p0r_20261003",
    "pre02_test_20261003_1541", "pre02_postcommit_test_20261003_173746",
    "f31_test_20261003_1410", "pre02_isolated_20261003",
    "AUDIT_DELETE_INTAKE_20261007_130559", "HOTFIX_OWL_COLUMN_INVISIBLE_20261010",
    "_archive_pre_cleanup_20261003", "UI_LIMPIA_SV_20261010",
    "DIAGNOSTICO_SV000000841_20261012", "pre02_audit",
    "IMPL_SEC_RECEPCION_20261004", "oracle_f31_audit",
    "IMPL_DELIVER_D2_20261004", "IMPL_B01_20261004", "UAT_R2_20261004",
    "IMPL_DELIVER_D2_C1_20261004", "_archive_pre_cleanup_20260822",
    "UAT_DELIVER_D2_20261004", "UAT_ROLLEO_EMBARQUE_20261005",
    "FASE_B_20261007_153214", "pre02_formalization_audit",
    "backups_provider_total_20260821_094139",
    "backups_20260821_20260821_091540", "backups_fix_proveedor_20260821_102851",
    "ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012", "CIERRE_E1_20261005",
    "UAT_B01_20261004", "UAT_INTAKE_20261004", "UAT_DRAFT_20261004",
    "UAT_R1_20261004", "FASE_C_20261007_154556", "AUDIT_R2_20261004",
    "AUDIT_BUSQUEDA_FILTROS_INTAKE_20261007", "FASE_D_20261007_155057",
    "AUDIT_COSTING_20261004", "UAT_COSTING_C2_20261004", "UAT_VR_20261004",
    "AUDIT_DELIVER_20261004", "backups_20260821_20260821_092634",
    "AUDIT_GUIA_DUPLICADOS_20261007", "UAT_INT_20261003",
    "FASE9_VERIFICACION_REMOTO_20261015", "pre02_publish_audit",
    "pre02_isolated_audit", "madenat_dev_audit_20261003",
    "appointment_crm", "postgresql.conf",
]

# Tanda B — citadas al menos una vez (E8 ya reescribió las citas). 35 carpetas.
TANDA_B = [
    "AUDITORIA_INTEGRAL_20261012", "BACKUP_AB_APPLY_20261008",
    "CONCILIACION_ENVIO_RETORNO_20261010", "AUDIT_REBAJA_ETIQUETAS_20261011",
    "FASE12_REQUERIMIENTOS_OPERACIONES_20261017", "INCIDENTE_GUIA_15183_20261007",
    "APPLY_AB_UI_20261008", "BLINDAJE_SOBRESCRITURA_20261012",
    "BLINDAJE_REBAJA_LOCAL_20261012", "VERIF_CUATRO_PUNTOS_20261012",
    "CIERRE_SOBRESCRITURA_V123_20261012", "APPLY_BUSQUEDA_INTAKE_20261007",
    "FASE11_INTEGRIDAD_CICLO_IMPUTACIONES_20261015", "FASE7_CIERRE_D18_20261015",
    "FASE8_CIERRE_DR_20261015", "FASE10_REBAJA_SV_ETIQUETAS_20261015",
    "IMPL_ASSIGN_SV_20261010_165247", "UNIFY_SV_REBAJA_MENU_20261010",
    "SAVE_REBAJA_20261011", "RESET_REBAJA_20261011", "SIMPLE_REBAJA_20261011",
    "UI_SAVE_REBAJA_20261011", "CIERRE_PENDIENTES_20261010",
    "HOTFIX_OWL_CHATTER_OE_20261012", "IMPL_SERVICE_RETURN_20261006",
    "IMPL_SERVICE_RETURN_AB_20261007", "IMPL_BUSQUEDA_INTAKE_20261007",
    "FASE6_HEAD_CHECK_20261015", "CONTRATO_APLICACION_20261011",
    "FASE13_INTAKE_ENGINE_20261023",
    "AUDITORIA_DISPONIBILIDAD_ETIQUETAS_20261015",
    "AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015",
    "DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015",
    "AUDIT_B01_20261004", "config",
]


# ── utilidades ───────────────────────────────────────────────────────────────

def sha256_texto(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def manifiesto_local(ruta):
    """(archivos, bytes, sha256) del contenido de una carpeta, sin seguir enlaces."""
    entradas = []
    for base, dirs, files in os.walk(ruta):
        dirs.sort()
        for nombre in sorted(files):
            p = os.path.join(base, nombre)
            if os.path.islink(p):
                continue
            entradas.append((os.path.relpath(p, ruta), os.path.getsize(p)))
    entradas.sort()
    texto = "\n".join(f"{r}\t{s}" for r, s in entradas)
    return len(entradas), sum(s for _, s in entradas), sha256_texto(texto)


def manifiesto_tar(ruta_tar, prefijo):
    """(archivos, bytes, sha256) de los ficheros regulares dentro del .tar.gz."""
    entradas = []
    with tarfile.open(ruta_tar, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            nombre = m.name
            if nombre.startswith(prefijo + "/"):
                nombre = nombre[len(prefijo) + 1:]
            entradas.append((nombre, m.size))
    entradas.sort()
    texto = "\n".join(f"{r}\t{s}" for r, s in entradas)
    return len(entradas), sum(s for _, s in entradas), sha256_texto(texto)


def procesos_abiertos(ruta):
    """Procesos del host con cwd/exe/descriptor dentro de la carpeta."""
    objetivo = os.path.realpath(ruta) + os.sep
    encontrados = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        for sub in ("cwd", "exe"):
            try:
                destino = os.readlink("/proc/%s/%s" % (pid, sub))
            except OSError:
                continue
            if destino.startswith(objetivo):
                encontrados.append("%s:%s" % (pid, sub))
        fd_dir = "/proc/%s/fd" % pid
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            try:
                destino = os.readlink(os.path.join(fd_dir, fd))
            except OSError:
                continue
            if destino.startswith(objetivo):
                encontrados.append("%s:fd/%s" % (pid, fd))
    return encontrados


def montajes_docker():
    """Rutas del host que algún contenedor tiene montadas (bind/volume)."""
    fuentes = set()
    try:
        ps = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True,
                            timeout=30)
        if ps.returncode != 0:
            return fuentes, ps.stderr.strip() or "docker ps falló"
        for cid in ps.stdout.split():
            det = subprocess.run(
                ["docker", "inspect", "--format",
                 "{{range .Mounts}}{{.Source}}\n{{end}}", cid],
                capture_output=True, text=True, timeout=30)
            for linea in det.stdout.splitlines():
                if linea.strip():
                    fuentes.add(os.path.realpath(linea.strip()))
    except (OSError, subprocess.SubprocessError) as exc:
        return fuentes, str(exc)
    return fuentes, None


def sha256_fichero(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_csv_d7():
    datos = {}
    with open(CSV_D7, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            if fila.get("tipo") == "tar.gz-carpeta":
                datos[fila["nombre"]] = fila
    return datos


# ── verificación previa ─────────────────────────────────────────────────────

def verificar(nombre, montajes, csv_d7, sha_tar=True):
    """Devuelve (datos, motivos). `motivos` vacío ⇒ apta para cuarentena."""
    ruta = os.path.join(RAIZ, nombre)
    tarp = os.path.join(BACKUPS, nombre + ".tar.gz")
    motivos = []
    if not os.path.isdir(ruta):
        return None, ["no existe la carpeta %s" % ruta]
    if not (os.path.isfile(tarp) and os.path.getsize(tarp) > 0):
        return None, ["falta el .tar.gz %s" % tarp]

    real = os.path.realpath(ruta)
    for fuente in montajes:
        if fuente == real or fuente.startswith(real + os.sep):
            motivos.append("origen de bind mount de contenedor: %s" % fuente)

    abiertos = procesos_abiertos(ruta)
    if abiertos:
        motivos.append("archivos abiertos por procesos: %s" % ", ".join(abiertos[:5]))

    fila = csv_d7.get(nombre)
    if not fila:
        motivos.append("sin fila en SHA256_BACKUPS_CONSOLIDACION.csv")

    n_local, b_local, sha_local = manifiesto_local(ruta)
    try:
        n_tar, b_tar, sha_tar_lista = manifiesto_tar(tarp, nombre)
    except (tarfile.TarError, OSError) as exc:
        return None, [".tar.gz ilegible: %s" % exc]
    if sha_local != sha_tar_lista:
        motivos.append("contenido distinto al .tar.gz: local %d arch./%d B vs tar %d arch./%d B"
                       % (n_local, b_local, n_tar, b_tar))

    datos = {
        "nombre": nombre,
        "origen": ruta,
        "tar": tarp,
        "archivos": n_local,
        "bytes": b_local,
        "manifiesto_sha256": sha_local,
        "tar_archivos": n_tar,
        "tar_bytes": b_tar,
    }
    if fila:
        if (int(fila["archivos_original"]), int(fila["bytes_original"])) != (n_local, b_local):
            motivos.append("conteo/bytes difieren del CSV D7: %d arch./%d B vs %s/%s"
                           % (n_local, b_local, fila["archivos_original"],
                              fila["bytes_original"]))
        if sha_tar:
            huella = sha256_fichero(tarp)
            datos["tar_sha256"] = huella
            if huella != fila["sha256"]:
                motivos.append("sha256 del .tar.gz no coincide con el CSV D7")
    return datos, motivos


def mover(datos):
    """Mueve la carpeta y registra la operación en el diario (append-only)."""
    os.makedirs(CUARENTENA, exist_ok=True)
    destino = os.path.join(CUARENTENA, datos["nombre"])
    if os.path.exists(destino):
        raise RuntimeError("el destino ya existe: %s" % destino)
    os.rename(datos["origen"], destino)
    entrada = dict(datos)
    entrada["destino"] = destino
    entrada["fecha"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    with open(DIARIO, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return entrada


def revertir(ejecutar):
    """Devuelve al origen lo registrado en el diario, verificando el manifiesto."""
    if not os.path.isfile(DIARIO):
        print("No hay diario en %s: nada que revertir." % DIARIO)
        return 0
    with open(DIARIO, encoding="utf-8") as fh:
        entradas = [json.loads(linea) for linea in fh if linea.strip()]
    problemas = 0
    for e in reversed(entradas):
        destino, origen = e["destino"], e["origen"]
        if not os.path.isdir(destino):
            print("[OMITIDA]   %-45s no está en cuarentena" % e["nombre"])
            continue
        if os.path.exists(origen):
            print("[BLOQUEADA] %-45s ya existe en el origen" % e["nombre"])
            problemas += 1
            continue
        n, b, sha = manifiesto_local(destino)
        if sha != e["manifiesto_sha256"]:
            print("[BLOQUEADA] %-45s manifiesto distinto al registrado" % e["nombre"])
            problemas += 1
            continue
        if not ejecutar:
            print("[DRY-RUN]   %-45s devolvería a %s (%d arch., %d B)"
                  % (e["nombre"], origen, n, b))
            continue
        os.rename(destino, origen)
        print("[REVERTIDA] %-45s %d archivos, %d B" % (e["nombre"], n, b))
    return 2 if problemas else 0


# ── principal ───────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Cuarentena reversible de carpetas de fase (FASE 4).")
    ap.add_argument("--tanda", choices=["A", "B", "AB"], default="AB")
    ap.add_argument("--ejecutar", action="store_true",
                    help="mueve de verdad (por defecto solo simula)")
    ap.add_argument("--revertir", action="store_true",
                    help="devuelve al origen lo registrado en el diario")
    ap.add_argument("--excluir", action="append", default=[],
                    help="carpeta extra a excluir (repetible)")
    ap.add_argument("--incluir-postergadas", action="store_true",
                    help="incluye las condicionadas a un arreglo pendiente")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sin-sha256-tar", action="store_true",
                    help="omite el sha256 de los .tar.gz (más rápido)")
    args = ap.parse_args(argv)

    if args.revertir:
        return revertir(args.ejecutar)

    lista = []
    if "A" in args.tanda:
        lista += TANDA_A
    if "B" in args.tanda:
        lista += TANDA_B
    lista = list(dict.fromkeys(lista))

    csv_d7 = leer_csv_d7()
    montajes, aviso = montajes_docker()
    modo = "EJECUCIÓN" if args.ejecutar else "DRY-RUN"

    print("=" * 78)
    print("CUARENTENA (%s) — tanda %s — %d candidatas" % (modo, args.tanda, len(lista)))
    print("Origen : %s" % RAIZ)
    print("Destino: %s" % CUARENTENA)
    print("Montajes de contenedor considerados: %d" % len(montajes))
    if aviso:
        print("AVISO docker: %s" % aviso)
    print("=" * 78)

    excluidas, a_verificar = [], []
    for nombre in lista:
        if nombre in EXCLUIDAS_FIJAS:
            excluidas.append((nombre, EXCLUIDAS_FIJAS[nombre]))
        elif nombre in POSTERGADAS and not args.incluir_postergadas:
            excluidas.append((nombre, "postergada: " + POSTERGADAS[nombre]))
        elif nombre in args.excluir:
            excluidas.append((nombre, "excluida por --excluir"))
        else:
            a_verificar.append(nombre)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        resultados = list(pool.map(
            lambda n: (n,) + verificar(n, montajes, csv_d7, not args.sin_sha256_tar),
            a_verificar))

    aptas, bloqueadas = [], []
    for i, (nombre, datos, motivos) in enumerate(resultados, 1):
        if motivos:
            bloqueadas.append((nombre, motivos))
            print("[%3d] BLOQUEADA  %-45s %s" % (i, nombre, "; ".join(motivos)))
        else:
            aptas.append(datos)
            print("[%3d] APTA       %-45s %7d arch. %10.1f MB  .tar.gz OK"
                  % (i, nombre, datos["archivos"], datos["bytes"] / 1048576.0))

    print("-" * 78)
    for nombre, motivo in excluidas:
        print("[ -- ] EXCLUIDA   %-45s %s" % (nombre, motivo))

    mb_aptas = sum(d["bytes"] for d in aptas) / 1048576.0
    print("-" * 78)
    print("Aptas: %d (%.1f MB) | Bloqueadas: %d | Excluidas: %d | Listadas: %d"
          % (len(aptas), mb_aptas, len(bloqueadas), len(excluidas), len(lista)))

    if bloqueadas:
        print("\nFAIL-CLOSED: hay carpetas bloqueadas; no se mueve ninguna.")
        return 2
    if not args.ejecutar:
        print("\nDRY-RUN: no se movió nada. Para ejecutar: --ejecutar --tanda %s"
              % args.tanda)
        return 0

    os.makedirs(CUARENTENA, exist_ok=True)
    for datos in aptas:
        entrada = mover(datos)
        print("[MOVIDA] %-45s -> %s" % (entrada["nombre"], entrada["destino"]))
    print("\n%d carpeta(s) en cuarentena. Diario: %s" % (len(aptas), DIARIO))
    print("Revertir: python3 %s --revertir --ejecutar" % os.path.basename(__file__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
