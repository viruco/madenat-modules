# Propuesta de ampliación de `.clinerules/madenat-regla-de-oro.md` — **NO APLICADA**

**Fecha:** 2026-10-26
**Archivo destino:** `/home/viruco/dev-stack/odoo/odoo-18-ce/.clinerules/madenat-regla-de-oro.md` (vive en la
raíz del repo Odoo, **fuera** de `custom_addons` y sin versionar: no lo cubre el repositorio de módulos).
**Estado:** el archivo original **no se ha tocado**; el diff se generó sobre una copia en `/tmp`.

## Diff propuesto

```diff
--- .clinerules/madenat-regla-de-oro.md
+++ .clinerules/madenat-regla-de-oro.md
@@ -39,7 +39,21 @@
 4. Levantar web y comprobar **HTTP 200** en `/web/login`.
 5. Comparar datos antes/después (md5 y conteos); solo registros **nuevos** pueden diferir.
 
-## 6. Cierre
+## 6. Documentación consolidada (FASE 13/2 y FASE 2)
+
+- **Una sola ubicación.** Toda la documentación vive en `custom_addons/madenat_lumber_docs/`. Prohibido crear
+  carpetas de fase (expedientes, auditorías, `FIX_*`, `APPLY_*`, `UAT_*`, `FASE*_*`) en la raíz del stack, en
+  `custom_addons/` ni en `backups/`: van a `madenat_lumber_docs/FASES/<CARPETA>/`.
+- **Rutas de destino.** `CANON/` para lo normativo vigente, `WIKI/` para guías y operación, `RAW/` para
+  insumos y auditorías sin dueño canónico, `FASES/` para expedientes de fase. `LEGADO/` es solo lectura.
+- **Citar siempre el nombre completo.** `CANON/20_AUDITORIA_XML_IDS.md`, nunca `CANON/20`, `CANON/05` ni «el
+  20»; igual con `RAW/…`, `WIKI/…` y `FASES/<CARPETA>/…`. Una cita ambigua se corrige al escribirla.
+- **Enlaces que se verifican.** Antes de cerrar un paso: 0 enlaces Markdown rotos y 0 rutas en backticks que
+  resuelvan solo en la raíz del stack (salvo rutas de módulos dentro de `custom_addons/`).
+- **Originales de la raíz.** No se borran hasta que el expediente esté consolidado, comprimido y verificado con
+  sha256; el borrado requiere autorización expresa y se hace por tandas.
+
+## 7. Cierre
 
 - Informe con: commits, pruebas (números reales), md5, estado de servicios, riesgos abiertos y punto
   de retoma.
```

## Por qué así

1. **Renumeración mínima.** La sección nueva entra como §6 y «Cierre» pasa a §7 para no dejar una sección
   normativa después del cierre de sesión.
2. **Coherente con lo ejecutado.** Las cinco reglas describen exactamente lo que se hizo en E3–E8 (destino
   `FASES/`, citas con nombre completo, verificación de enlaces, respaldo antes de borrar).
3. **Verificable.** La regla de enlaces usa las mismas dos comprobaciones del verificador
   (`check_links` / `check_paths`), no una aspiración genérica.

## Efecto de aplicarlo

- `.clinerules/madenat-regla-de-oro.md` sube de 6 a 7 secciones; ninguna regla existente cambia.
- Al no estar versionado, aplicarlo **no** genera commit en `custom_addons`: hay que copiarlo a mano o
  moverlo al repo (`custom_addons/.clinerules/`) si se quiere rastrear. Esa decisión no se toma aquí.
