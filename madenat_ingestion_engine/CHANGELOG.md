# Changelog

Todos los cambios notables de este módulo se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [18.0.1.3.0] - 2026-10-19

### Added
- **Bloque 6D (FASE 12 / AD-127) — Packing estándar MADENAT (Forestal Andes)**:
  - Generación de plantilla Excel estándar `PLANTILLA_PACKING_ESTANDAR_MADENAT.xlsx` con listas desplegables (DataValidation) para producto, subproducto y perfil.
  - Soporte de ingesta de proveedores normalizados (Arauco, JCE en dimensiones separadas, BYC, Fátima).
  - Pruebas de ida y vuelta y verificación de redondeo a 3 decimales en `tests/test_packing_estandar_madenat_6d.py`.

## [18.0.1.2.0] - 2026-10-17

### Added
- **WP-E (FASE 12 / AD-112) — Plantilla estándar PACKING_METRICO_ASERRADA y guía de llenado**:
  - Archivo modelo XLSX profesional: `data/templates/PLANTILLA_PACKING_METRICO_ASERRADA.xlsx` para proveedores sin integración automática (Arauco, JCE, BYC, Fátima, etc.) o digitación asistida.
  - Generador automatizado de la plantilla: `data/templates/generate_packing_template.py`.
  - Guía completa de llenado y reglas operativas: `docs/GUIA_LLENADO_PACKING_METRICO.md`.
  - Pruebas automatizadas de extracción y verificación de perfil en `tests/test_packing_metrico_template.py`.

## [18.0.1.1.0] - 2026-10-16

### Added
- Versión inicial del motor de ingesta y normalización de documentos (Excel/PDF).
