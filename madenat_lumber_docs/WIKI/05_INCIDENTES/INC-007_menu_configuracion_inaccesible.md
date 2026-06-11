# INC-007: Menú Configuración inaccesible para Configurador de Ingesta

**ID:** INC-007
**Fecha:** 2026-06-06
**Estado:** RESUELTO
**Severidad:** Alta (seguridad/navegación)
**Módulo afectado:** madenat_lumber_core

---

## Síntoma

El grupo `group_lumber_config_manager`, creado específicamente para gestionar reglas de ingesta (mapas, tolerancias, filtros), no podía acceder al menú Configuración porque `menu_madenat_config_root` solo aceptaba `groups="base.group_system"`.

## Causa raíz

`lumber_core_menu.xml:138` definía:
```xml
groups="base.group_system"
```

El grupo `group_lumber_config_manager` hereda de `group_madenat_admin` → `group_madenat_cost_auditor` → `base.group_user`. `base.group_system` no implica los grupos custom, por lo que el Configurador quedaba excluido.

Contradicción entre el diseño de seguridad (grupo creado para gestionar ingesta) y la navegación (menú inaccesible para ese grupo).

## Solución

Agregar `group_lumber_config_manager` al atributo `groups`:
```xml
groups="base.group_system,group_lumber_config_manager"
```

## Archivos modificados

`madenat_lumber_core/views/lumber_core_menu.xml` — línea 138

## Verificación

El Configurador de Reglas de Ingesta ahora ve el menú Configuración y sus submenús (Patios de Recepción, Subproductos y Grados).

## Relacionado

- REMEDIACION_CRITICA_2026-06-06.md — Cambio #6
- AUDITORIA_INTEGRAL_2026-06-06.md — Hallazgo A-R4