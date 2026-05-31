# MADENAT — Índice de Conocimiento Operativo

**Versión:** 1.0.0
**Fecha:** 2026-05-28
**Estado:** ACTIVO

---

## Regla de oro

> Un solo archivo es dueño de cada tipo de verdad.
> Si una verdad cambia, se actualiza primero en el canónico dueño del tema.
> Nunca se duplica información entre archivos.

---

## CANON — Núcleo documental

| Archivo | Dueño de la verdad |
|---|---|
| `CANON/00_ARQUITECTURA.md` | Base técnica, componentes, restricciones y gates |
| `CANON/02_CONTINUIDAD.md` | Checkpoint vivo de retoma operativa |
| `CANON/03_TESTS.md` | Matriz de pruebas y evidencia funcional |
| `CANON/04_DECISION_LOG.md` | Registro de decisiones técnicas y funcionales |
| `CANON/05_BACKLOG.md` | Prioridades y tareas pendientes vigentes |
| `CANON/06_CHECKLIST.md` | Secuencia operativa de trabajo |
| `CANON/07_TRABAJO_CON_IA.md` | Protocolo canónico de trabajo con IA |

---

## WIKI — Negocio

| Nota | Tema |
|---|---|
| `01_NEGOCIO/flujo_compra_madera.md` | Ciclo completo desde compra hasta recepción |
| `01_NEGOCIO/flujo_recepcion_madera.md` | Proceso de ingreso físico y validación |
| `01_NEGOCIO/flujo_despacho_embarque.md` | Proceso de salida a puertos y clientes |
| `01_NEGOCIO/reglas_lotes_trazabilidad.md` | Reglas de negocio de tracking de lotes |
| `01_NEGOCIO/actores_y_roles.md` | Proveedor, operador, despachador, administrador |
| `01_NEGOCIO/reglas_financieras.md` | Gates de contabilidad, valorización y reportes |
| `01_NEGOCIO/tipos_madera_clasificacion.md` | Especies, dimensiones estándar, calidades y codificación de lotes |

---

## WIKI — Técnico

| Nota | Tema |
|---|---|
| `02_TECNICO/modulo_lumber_core.md` | Arquitectura y componentes del módulo principal |
| `02_TECNICO/modelo_lotes.md` | Campos, métodos y reglas del modelo de lotes |
| `02_TECNICO/modelo_recepciones.md` | Modelo lumber.reception: campos, estados, métodos computados |
| `02_TECNICO/modelo_despachos.md` | Modelos de embarques, contenedores, líneas y checklist documental |
| `02_TECNICO/herencia_odoo_modelos.md` | Patrones de herencia usados en MADENAT |
| `02_TECNICO/campos_computados.md` | Listado verificado de campos @api.depends por modelo |
| `02_TECNICO/tracking_mail_thread.md` | Implementación y errores conocidos del tracking |
| `02_TECNICO/security_accesos.md` | Grupos, permisos ir.model.access, sin ir.rule |
| `02_TECNICO/dependencias_modulos.md` | Árbol de dependencias entre módulos MADENAT |

---

## WIKI — Operación

| Nota | Tema |
|---|---|
| `03_OPERACION/entorno_wsl2_docker.md` | Stack completo WSL2 + Docker + PostgreSQL |
| `03_OPERACION/comandos_odoo_dev.md` | Comandos de actualización, reinicio y debug |
| `03_OPERACION/comandos_postgresql.md` | Consultas y mantenimiento de base de datos |
| `03_OPERACION/comandos_docker.md` | Gestión de contenedores y redes |
| `03_OPERACION/despliegue_modulo.md` | Flujo completo de despliegue de cambios |
| `03_OPERACION/comandos_postgresql.md` | Comandos psql, queries de diagnóstico, backups manuales |
| `03_OPERACION/backup_restauracion.md` | Procedimiento de backup PostgreSQL, restauración, frecuencia |
| `03_OPERACION/variables_entorno.md` | Variables docker-compose, odoo.conf, puertos, credenciales dev vs prod |
| `03_OPERACION/migracion_odoo19.md` | Checklist migración Odoo 18→19, cambios conocidos, preparación |

---

## WIKI — Decisiones

| Nota | Tema |
|---|---|
| `04_DECISIONES/DEC-001_modularizacion_v5.md` | Refactor modular a versión 5.0.0 |
| `04_DECISIONES/DEC-002_sin_procesamiento_fisico.md` | Decisión de no modelar procesamiento físico |
| `04_DECISIONES/DEC-003_tracking_sin_chatter.md` | Resolución de duplicado en mail.thread |
| `04_DECISIONES/DEC-004_postgresql_docker.md` | Uso de PostgreSQL en contenedor separado |
| `04_DECISIONES/DEC-005_oracle_cloud_prod.md` | Estrategia de despliegue en Oracle Cloud |

---

## WIKI — Incidentes

| Nota | Tema |
|---|---|
| `05_INCIDENTES/INC-001_campo_name_duplicado.md` | Duplicado de campo name en guia_processing |
| `05_INCIDENTES/INC-002_db_host_incorrecto.md` | Error odoo18_db vs madenat_test |
| `05_INCIDENTES/INC-003_address_in_use.md` | Puerto en uso por container activo |
| `05_INCIDENTES/INC-004_column_inexistente.md` | Columna inexistente por falta de actualización |
| `05_INCIDENTES/INC-005_license_manifest.md` | Falta de license en manifests de módulos |

---

## WIKI — Sesiones

| Nota | Uso |
|---|---|
| `06_SESIONES/_PLANTILLA_SESION.md` | Plantilla para registrar sesiones: contexto, objetivos, decisiones, pendientes |
| `06_SESIONES/_CAPSULA_CONTEXTO.md` | Cápsula activa de contexto para pegar en IA |

---

## Plantillas reutilizables

- `_PLANTILLA_NOTA.md` — estructura base para cualquier nota wiki
- `_PLANTILLA_DECISION.md` — estructura base ADR para decisiones técnicas
- `_PLANTILLA_INCIDENTE.md` — estructura base para documentar incidentes
