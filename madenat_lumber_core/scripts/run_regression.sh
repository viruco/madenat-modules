#!/usr/bin/env bash
# ==============================================================================
# MADENAT — Odoo 18 CE: Script de Regresión Canónica sobre los 7 Módulos
# CANON/03 §31 / AD-125 / AD-127
# Prohibido el uso de -i. Uso exclusivo de -u sobre los 7 módulos del núcleo:
# core, intake, logistics, engine, purchasing, costing, billing.
# ==============================================================================
set -e

TS=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/home/viruco/dev-stack/odoo/odoo-18-ce/FASE12_REQUERIMIENTOS_OPERACIONES_20261017/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/regresion_7_modulos_${TS}.log"
EXIT_FILE="${LOG_DIR}/regresion_7_modulos_${TS}.exit"

echo "=== INICIANDO REGRESIÓN MADENAT (${TS}) ==="
echo "Módulos: core, intake, logistics, engine, purchasing, costing, billing"
echo "Destino log: ${LOG_FILE}"

docker exec odoo18_app odoo \
    -c /etc/odoo/odoo.conf \
    -d madenat_test \
    --http-port=8079 \
    -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics,madenat_ingestion_engine,madenat_lumber_purchasing,madenat_lumber_costing,madenat_lumber_billing \
    --test-enable \
    --stop-after-init > "$LOG_FILE" 2>&1
RET=$?

echo "$RET" > "$EXIT_FILE"
echo "=== REGRESIÓN FINALIZADA CON CÓDIGO ${RET} ==="
echo "Log guardado en: ${LOG_FILE}"
exit "$RET"
