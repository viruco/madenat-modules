# ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012 — Alineación documental + inventario + inspección previa

**Fecha:** 2026-10-12 · **Entorno:** `madenat_test` LOCAL + repositorio local. **TEST remoto: NO tocado.**
**Regla cumplida:** SIN conexión al remoto · SIN commit/push/despliegue · SIN `-u all` · SIN reparación
histórica · SIN tocar datos ni `IMP04823`/`IMP02220` · SIN cambiar ACL/`mail`/core.

## 0. Baseline

- **Repositorio:** `custom_addons/.git` · **Rama:** `feat/guia-correccion-documental-preservada-20261002`
  · **HEAD:** `b1d2d1911648f3264bf629c8eccf79a1c140eaf3` · **WIP:** **104** entradas (`git status --porcelain`).
- **Versiones locales instaladas:** `madenat_lumber_core` **18.0.6.7.0**, `madenat_lumber_logistics`
  **18.0.1.26.0**, `madenat_lumber_intake` **18.0.0.13.0**, `madenat_lumber_costing` 18.0.1.0.0,
  `madenat_vendor_payment` **18.0.1.2.0** (instalado).
- **Respaldo previo a editar:** `code/pre_align_docs.tar.gz` (CANON/02,03,05,19,INDICE y WIKI/00,03).

---

## Parte A — Alineación de la documentación · **CORREGIDA (con 2 hallazgos preexistentes declarados)**

### A.1 Causa del desajuste

La entrega HOTFIX_OWL_CHATTER (sesión previa) escribió sus metadatos **partiendo de la cabecera obsoleta** de
cada documento en vez de la **última versión ya registrada** en el changelog. Además rotuló su sección de 02
como `§17.16.19`, **ya reservada** por la entrega AUD-ETQ-01..05, y el comentario del INDICE quedó duplicado
(`2026-10-12 (1)`). Los CANON tienen además **desajustes propios previos** (cabeceras por debajo del changelog).

### A.2 Tabla de alineación (documento → versión registrada → encontrada → corregida → causa → evidencia)

| Documento | Versión **registrada** (máx. declarado) | Versión **encontrada** | Versión **corregida** | Causa | Evidencia |
|---|---|---|---|---|---|
| `CANON/02_CONTINUIDAD.md` | **12.38.0** (`02 → 12.38.0`; INDICE 2026-10-12 (4)) | 12.35.0 | **12.39.0** | Mi bump partió de 12.34.0 (cabecera obsoleta) | `logs/verify_alignment_pre/post.out`; greps en A.3 |
| `CANON/03_TESTS.md` | **6.37.0** (`03 → 6.37.0`) | 6.34.0 | **6.38.0** | Ídem (cabecera tenía 6.33.0) | ídem |
| `CANON/19_...md` | **1.30.0** (INDICE 2026-10-12 (5)) | 1.31.0 | **1.31.0** (ya correcto) | — | ídem |
| `CANON/05_BACKLOG.md` | **8.25.0** | 8.26.0 | **8.26.0** (ya correcto) | — | ídem |
| `CANON/INDICE_DOCUMENTACION.md` | **12.28.0** | 12.29.0 | **12.29.0** (ya correcto) | — | ídem |
| `WIKI/00_INDICE.md` | 2.0.1 | 2.0.2 | **2.0.2** (ya correcto) | — | ídem |

**Sección de 02:** `§17.16.19` (mía) **→ `§17.16.30`** (la 19 estaba reservada; la 30 es la siguiente libre
tras `§17.16.29`). **Comentario de changelog de 02:** de `(6)` **→ `(5)`** (no existía `(5)` de 2026-10-12).
**Comentario del INDICE:** de `2026-10-12 (1)` **→ `2026-10-12 (6)`** (elimina el duplicado) y versiones
`02 12.39.0 / 03 6.38.0`.

**Defecto estructural PREEXISTENTE corregido (INDICE):** el comentario `2026-10-12 (2)` (VERIFICACIÓN PROBATORIA
P1–P4) estaba **truncado** (terminaba en `**Sin`) y su **cola** (`commit/push/despliegue; TEST remoto
intacto.** -->`) había quedado **desplazada al final del archivo** como línea suelta. Se **re-adjuntó la cola a su
comentario** ⇒ `<!--`/`-->` **balanceados** (22/22; antes: 1 comentario abierto sin cerrar). Verificado con
escáner de marcadores (`logs/verify_alignment_post.out` y el chequeo de balance).

> **Fuente única canónica:** sólo se editaron los CANON/WIKI existentes; **no** se crearon documentos paralelos.

### A.3 Método y verificación (script)

`code/verify_doc_alignment.py` comprueba: (1) cabecera ≥ última versión declarada; (2) secciones duplicadas;
(3) ids de comentario duplicados. **Antes:** 4 hallazgos (2 míos + 2 preexistentes). **Después:** 2 hallazgos,
**ambos preexistentes** (ver A.4). Salidas: `logs/verify_alignment_{pre,post}.out`.

### A.4 Hallazgos PREEXISTENTES (detectados; **NO** corregidos → requieren decisión)

1. **02 — id de comentario duplicado:** dos comentarios `2026-10-10 (3)` (para `§17.16.10` y `§17.16.11`);
   además faltan `(4)(5)(6)`. Renumerar arrastraría 7 entradas de entregas previas ⇒ **ambigüedad**: se declara,
   no se reescribe.
2. **03 — secciones duplicadas §5–§9:** existen **dos series** `## 5.`…`## 9.` (la fundacional y la serie
   "Cobertura…" que reusó 5–9 antes de saltar a §10). La renumeración "correcta" es **ambigua** (desplazar
   §10–§30 → §15–§35, 26 encabezados, **o** anexar la serie a §31–§35) y tocaría entregas previas ⇒ se declara
   con opciones, **sin ejecutar**.

### A.5 Hallazgo estructural preexistente (entradas sin sección)

El changelog de 02 y el INDICE citan **§17.16.19 … §17.16.29**, pero esas **secciones de cuerpo NO existen** en
02 (solo comentarios; su contenido vive en los expedientes `AUDIT_REBAJA_ETIQUETAS_20261011/`,
`RESET_REBAJA_20261011/`, `SIMPLE_REBAJA_20261011/`, `UI_SAVE_REBAJA_20261011/`, `SAVE_REBAJA_20261011/`,
`CONTRATO_APLICACION_20261011/`, `BLINDAJE_REBAJA_LOCAL_20261012/`, `CIERRE_SOBRESCRITURA_V123_20261012/`).
No se reconstruyen de memoria (instrucción explícita). **Propuesta:** o se aceptan los expedientes como fuente
de sección, o se restauran como secciones nuevas en una intervención dedicada.

---

## Parte B — Inventario del marcado heredado · **ACREDITADA**

Barrido de **todos** los módulos MADENAT (`code/part_b_inventory.sh`, salida `logs/part_b_inventory.out`):

| Módulo | Archivo · línea | Instalado local | En paquete a desplegar | Vista | Riesgo |
|---|---|---|---|---|---|
| `madenat_vendor_payment` | `views/lumber_shipment_cost_views.xml:151` (`div.oe_chatter` + `message_follower_ids`/`activity_ids`/`message_ids` en 152–154) | **Sí** (18.0.1.2.0) | **No** (no está en `data` del manifest ni en el paquete) | **Principal** (`lumber.shipment.cost.line.form`, sin `inherit_id`) | **Bajo** |

**Hallazgo clave:** `lumber_shipment_cost_views.xml` **NO figura en el `data` del `__manifest__.py`** y el modelo
`lumber.shipment.cost.line` **no hereda `mail.thread`** (sin `message_ids`/`activity_ids`). Por eso su vista **no
está** en la BD (0 vistas con `class="oe_chatter"`) y **no reproduce** hoy. Si se habilitara, además fallaría por
campos inexistentes. **Propuesta (sujeta a autorización):** `div.oe_chatter` → `<chatter/>` **y** dar soporte de
chatter al modelo **y** añadirlo al manifest — o **retirar** el archivo huérfano. **No ejecutado.**

- **Único defecto real** en MADENAT: el anterior. El resto usa correctamente `<chatter/>` (15 usos).
- **Sin** otros `message_ids`/`message_follower_ids`/`activity_ids` manuales (solo esas 3 líneas), ni otras
  construcciones obsoletas.

**Verificación de los formularios corregidos** (arch **efectivo con herencias** aplicadas, ORM):
`logs/effective_arch_chatter_check.out` ⇒ ambos (`madenat.sv.imputation`, `madenat.processor.return.link`)
tienen `chatter=True`, `message_ids` **NO** es campo suelto (`False`), `message_follower_ids` **NO** (`False`).

---

## Parte C — Inspección de SOLO LECTURA del TEST remoto · **PREPARADA (no ejecutada por Cline)**

- **Guion:** `docs/INSPECCION_REMOTO_SOLO_LECTURA.sh` (lo ejecuta **Mauricio** en el remoto).
- **Tabla de seguridad:** `docs/SEGURIDAD_SCRIPT_INSPECCION.md` (comando → lectura/escritura → riesgo). Todas las
  sentencias son `SELECT`/`grep`/`--version`; **0 escrituras**; sin `systemctl`, `pg_restore`, `-u`, redirecciones
  de escritura. `bash -n` OK.
- **Dry-run** controlado: `logs/inspeccion_dryrun.out` (prefijos sustituidos) → ejecuta las 9 secciones sin
  efectos.
- **Recoge:** (1) versión de Odoo; (2) módulos MADENAT; (3) `madenat_vendor_payment`; (4) vistas con
  `oe_chatter`; (5) si el core compila `oe_chatter` o sólo `<chatter/>`; (6) versiones en disco de manifests;
  (7) última actualización de módulos; (8) errores Owl/vista (filtrado); (9) conteo de usuarios activos.
- **Privacidad:** no imprime correos/claves/datos; se indica qué recortar antes de pegar.
- **Cline NO se conecta al remoto.** Si no se entrega la salida, **no** se interpreta ni se inventan resultados.

---

## Parte D — Criterio de decisión de despliegue · **PREPARADO (sin ejecutar)**

Árbol completo (CASOS 1–5 con módulos a copiar, `-u`, respaldo, smoke test, rollback y aviso a Cristhian) en
`FASES/HOTFIX_OWL_CHATTER_OE_20261012/docs/PLAN_DESPLIEGUE_ACUMULADO.md` **§10–§11**. Resumen:
CASO 1 (remoto sólo `<chatter/>` + vistas con `oe_chatter`) → **priorizar hotfix**; CASO 2 (core viejo que aún
compila `oe_chatter`) → preventivo, combinable; CASO 3 (`vendor_payment` instalado con `oe_chatter`) → riesgo
adicional, corrección sujeta a autorización; CASO 4 (versiones remotas distintas) → reconstruir paquete mínimo y
orden; CASO 5 (ambiguo) → **declarar pendiente, no decidir**.

---

## Entregables y archivos

- `README.md` (este informe) · `docs/INSPECCION_REMOTO_SOLO_LECTURA.sh` ·
  `docs/SEGURIDAD_SCRIPT_INSPECCION.md` · `docs/PLAN_DESPLIEGUE_ACUMULADO.md` (actualizado).
- `code/verify_doc_alignment.py` · `code/part_b_inventory.sh` · `code/pre_align_docs.tar.gz`.
- `logs/verify_alignment_{pre,post}.out` · `logs/part_b_inventory.out` ·
  `logs/effective_arch_chatter_check.out` · `logs/inspeccion_dryrun.out`.
- **WIP ajeno preservado** (104 entradas; solo se editaron los CANON/WIKI listados). **Sin commit/push.**

## Pendientes / autorizaciones requeridas
1. Decisión sobre los **2 hallazgos preexistentes** de numeración (02 comentario; 03 §5–§9).
2. **Restauración/aceptación** de las secciones §17.16.19…§17.16.29 (hoy solo en expedientes).
3. Corrección/retiro de `madenat_vendor_payment` (Parte B).
4. Ejecutar la **inspección remota** (Mauricio) y remitir la salida para aplicar el árbol de decisión.
5. Aceptación de **navegador** pendiente (VIEW cliente).
