# PROMPT — CONSOLIDACIÓN DE DOCUMENTACIÓN, FASE 2: EJECUCIÓN

> Copia operativa del encargo ejecutado el 2026-10-26. Guardada en la ubicación canónica de la fase
> (`custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/`) al consolidar la documentación (E3).
> Las referencias de ruta del texto original se han mantenido literales tal como se emitieron.

---

Lee primero .clinerules/madenat-regla-de-oro.md. Regla de Oro completa, un paso a la vez, evidencia en cada afirmación ([VERIFICADO] / [INFERENCIA] / [NO VERIFICADO]). Prohibido git add -A. Commits pequeños con git add por ruta. No toques .obsidian/, LEGADO/ (salvo lo indicado), backups/ del repo, ni los 11 cambios ajenos de costing/* y lumber_reports_menu.xml. No modifiques código de módulos salvo en el punto de control C2, con autorización.

## DECISIONES APROBADAS

D1. madenat_lumber_docs sigue dentro del repo custom_addons (rama fase13-2a-lectura).
D2. Huecos CANON 01, 06, 09, 10 y 14 bloqueados (no reutilizar); se registran como "reservado" en el índice. Números nuevos desde 21.
D3. Renombrar CANON/05_AUDITORIA_XML_IDS.md a 20_AUDITORIA_XML_IDS.md con git mv y actualizar sus referencias (WIKI/00_INDICE.md:27, CANON/INDICE_DOCUMENTACION.md:129, RAW/IMPLEMENTACION_IDENTIFICACION_OPERATIVA_LOTES_R1_20260925.md:152,164). Revisa con grep que no queden otras.
D4. Mover la documentación dispersa a madenat_lumber_docs/FASES/<NOMBRE_CARPETA>/ (informes, PROMPT_*, evidencias, CSV, scripts de auditoría pequeños). Aplica los filtros de F2.
D5. Congelar en el repo la evidencia 2B/2D (CSV, scripts, logs 2d_upgrade*.log y dbg*). El dump de 11,7 MB va fuera de git, con su sha256 anotado.
D6. Los dos tests que dependen de xlsx ausentes se saltan con aviso si falta el archivo (punto de control C2; no antes).
D7. Las 21 carpetas espejo se comprimen en .tar.gz en /home/viruco/dev-stack/backups/ (fuera de git); el original se elimina solo con autorización (C1).

NO SE MUEVEN: CANON/00..19 (excepto el rename D3), INDICE_DOCUMENTACION.md, README/CHANGELOG de cada módulo, fixtures de tests, data/templates/*.xlsx y docs/ del madenat_ingestion_engine, .clinerules/ (en la raíz).

## ETAPAS (un commit por etapa; reporta y espera mi OK solo donde diga PUNTO DE CONTROL)

E0. Detección de estado: git status por ruta, HEAD (esperado 1c14206), rama, árbol propio limpio. Crea un manifiesto de línea base: sha256 de todo archivo que se va a mover o tocar, con ruta origen (guárdalo en FASES/00_MANIFIESTO_CONSOLIDACION_ANTES.csv). Sin ese manifiesto no se mueve nada.

E1. Corregir el índice con evidencia. Compara las versiones y fechas declaradas en CANON/INDICE_DOCUMENTACION.md (02 v12.50.0, 03 v6.43.0, 04 v12.53.0, 12 v1.21.0; fecha 2026-10-21 con filas del 2026-10-26) con las de los propios documentos (12.49.0, 6.42.0, 12.52.0, 1.20.0). Determina por git log -p y por el contenido cuál refleja la realidad. Corrige el lado equivocado. Corrige WIKI/00_INDICE.md (cita INDICE v10.0.0; lista 13 archivos CANON inexistentes) y añade a WIKI/00_INDICE.md los 4 archivos no indexados (madenat_lumber_logistics.md, roadmap_core.md, INC-011, sesión 2026-09-08). Commit docs.

E2. Rename D3 + registrar los huecos reservados (D2) en el índice con la nota "ARCHIVADO en LEGADO" (ya documentado: no reutilizar). Commit docs.

E4. Resto de carpetas de fase (87 en /home/viruco/dev-stack/odoo/odoo-18-ce, excluidas las 21 carpetas espejo y las de código): clasifica cada una con el siguiente filtro y entrega la tabla antes de mover:
  - Va a git (FASES/<carpeta>/): .md, .txt, .csv, .pdf/.xlsx de documentación cuando pesen menos de 2 MB cada uno.
  - NO va a git: addons/, workcopy/, verify_*/, respaldos, *.dump, *.sql, *.tar*, *.log mayores de 1 MB y cualquier binario mayor de 2 MB. Van comprimidos a /home/viruco/dev-stack/backups/<carpeta>.tar.gz con sha256.
  Mueve por tandas de máximo 10 carpetas, un commit por tanda, con manifiesto de cada tanda. Crea FASES/00_INDICE_FASES.md (carpeta, fecha, resumen de una línea, estado, ruta nueva, dónde quedó lo no versionado). Si una carpeta mezcla documentación y código, divídela y documenta la división.

E5. Scripts sueltos (13 en la raíz de odoo-18-ce) a LEGADO/auditorias/scripts/ con git add por ruta. Excepción: run_tests.sh y deploy_production.sh siguen citados por CANON/11 y por el flujo de despliegue; déjalos donde están y documenta por qué (o actualiza la cita si lo mueves; dime cuál elegiste).

E6. Crear RAW/00_INDICE_RAW.md que liste los 33 documentos de RAW (30 hoy sin referencias) con fecha, tema y estado; añadir ambos nuevos índices (FASES y RAW) a CANON/INDICE_DOCUMENTACION.md como anexo, sin tocar los números de los canónicos. Registrar la consolidación como AD en CANON/04_DECISION_LOG.md (formato y numeración existentes; solo lo [VERIFICADO]) y en 02_CONTINUIDAD.md.

E7. Verificación global antes del punto de control: (a) script que valide todos los enlaces relativos de CANON, WIKI, RAW y FASES (esperado 0 rotos); (b) comparar sha256 de todo lo movido contra el manifiesto; (c) grep de cada ruta antigua en todo custom_addons y .clinerules (esperado 0); (d) git status final con solo los 11 cambios ajenos.

PUNTO DE CONTROL C1 (me presentas, no ejecutes): informe de E0 a E7 con tablas, y la lista de originales que se podrían eliminar con su verificación sha256. Elimina SOLO lo que yo autorice explícitamente. Después: archivar las 21 carpetas espejo en .tar.gz (D7), verificar los archivos y esperar mi autorización para borrar originales.

PUNTO DE CONTROL C2 (requiere mi autorización previa; es código): (1) clonar madenat_test a una BD temporal y correr una línea base de las suites de madenat_lumber_core y madenat_lumber_logistics (reportando los rojos preexistentes, por ejemplo TestSvConcurrency.test_01); (2) con esa base, proponer el diff para que los tests de test_consolidation_import_wizard.py:65-66 se salten con aviso si falta el xlsx. No lo apliques sin OK; si lo aplico, commit aparte de código con su test, y vuelve a correr la suite del módulo.

ACTUALIZACIÓN DE REGLAS (con mi autorización en C1): propón el diff para .clinerules/madenat-regla-de-oro.md: la documentación vive en madenat_lumber_docs; rutas de FASES/, RAW/ y CANON/; citar siempre el nombre completo (CANON/20_… y no "CANON/05"); y no crear carpetas de fase nuevas fuera de madenat_lumber_docs/FASES/.

## ENTREGA Y CIERRE

- Guarda este prompt en madenat_lumber_docs/FASES/FASE13_20261023/PROMPT_CONSOLIDACION.md.
- Reporta por etapa: commits (hash y mensaje), archivos movidos (conteo y peso), verificaciones sha256 y de enlaces, lo que quedó fuera de git y dónde.
- Si algo no cuadra (hash distinto, enlace roto, referencia no encontrada, carpeta ambigua), detente, repórtalo y no corrijas.
- Cierra con la frase exacta: "CONSOLIDACIÓN DOCUMENTAL COMPLETADA — A LA ESPERA DE REVISIÓN". No inicies el tramo 3 de la 2B ni la Fase 2C.


E3. Mover FASE13_INTAKE_ENGINE_20261023/ a madenat_lumber_docs/FASES/FASE13_20261023/ (informes 2A/2B/FRENTE_A/FRENTE_B, PROMPT_2D, evidencias/ y logs/scripts congelados de /tmp según D5). Pasos: copiar, comparar sha256 contra el manifiesto, git add por ruta. Actualiza las 4 referencias con ruta literal (CANON/04_DECISION_LOG.md:4271, PROMPT_2D.md:4,33, INFORME_FASE_2B.md:209-210,1663,1731-1732,1744-1745) y reemplaza las rutas absolutas de fase13_md5_vs_csv_compare.py:13,23 por rutas relativas. Comprueba que los md5 45ad1588… y 02d6284d… siguen coincidiendo con los CSV movidos y que el script devuelve exit 0. Commit docs. No borres el original todavía.
