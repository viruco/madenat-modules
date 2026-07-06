#!/bin/bash
# extract_odoo_module.sh - Script para extraer módulos Odoo

MODULE_NAME="$1"
BASE_PATH="/opt/odoo18/custom_addons"
MODULE_PATH="$BASE_PATH/$MODULE_NAME"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
OUTPUT_FILE="${MODULE_NAME}_extraction_${TIMESTAMP}.txt"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar si un módulo existe
module_exists() {
    local module="$1"
    local manifest="$BASE_PATH/$module/__manifest__.py"
    local openerp="$BASE_PATH/$module/__openerp__.py"
    [[ -f "$manifest" || -f "$openerp" ]]
}

# Función para listar módulos disponibles
list_modules() {
    echo "Módulos disponibles en $BASE_PATH:"
    for dir in "$BASE_PATH"/*; do
        if [[ -d "$dir" ]]; then
            module=$(basename "$dir")
            if module_exists "$module"; then
                echo "  - $module"
            fi
        fi
    done
}

# Función para obtener contenido de archivo
get_file_content() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if file -b "$file" | grep -q "text"; then
            cat "$file" 2>/dev/null || echo "❌ ERROR: No se pudo leer el archivo"
        else
            echo "⚠️  ARCHIVO BINARIO - OMITIDO"
        fi
    else
        echo "❌ ARCHIVO NO ENCONTRADO"
    fi
}

# Verificar parámetros
if [[ $# -eq 0 ]]; then
    echo -e "${RED}Uso: $0 <nombre_modulo>${NC}"
    echo -e "${YELLOW}O usa: $0 --list para ver módulos disponibles${NC}"
    list_modules
    exit 1
fi

# Listar módulos si se solicita
if [[ "$1" == "--list" || "$1" == "-l" ]]; then
    list_modules
    exit 0
fi

# Verificar si el módulo existe
if [[ ! -d "$MODULE_PATH" ]]; then
    echo -e "${RED}❌ El módulo '$MODULE_NAME' no existe en $BASE_PATH${NC}"
    echo -e "${YELLOW}Módulos disponibles:${NC}"
    list_modules
    exit 1
fi

if ! module_exists "$MODULE_NAME"; then
    echo -e "${RED}❌ '$MODULE_NAME' no parece ser un módulo Odoo válido${NC}"
    exit 1
fi

echo -e "${YELLOW}Extrayendo módulo: $MODULE_NAME...${NC}"

# Crear archivo de extracción
{
    # Encabezado
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  MÓDULO ODOO: $MODULE_NAME"
    echo "║  Fecha de extracción: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "║  Ruta: $MODULE_PATH"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    
    # Estructura del módulo
    echo "=== ESTRUCTURA DEL MÓDULO ==="
    find "$MODULE_PATH" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$MODULE_PATH" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$MODULE_PATH" -type f ! -path "*/__pycache__/*" ! -name "*.pyc" ! -name ".*" | \
    sed "s|$MODULE_PATH/||" | sort | while read -r file; do
        echo "./$file"
    done
    echo ""
    
    # Contenido de archivos
    find "$MODULE_PATH" -type f \( -name "*.py" -o -name "*.xml" -o -name "*.csv" \) \
    ! -path "*/__pycache__/*" ! -name "*.pyc" ! -name ".*" | sort | while read -r file; do
        rel_path="${file#$MODULE_PATH/}"
        echo "=== ARCHIVO: $rel_path ==="
        get_file_content "$file"
        echo "========================================"
        echo ""
    done
    
    # Pie de página
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  EXTRACCIÓN COMPLETADA"
    echo "║  Módulo: $MODULE_NAME"
    echo "║  Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "╚══════════════════════════════════════════════════════════╝"
} > "$OUTPUT_FILE"

# Estadísticas finales
LINES=$(wc -l < "$OUTPUT_FILE")
SIZE=$(du -k "$OUTPUT_FILE" | cut -f1)

echo -e "${GREEN}✅ Extracción completada: $OUTPUT_FILE${NC}"
echo -e "${GREEN}📊 Estadísticas: $LINES líneas, ${SIZE}KB${NC}"