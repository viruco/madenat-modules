# PROMPT 2D — Procedencia del perfil y vigencia de la lectura (FASE 13)

> Copia operativa del encargo ejecutado el 2026-10-26. Base aprobada: §12.4 del
> `INFORME_FASE_2B.md` (diff publicado) + decisiones H1–H5.

## 1. Objetivo

Aplicar la **FASE 2D** del motor de ingesta:

1. La sugerencia documental de perfil **no** puede sobrescribir una elección explícita del operador.
2. La lectura del documento tiene **vigencia**: si cambian sus entradas, deja de valer y hay que releer
   antes de derivar el ingreso.

## 2. Decisiones aprobadas

| ID | Decisión |
|---|---|
| H1 | Crear `.clinerules/madenat-regla-de-oro.md` y guardar este prompt en `custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/PROMPT_2D.md` |
| H2 | Sí: la derivación exige `previewed` en **las tres** modalidades; la lectura de Procesado también deja `previewed`. Debe mantener verdes T1–T6 |
| H3 | Migración **solo** si los valores por defecto no bastan; en su caso, inicializar columnas nuevas de forma idempotente. Si no hace falta, omitirla y reportarlo |
| H4 | Aceptar la limitación: el distintivo «Perfil sugerido» se ve mientras la procedencia no sea `chosen`; sin badge adicional de «elegido» |
| H5 | Diferir `_onchange_intake_modality_patio` (riesgo **R6**) y documentarlo en informe y CANON |

## 3. Alcance del código

- `custom_addons/madenat_lumber_intake/models/intake_wizard.py`
- `custom_addons/madenat_lumber_intake/views/intake_wizard_views.xml`
- `custom_addons/madenat_lumber_intake/__manifest__.py` → `18.0.0.22.0`
- `custom_addons/madenat_lumber_intake/migrations/18.0.0.22.0/post-migrate.py` (**solo si H3 lo exige**)
- `custom_addons/madenat_lumber_intake/tests/test_intake_profile_provenance.py` (nuevo, T-2D-1…9)
- `custom_addons/madenat_lumber_intake/README.md` y `CHANGELOG.md`
- CANON: `04_DECISION_LOG`, `12_FLUJOS_INGESTA`, `03_TESTS`, `02_CONTINUIDAD`, `INDICE_DOCUMENTACION`
- `custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/INFORME_FASE_2B.md` (§2D)

**Excluido de commits:** `custom_addons/madenat_lumber_costing/*` (8 archivos) y
`custom_addons/madenat_lumber_reports/views/lumber_reports_menu.xml`.

## 4. Contenido funcional (5 campos)

`profile_suggested`, `profile_origin` (`default`/`suggested`/`chosen`), `profile_mismatch_hint`,
`reading_signature` y el helper de vista `has_required_documents`.

## 5. Pasos ejecutados

1. Detección de estado (árbol propio limpio, md5 del informe, contenedores arriba).
2. Relectura del diff publicado y de las líneas ancla reales.
3. Commits por ruta: modelo+vista → pruebas → correcciones de prueba → README/CHANGELOG.
4. Creación de `.clinerules/madenat-regla-de-oro.md` y de este `PROMPT_2D.md`.
5. Despliegue en `madenat_test`: respaldo → parar web → `-u` con `--test-tags` → levantar web → HTTP 200.
6. Verificación: T-2D-1…9, T1–T6, suites 2A/2B, md5 de líneas y lotes.
7. Documentación CANON + §2D del informe y cierre.

## 6. Matriz de verificación

- `T-2D-1…T-2D-9` (procedencia, invalidación, lectura rancia, documentos requeridos, contrato de vista).
- `T1…T6` del wizard (`test_intake_wizard`) sin regresiones.
- Suites de 2A/2B: clasificación, marca de advertencia, coherencia de perfil, volúmenes y granel.
- Datos: md5 de líneas y lotes sin cambios; sólo se admiten **registros nuevos** distintos.
- Servicio: `HTTP 200` en `/web/login`.

## 7. Reglas de trabajo

- Regla de Oro: un paso por vez, evidencia antes de afirmar.
- `git add` por ruta (nunca `-A`); commits pequeños y temáticos.
- Ante un fallo: reportarlo tal cual, sin arreglos colaterales ni commits adicionales no autorizados.
- Cierre exacto: `FASE 2D COMPLETADA — A LA ESPERA DE REVISIÓN`. No iniciar 2B tramo 3 ni Fase 2C.
