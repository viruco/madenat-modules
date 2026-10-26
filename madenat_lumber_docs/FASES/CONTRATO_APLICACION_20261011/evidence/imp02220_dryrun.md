# IMP02220 — DRY-RUN DE ALTERNATIVAS (sólo lectura; NADA ejecutado)

**Documento:** `madenat.sv.imputation` `id=1189` `IMP02220` · compañía 1 · guía **1198 / «19827»**
(`state=validated`, `service_return_confirmation=yes`) · `documentary_key IMP-1198-E95825AAF94E58AD`.
**Estado:** `applied`. **Creado/aplicado** por usuario 8 el **2026-10-10 22:30:45** (misma marca de
tiempo ⇒ una transacción). `processor_id` vacío. **Sin reversa.**

## Hechos verificados (read-only)
- **Líneas (2):** etiqueta `18368` nominal **3.263 m³**; etiqueta `18372` nominal **4.225 m³**.
- **Σ nominal comprometido = 7.488 m³**; **repartos SV = 0** (Σ `imputed_volume_m3` = 0).
- **Disponibilidad actual por etiqueta:** `18368` nominal 3.263 / activo 3.263 / **disponible 0.000**;
  `18372` nominal 4.225 / activo 4.225 / **disponible 0.000**.
- **Efecto sobre SV:** **ninguno** (ningún SV cambia su saldo documental por IMP02220).
- **Dependencias:** `madenat.processor.return.link` de la guía 1198 = **0**; no hay otras imputaciones
  sobre esas etiquetas; etiquetas con `lot_flow_type=NULL` (anomalía **independiente**, sin causalidad
  demostrada).
- **Historia:** 1 evento `madenat.audit.log` (`imputation`, usuario 8, 2026-10-10 22:30:45); 1
  `mail.message`. Sin `deviation` ni `imputation_reverse`.
- **Clasificación exigida a registrar:** «Aplicado bajo comportamiento anterior; nominal comprometido sin
  reparto SV; pendiente de decisión de regularización».

## Alternativas (impacto)

| | **Alt-1 Conservar con clasificación explícita** | **Alt-2 Revertir y reasignar (si procede y se autoriza)** |
| --- | --- | --- |
| Acción | Sin cambios al documento; se registra la clasificación en documentación/nota | `action_reverse` (Jefatura/Gerencia, con motivo) + nueva imputación **con reparto** |
| Capacidad etiqueta | Se mantiene consumida **7.488 m³** (no reutilizable) | Libera **7.488 m³**; la nueva operación vuelve a comprometer según su reparto |
| Efecto SV | Ninguno | Asigna a SV (según destino real); el reparto previo no existía |
| Dependencias | Ninguna | Ninguna (0 links; sin documentos posteriores que dependan) |
| Historia | Intacta | Append-only: original `reversed` + nuevo `applied` (ambos consultables) |
| Riesgos | Capacidad «muerta» sin destino; puede inducir errores operativos | Reasignar a un SV incorrecto si no se conoce el destino real; nueva reserva |
| Validaciones al ejecutar | — (nada que ejecutar) | Techo duro, integridad etiqueta–guía (D10), motivo de reversa, permisos Jefatura/Gerencia |
| Autorización requerida | Aprobar la **clasificación** (documental) | Aprobar **reversa + reasignación** y confirmar el SV destino real |

**Recomendación:** **Alt-1** por defecto (conservar y clasificar) mientras no exista un destino SV real
confirmado; **Alt-2** si Mauricio confirma el destino y lo autoriza.

## Límites
- **No** se ha ejecutado reversa ni reparación.
- **No** se vincula `lot_flow_type=NULL` a esta regularización (sin evidencia causal).
- Cualquier reparación sería **idempotente y con dry-run**, previa **copia de seguridad** (`code_cierre/`,
  `db_cierre/`) y **autorización expresa**.
