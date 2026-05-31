# ESTADO DEL MÓDULO — madenat_lumber_core

## Estado canónico

El módulo `madenat_lumber_core` se encuentra en un estado de **arquitectura modular operativa con desacoplamiento parcial**. [file:123]

La implementación actual confirma la existencia y uso real de componentes desacoplados para validación, orquestación y persistencia de inventario, incluyendo `ingestiongate.py`, `receptionworkflow.py` y `receptionservice.py`. [file:122][file:123]

Sin embargo, el desacoplamiento estructural **no puede considerarse completamente cerrado**, ya que persisten concentraciones significativas de lógica en archivos de gran tamaño, principalmente `models/lumber_reception.py` con 2440 líneas y `models/madenat_guia_processing.py` con 3458 líneas. [file:123]

Por lo tanto, el estado correcto del módulo es:

- Arquitectura modular funcional: **sí**. [file:122]
- Gates 0–3 implementados y operativos: **sí**. [file:122]
- Firma SHA-256 y blindaje de Gate 3: **sí**. [file:122][file:123]
- Refactor monolítico total: **no**. [file:123]
- Deuda de desacoplamiento remanente: **sí, mitigada pero vigente**. [file:123]

## Capacidades confirmadas

### 1. Pipeline de validación por Gates

El módulo implementa una arquitectura de validación por etapas mediante `Gate0PreUpload`, `Gate1DocumentReconciliation`, `Gate2CommercialAnalysis` y `Gate3PreCommit`, definidos en `models/ingestiongate.py`. [file:122]

La evidencia también muestra que estos Gates no son decorativos ni experimentales, sino que están integrados en el flujo principal desde `lumber_reception.py` y `receptionworkflow.py`. [file:122]

### 2. Orquestación y servicios extraídos

La lógica desacoplada incluye al menos estos componentes funcionales:

- `receptionworkflow.py`: máquina de estados y pipeline de ingesta. [file:122]
- `receptionservice.py`: motor de inventario para creación de lotes y pickings. [file:122]
- `receptionparser.py`: parser de recepción desacoplado. [file:123]
- mixins de validación e ingesta: `mixinlumberingest.py`, `validationchecklistmixin.py`. [file:123]

Esto demuestra una refactorización real y ya integrada en producción técnica del módulo. [file:122][file:123]

### 3. Trazabilidad y blindaje criptográfico

La documentación y la implementación son consistentes en que Gate 3 concentra el write real de inventario y genera snapshot + firma SHA-256 para trazabilidad e integridad del proceso. [file:122][file:123]

Esta afirmación sí está sostenida por evidencia suficiente como para mantenerse como parte del estado canónico. [file:122]

### 4. Cobertura de pruebas

El módulo cuenta con al menos dos suites de prueba relevantes:

- `tests/testingestiongate.py` con foco en Gate 0 y Gate 1. [file:122][file:123]
- `tests/test_lumber_reception.py` con foco en volumen, lotes, service, Gate 3 y edge cases. [file:122][file:123]

No obstante, la narrativa documental actual presenta discrepancias en el conteo total de tests, ya que algunos documentos hablan de 14, otros de 16 y otros de T01–T28. [file:123]

## Deuda técnica vigente

Aunque el módulo está operativo y sustancialmente refactorizado, las siguientes deudas siguen vigentes:

- Persistencia de archivos gigantes (`lumber_reception.py`, `madenat_guia_processing.py`). [file:123]
- Artefactos no productivos en repositorio: `views.backup`, `models/0`, `madenat_addons.tar.gz`, `__pycache__`. [file:123]
- Desalineación documental entre roadmap, resumen ejecutivo, backlog y continuidad. [file:123]
- Warnings operativos recientes de Odoo no absorbidos aún por la documentación canónica, incluyendo temas de `selection_add`, parámetros inválidos, manifests sin `license`, y validaciones de vistas. [file:48][file:122]

## Declaración oficial

La posición oficial del proyecto debe ser la siguiente:

> `madenat_lumber_core` es un módulo funcional, modularizado y trazable, apto para continuidad de desarrollo, pero aún no completamente desacoplado en términos estructurales. La deuda remanente no bloquea la operación actual, pero sí debe permanecer explícitamente registrada en backlog y documentación canónica. [file:123]

## Qué no debe volver a afirmarse

A partir de ahora, estos enunciados deben evitarse o corregirse:

- “Monolito destruido exitosamente”. [file:123]
- “0 código espagueti”. [file:122]
- “0 deuda técnica crítica” como afirmación absoluta. [file:123]
- “Arquitectura 100% delegada” sin matices. [file:122]

## Próximo foco

El siguiente foco razonable del proyecto es continuar la evolución funcional del módulo sin perder disciplina arquitectónica, manteniendo una línea de trabajo dual:

1. evolución de negocio e integración financiera, [file:123]
2. reducción progresiva de deuda estructural residual. [file:123]