#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extraer módulos Odoo desde /opt/odoo18/custom_addons
Los archivos se guardan en /tmp/
"""

import os
import sys
from datetime import datetime

def get_file_content(file_path):
    """Obtiene el contenido de un archivo con manejo de errores"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            return f"❌ ERROR: No se pudo leer el archivo - {str(e)}"
    except Exception as e:
        return f"❌ ERROR: No se pudo leer el archivo - {str(e)}"

def list_modules():
    """Lista los módulos disponibles"""
    base = "/opt/odoo18/custom_addons"
    modules = []
    for item in os.listdir(base):
        item_path = os.path.join(base, item)
        if os.path.isdir(item_path):
            manifest_path = os.path.join(item_path, '__manifest__.py')
            openerp_path = os.path.join(item_path, '__openerp__.py')
            if os.path.exists(manifest_path) or os.path.exists(openerp_path):
                modules.append(item)
    return sorted(modules)

def extract_module(module_name):
    """Extrae un módulo específico y guarda en /tmp/"""
    base_path = "/opt/odoo18/custom_addons"
    module_path = os.path.join(base_path, module_name)
    
    if not os.path.exists(module_path):
        print(f"❌ El módulo '{module_name}' no existe")
        return False
    
    # Crear archivo de salida en /tmp/
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"/tmp/{module_name}_extraction_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("╔══════════════════════════════════════════════════════════╗\n")
        f.write(f"║  MÓDULO ODOO: {module_name}\n")
        f.write(f"║  Fecha de extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"║  Ruta: {module_path}\n")
        f.write(f"║  Destino: {output_file}\n")
        f.write("╚══════════════════════════════════════════════════════════╝\n\n")
        
        # Estructura del módulo
        f.write("=== ESTRUCTURA DEL MÓDULO ===\n")
        for root, dirs, files in os.walk(module_path):
            # Excluir __pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            level = root.replace(module_path, '').count(os.sep)
            indent = ' ' * 2 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if not file.endswith('.pyc'):
                    f.write(f"{subindent}{file}\n")
        f.write("\n")
        
        # Contenido de archivos
        file_count = 0
        for root, dirs, files in os.walk(module_path):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith(('.py', '.xml', '.csv')) and not file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, module_path)
                    
                    # Saltar archivos grandes
                    if os.path.getsize(file_path) > 1024 * 1024:
                        f.write(f"=== ARCHIVO: {rel_path} ===\n")
                        f.write("⚠️  ARCHIVO DEMASIADO GRANDE - OMITIDO\n")
                        f.write("========================================\n\n")
                        continue
                    
                    f.write(f"=== ARCHIVO: {rel_path} ===\n")
                    content = get_file_content(file_path)
                    f.write(content)
                    if content and not content.endswith('\n'):
                        f.write("\n")
                    f.write("========================================\n\n")
                    file_count += 1
        
        # Pie de página
        f.write("╔══════════════════════════════════════════════════════════╗\n")
        f.write("║  EXTRACCIÓN COMPLETADA\n")
        f.write(f"║  Módulo: {module_name}\n")
        f.write(f"║  Archivos procesados: {file_count}\n")
        f.write(f"║  Ubicación: {output_file}\n")
        f.write(f"║  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("╚══════════════════════════════════════════════════════════╝\n")
    
    # Estadísticas
    line_count = sum(1 for _ in open(output_file, 'r', encoding='utf-8'))
    file_size = os.path.getsize(output_file) / 1024
    
    print(f"✅ Módulo '{module_name}' extraído exitosamente")
    print(f"📁 Ubicación: {output_file}")
    print(f"📊 Estadísticas: {line_count} líneas, {file_size:.1f} KB, {file_count} archivos procesados")
    
    # Mostrar ubicación completa
    print(f"🔗 Ruta completa: file://{output_file}")
    
    return True

def show_recent_extractions():
    """Muestra las extracciones recientes en /tmp/"""
    print("\n📂 Extracciones recientes en /tmp/:")
    extractions = []
    try:
        for file in os.listdir("/tmp"):
            if "_extraction_" in file and file.endswith(".txt"):
                file_path = os.path.join("/tmp", file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                size = os.path.getsize(file_path) / 1024
                extractions.append((mod_time, file, size))
        
        # Ordenar por fecha (más reciente primero)
        extractions.sort(reverse=True)
        
        for mod_time, file, size in extractions[:5]:  # Mostrar solo las 5 más recientes
            print(f"  - {file} ({size:.1f} KB) - {mod_time.strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        print(f"  No se pudieron listar extracciones recientes: {e}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_odoo_module.py <nombre_modulo>")
        print("Uso: python3 extract_odoo_module.py --list")
        print("Uso: python3 extract_odoo_module.py --recent")
        print("\nMódulos disponibles:")
        for module in list_modules():
            print(f"  - {module}")
        show_recent_extractions()
        return
    
    if sys.argv[1] in ['--list', '-l']:
        print("Módulos disponibles:")
        for module in list_modules():
            print(f"  - {module}")
        return
    
    if sys.argv[1] in ['--recent', '-r']:
        show_recent_extractions()
        return
    
    module_name = sys.argv[1]
    if module_name not in list_modules():
        print(f"❌ Módulo '{module_name}' no encontrado")
        print("Módulos disponibles:")
        for module in list_modules():
            print(f"  - {module}")
        return
    
    extract_module(module_name)

if __name__ == "__main__":
    main()