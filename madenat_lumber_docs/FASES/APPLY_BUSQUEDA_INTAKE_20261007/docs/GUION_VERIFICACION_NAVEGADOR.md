# GUION_VERIFICACION_NAVEGADOR (V3) — pendiente de comprobar

Entorno: `madenat_test` local (`http://127.0.0.1:8069`).
Usuario: **operativo** de `group_madenat_operaciones` (no administrador).
Ruta: **MADENAT Lumber → Operaciones → Abastecimiento → Gestión de Entradas → Ingreso de Madera**.

> Estado: **V3 NO ejecutada**. Este guion es para la comprobación real. No se
> declara "UI verificada" hasta completarlo.

## 1. OC documental vs OC vinculada
1. En la lista, la columna **"OC documental"** muestra la referencia del documento
   (p. ej. `MC - 2506 - 01`). Abrir una fila e ir al bloque Resumen: deben verse
   **"OC documental"** (referencia) y **"OC vinculada"** (relación interna) como dos
   datos distintos.
2. Menú **Filtros → Agrupar por → "OC documental"**: aparecen grupos por referencia
   real (no un único grupo "(No definido)").
3. **Agrupar por → "OC vinculada"**: como hoy no hay OC vinculadas, un solo grupo vacío.
4. **Filtros**: "OC vinculada", "OC pendiente de vinculación", "OC no indicada" → los
   conteos deben cuadrar (en la base: 0 / 15 / 3).

## 2. Fechas (emisión vs recepción)
5. En la lista, junto a **"Fecha de guía"**, la columna **"Origen fecha"** muestra un
   badge **"Emisión de guía (documento)"** o **"Recepción al sistema"**.
6. **Agrupar por → "Origen de fecha"**: dos grupos (Emisión / Recepción).

## 3. Producto real
7. En la barra de búsqueda, campo **"Producto (contiene)"**: elegir un producto →
   la lista trae los ingresos **cuyas líneas** contienen ese producto, tanto de
   **Producto** como de **Procesado**, **sin filas duplicadas**.

## 4. Procesador
8. Campo **"Procesador"** y **Agrupar por → "Procesador"**. Para guías de servicio con
   Orden de Procesamiento debe mostrar la planta procesadora; en Producto queda vacío.
   Verificar que **no** coincide con el "Proveedor".

## 5. Combinaciones de filtros
9. **Producto + Volúmenes** (dos modalidades): debe dar **0 resultados** (AND).
10. **Producto + Verificado**: intersección coherente.
11. **OC pendiente de vinculación + Volúmenes**: solo guías de volumen con OC documental.
12. **Origen de fecha (Recepción) + Producto**: solo recepciones sin fecha de guía.

## 6. Navegación
13. Abrir una fila → **"Modificar origen"** → debe abrir el registro correcto
    (`lumber.reception` o `madenat.guia.processing`) y **volver** a Ingreso de Madera.

## 7. Registro de resultado
Anotar por cada punto: OK / discrepancia (con captura), y si algún filtro combinado
se comporta distinto a lo esperado. Si aparece divergencia, **no** aplicar más cambios
hasta revisarla.
