# QUICK_START — madenat_lumber_core

**Estado:** Arquitectura modularizada, documentación alineada y continuidad técnica lista.  
**Objetivo:** Entender el estado actual del módulo en pocos minutos y continuar sin perder contexto.

## Qué revisar primero

1. `docs/RESUMEN_AUDITORIA_Y_DOCUMENTACION.md`.
2. `docs/00_ARQUITECTURA.md`.
3. `docs/03_TESTS.md`.
4. `docs/02_CONTINUIDAD.md`.
5. `docs/ROADMAP.md`.

## Estado resumido

- Arquitectura modular operativa, con servicios extraídos para parser, workflow y stock.
- Imports y sintaxis verificados.
- 14 tests core documentados como pasando en la matriz principal.
- Despliegue Docker validado.
- Próximo foco funcional: Fase 6, integración financiera.

## Comandos útiles

```bash
docker ps | grep odoo18
pytest tests/ -v
python -m py_compile models/lumber_reception.py
```

## Qué significa el estado actual

El módulo está estable para continuidad técnica. La documentación principal ya refleja el estado modular real y permite que otro desarrollador retome el trabajo con rapidez.

## Archivos clave

| Archivo | Para qué sirve |
|---|---|
| `docs/RESUMEN_AUDITORIA_Y_DOCUMENTACION.md` | Entrada principal del proyecto. |
| `docs/00_ARQUITECTURA.md` | Mapa de arquitectura y responsabilidades. |
| `docs/03_TESTS.md` | Evidencia de validación funcional. |
| `docs/02_CONTINUIDAD.md` | Guía para seguir desarrollando. |
| `docs/CHECKLIST_FINALIZACION.md` | Verificación previa a entrega. |

## Siguiente paso recomendado

Iniciar la lectura por el resumen maestro y después validar la arquitectura y los tests antes de tocar nuevas funcionalidades.
