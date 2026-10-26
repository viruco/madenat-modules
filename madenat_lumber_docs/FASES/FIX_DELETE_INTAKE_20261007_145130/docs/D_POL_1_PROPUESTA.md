# D-POL-1 — Cierre de la decisión de política (propuesta concreta)

## Conclusión: **Opción B**

> **El FK del retorno 7813 es incorrecto y el retorno pertenece materialmente a otra
> cabecera (la cadena de la recepción 1369, vía el receipt 436).**

No es “opción A” (no es un retorno propio de la guía: la guía **no** tiene movimientos
propios). No es “opción C” (la atribución **no** es ambigua: hay evidencia material
concluyente). Ver `REPRODUCCION_CADENA_436_7813_7814.md`.

Evidencia (no inferencia) que sustenta B:

1. `7813.move_id.origin_returned_move_id = 6420` (el move del receipt **436**).
2. Los 12 lotes de 7813 pertenecen a la **recepción 1369** (`reception_id=1369`).
3. La guía 33152 tiene **0 lotes propios** y **0 movimientos propios**.
4. El FK de 7813 es el **único** vínculo con la guía y proviene del **contexto**
   (mecanismo reproducido), no de una relación operativa.

## Qué implica la opción B

1. **El parche de atribución es correcto** y se mantiene: el Modo A **bloquea** mientras
   exista el FK espurio (no se inventa una excepción para “permitir borrar”).
2. Para poder eliminar 15183 hace falta **reparar el dato** (retirar el FK espurio de 7813),
   mediante un **procedimiento separado**, con **autorización propia**, **sin** ejecutarlo
   ahora y **preservando** todo el histórico material.
3. No se cambia ninguna política ni se incorpora nada a CANON: se corrige un dato que
   quedó mal atribuido por un defecto de código ya corregido (`02` + `03`).

## Lo que NO se hace

* **No** se propone “ignorar los retornos derivados de cancelación” de forma global
  (eso ocultaría el defecto y podría dejar trazabilidad rota).
* **No** se borra ni reasigna el retorno real 7813 automáticamente.
* **No** se borra la cabecera dejando referencias colgantes: al reparar el FK, el retorno
  7813 conserva íntegra su cadena (`origin='Return of EMB-00227'`, moves, lotes) que apunta
  al **receipt 436**, que sobrevive. Eliminar la guía **no** rompe esa traza.

## Sobre “borrar una cabecera conservando referencias históricas”

Ni siquiera hace falta un cambio de doctrina: la guía 33152 **no** es referenciada
materialmente por ningún documento (el único vínculo era el FK espurio). Con el FK
reparado, la eliminación de la guía es **limpia**: no deja trazabilidad rota porque la
trazabilidad material pertenece a la recepción 1369, intacta. La evidencia documental de la
guía (5 mensajes + 4 adjuntos) se conserva en el **snapshot firmado** de auditoría
(`madenat.audit.log`, convención BT-01) al eliminar en dev; en producción, el Modo A
bloquearía por evidencia (política vigente) y habría que decidir su tratamiento aparte.

## Respuesta requerida

> **“Para eliminar 15183 falta exactamente** la **reparación autorizada del FK espurio de
> `stock.picking` 7813** (`guia_processing_id = NULL`), mediante un procedimiento separado
> —y la autorización operativa del borrado—. Con ese único cambio de dato, la guía 33152
> no tiene ninguna dependencia material propia y el Modo A procede en el entorno de
> desarrollo.”

No es una decisión de política abstracta: se resuelve **comprobando la atribución**, que ya
está comprobada (Opción B).
