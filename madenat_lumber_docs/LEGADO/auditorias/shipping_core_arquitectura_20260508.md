# Arquitectura — MADENAT Shipping Core

**Módulo:** `madenat_lumber_shipping_core`
**Versión:** `18.0.1.0.0`
**Fecha auditoría:** 2026-05-08
**Estado:** REQUIERE AUDITORÍA
**Tests:** ❌ SIN TESTS

---

## Propósito

Este módulo entrega los datos maestros de transporte marítimo para el ecosistema MADENAT ERP. Define buques, viajes y reservas de espacio (bookings) como un catálogo que debe ser consumido por logística y facturación.

## Posición en la Cadena

```
Odoo Core → [madenat_lumber_shipping_core] → madenat_lumber_core
```

## Modelos Definidos

### `shipping.vessel`
**Archivo:** `models/shipping_vessel.py`
**Descripción:** Representa una motonave / buque utilizado en la cadena de exportación.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `name` | Char | Nombre del buque | — |
| `imo_number` | Char | Número IMO con formato `IMO 1234567` | — |
| `flag_country_id` | Many2one | Bandera del buque | → `res.country` |
| `vessel_type` | Selection | Tipo de buque | — |
| `capacity_teu` | Integer | Capacidad en TEU | — |
| `active` | Boolean | Activo / Inactivo | — |

**Métodos de negocio:**
- `_check_imo_number()` — valida el formato del número IMO cuando se provee.

### `shipping.voyage`
**Archivo:** `models/shipping_voyage.py`
**Descripción:** Define un viaje marítimo asociado a un buque, con estados y fechas estimadas.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `name` | Char | Nombre interno calculado | — |
| `display_name` | Char | Nombre mostrado calculado | — |
| `vessel_id` | Many2one | Buque asignado al viaje | → `shipping.vessel` |
| `voyage_reference` | Char | Referencia de viaje de la naviera | — |
| `port_of_loading` | Char | Puerto de carga | — |
| `port_of_discharge` | Char | Puerto de descarga | — |
| `etd` | Date | Salida estimada | — |
| `eta` | Date | Llegada estimada | — |
| `state` | Selection | Estado del viaje | — |

**Métodos de negocio:**
- `_compute_names()` — construye `name` y `display_name` desde `vessel_id` y `voyage_reference`.
- `_expand_states()` — expande todos los estados configurados para la vista kanban/grupo.

### `shipping.booking`
**Archivo:** `models/shipping_booking.py`
**Descripción:** Reserva de espacio (booking) para un viaje marítimo.

| Campo | Tipo | Descripción | Relación externa |
|-------|------|-------------|-----------------|
| `name` | Char | Número de booking | — |
| `shipping_line_id` | Many2one | Línea naviera | → `res.partner` |
| `voyage_id` | Many2one | Viaje asignado | → `shipping.voyage` |
| `container_qty` | Integer | Cantidad de contenedores | — |
| `container_type` | Selection | Tipo de contenedor | — |
| `booking_date` | Date | Fecha de reserva | — |
| `cargo_cutoff_date` | Datetime | Fecha límite de carga | — |
| `vgm_cutoff_date` | Datetime | Fecha límite VGM | — |
| `notes` | Text | Notas e instrucciones | — |
| `active` | Boolean | Activo / inactivo | — |

**Métodos de negocio:**
- No define métodos complejos propios, solo guarda el estado de reserva.

## Modelos Heredados

### `mail.thread` / `mail.activity.mixin`
**Archivo:** `models/shipping_vessel.py`, `models/shipping_voyage.py`, `models/shipping_booking.py`
**Campos añadidos:**
- Tracking en `shipping.vessel`, `shipping.voyage` y `shipping.booking` para historial de cambios.

## Wizards

No existen wizards declarados en este módulo.

## Relaciones con otros módulos MADENAT

Este módulo no define relaciones directas con modelos específicos de MADENAT. Sus vínculos son mayormente con modelos estándar de Odoo y con sus propios maestros internos.

| Campo | Modelo origen | Módulo | Tipo relación |
|-------|--------------|--------|---------------|
| `shipping.booking.shipping_line_id` | `shipping.booking` | Odoo Core | Many2one → `res.partner` |
| `shipping.booking.voyage_id` | `shipping.booking` | Este módulo | Many2one → `shipping.voyage` |
| `shipping.voyage.vessel_id` | `shipping.voyage` | Este módulo | Many2one → `shipping.vessel` |
| `shipping.vessel.flag_country_id` | `shipping.vessel` | Odoo Core | Many2one → `res.country` |

## Seguridad

| Modelo | Usuario | Acceso |
|--------|---------|--------|
| `shipping.vessel` | `base.group_user` | CRUD |
| `shipping.voyage` | `base.group_user` | CRUD |
| `shipping.booking` | `base.group_user` | CRUD |

**Observaciones de seguridad:**
- El archivo `security/security.xml` define grupos personalizados `group_shipping_user` y `group_shipping_manager`, pero la configuración de `ir.model.access.csv` usa directamente `base.group_user`.
- Esto sugiere que los grupos propios no estén aplicando restricciones efectivas y que la intención declarada de “Usuario (Solo Lectura)” no se esté respetando.

## Tests

No se detectó directorio `tests/` ni archivos de pruebas en el módulo.

## Deuda Técnica

| ID | Severidad | Descripción | Fix estimado |
|----|-----------|-------------|-------------|
| DT-NEW-madenat_lumber_shipping_core-001 | 🟡 Importante | No hay pruebas unitarias o de integración en el módulo. | 60 min |
| DT-NEW-madenat_lumber_shipping_core-002 | 🟡 Importante | `security/ir.model.access.csv` otorga CRUD a `base.group_user`; los grupos definidos en `security/security.xml` no se utilizan para el control de acceso. | 30 min |
| DT-NEW-madenat_lumber_shipping_core-003 | 🟢 Menor | Existe `models/shipping_models.py` con definiciones duplicadas de `shipping.vessel`, `shipping.voyage` y `shipping.booking`, pero no es importado en `models/__init__.py`. | 20 min |

## Decisiones de Diseño

- **Uso de maestros estándar de Odoo:** Se eligieron `res.partner` y `res.country` para evitar crear modelos propios de navieras y banderas, facilitando la integración con otros procesos de Odoo.
- **Modelo de viaje con nombre calculado:** `shipping.voyage` normaliza su identidad usando `vessel_id` + `voyage_reference`, lo cual mejora la claridad en listados y evita duplicar nombres manuales.
- **Simplicidad en puertos:** Opta por campos `Char` para `port_of_loading` y `port_of_discharge` en lugar de un catálogo de puertos, reduciendo la complejidad de datos maestros.

---
*Auditado: 2026-05-08 | Próxima revisión: 2026-05-15*
