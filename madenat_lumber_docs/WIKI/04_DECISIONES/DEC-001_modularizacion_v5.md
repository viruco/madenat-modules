# DEC-001 — Refactor Modular a Versión 5.0.0

**Fecha:** 2026-05-03
**Estado:** Aceptada
**Módulo afectado:** madenat_lumber_core, madenat_lumber_reports

## Contexto

El módulo crecía como monolito. Modelos, vistas, reportes y lógica mezclados sin separación clara. Cada actualización tenía riesgo de romper partes no relacionadas.

## Opciones evaluadas

| Opción | Ventaja | Desventaja |
|---|---|---|
| Mantener monolito | Sin costo de refactor | Difícil mantenimiento |
| Separar módulos por dominio | Menor acoplamiento | Costo de refactor |
| Separar solo reportes | Impacto mínimo | No resuelve fondo del problema |

## Decisión tomada

Separar `madenat_lumber_reports` como módulo independiente. El core queda con modelos, vistas, seguridad y datos base. Los reportes tienen ciclo de actualización propio.

## Impacto

- Versión del core sube a 5.0.0.
- Reportes se instalan y actualizan de forma independiente.
- Cada módulo declara su `license` en manifest (fix INC-005).

## Criterio de revisión

Revisar al preparar migración a Odoo 19 (julio 2026).

## Referencias

- [[dependencias_modulos]]
- [[00_ARQUITECTURA]]
- [[INC-005_license_manifest]]
