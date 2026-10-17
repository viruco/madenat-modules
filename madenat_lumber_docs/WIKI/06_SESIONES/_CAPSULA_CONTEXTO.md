# 🪵 CÁPSULA DE CONTEXTO — MADENAT LUMBER DOCS

**Fecha de última actualización:** 2026-10-17  
**Fase activa:** FASE 12 — Requerimientos de Operaciones (Cristhian)  
**Estado:** Bloque 1 y Bloque 2 COMPLETADOS en local (TDD 100% verde) | Bloque 3 DETENIDO  

---

## 1. Proyecto y Entorno
- **Plataforma:** Odoo 18 CE custom — industria maderera (Chile).
- **Entorno:** WSL2 Ubuntu + Docker (`odoo18_app` en puerto 8069, `odoo18_db` postgres:15 interno).
- **Base de datos de trabajo:** `madenat_test` | Usuario: `odoo`.
- **Regla técnica:** Ejecución CLI con `--stop-after-init --http-port=8070` para evitar colisión de puertos.

---

## 2. Ecosistema de Módulos Custom (`custom_addons/`)
- `madenat_lumber_core` (`18.0.6.9.0`): Lógica troncal de lotes, UoM (regla 2.36 m³ = 1 MBF), recepciones y guías.
- `madenat_lumber_logistics` (`18.0.1.38.0`): Consolidación, contenedores, embarques e imputación documental SV (I2).
- `madenat_lumber_intake` (`18.0.0.16.0`): Fachada y consola de ingreso de madera, filtro y menú «Ingresos por Volúmenes».
- `madenat_ingestion_engine` (`18.0.1.2.0`): Motor agnóstico de extracción/normalización de Excel/PDF, perfiles y plantilla métrica.
- `madenat_toll_processing` / `madenat_lumber_shipping_core`: Módulos de maquila y transporte marítimo.
- `madenat_lumber_costing` / `madenat_lumber_reports`: Preservados en su estado WIP preexistente sin commitear.

---

## 3. Estado de Fases Recientes (Reconciliación D-E0-1)
- **FASE 10 (AD-109) — 100% CERRADA:** Correcciones S1 (firma/clave documental con etiquetas seleccionadas), S2 (filtro y reanudación operativa de borrador en preparación) y S3 (bloqueo sin etiquetas incluidas).
- **FASE 11 (AD-110) — 100% CERRADA:** Integridad de ciclo de vida de imputaciones SV. A-1/B-1 (escritura de `state` protegida contra mutaciones directas vía RPC/ORM), M-2 (reversa con locks de capacidad), M-4 (trazabilidad encadenada origin↔reversed), B-2 (líneas inmutables tras preparación) y B-3 (anulación con motivo obligatorio firmado).
- **FASE 12 — Operaciones (Bloques 1 y 2 CERRADOS):**
  - **Bloque 1 (AD-111):** WP-C (búsqueda por estado y submenú «Ingresos por Volúmenes»); WP-B rótulos (unificación de «Vol. Compra (m³)», «Vol. Export (m³)» y «Vol. Documental (m³)»); investigación D-E0-3 (guía 95806 / JCE -> "S.I.I.").
  - **Bloque 2 (AD-112):** WP-F P1–P5 (control de disponibilidad de etiquetas en imputación SV: `asignable`, `action_select_all` seguro, pestaña «Sin disponibilidad», resumen coherente, error nominativo); WP-E (plantilla estándar `PACKING_METRICO_ASERRADA.xlsx` y guía de llenado); WP-G (alineación documental canónica y wiki).

---

## 4. Reglas de Operación y Desarrollo
1. **Regla de Oro:** NUNCA documentar sin verificar contra el código real (`.py` y `.xml`).
2. **Restricción de Datos:** NO alterar datos de negocio históricos reales (`IMP04823`, `IMP02220`, guías reales).
3. **Control de Versiones:** Versiones monótonas en manifests, actualización obligatoria de `CHANGELOG.md` y commits locales con rutas explícitas sin push.
4. **Validación:** TDD estricto (RED -> GREEN) y regresión comparada por nombre de prueba.
