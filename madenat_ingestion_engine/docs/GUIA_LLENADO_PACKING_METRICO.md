# Guía de Llenado: Plantilla Estándar de Packing List (Sistema Métrico)

**Módulo**: `madenat_ingestion_engine`  
**Perfil**: `packing_metrico_aserrada`  
**Archivo Plantilla**: [`data/templates/PLANTILLA_PACKING_METRICO_ASERRADA.xlsx`](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_ingestion_engine/data/templates/PLANTILLA_PACKING_METRICO_ASERRADA.xlsx)  
**Versión**: 1.0  
**Fecha**: 2026-10-17  

---

## 1. Propósito y Alcance

Esta plantilla define el formato estándar para el ingreso de recepciones de madera aserrada (seca cepillada o verde) bajo el **sistema métrico** (`mm / m`), especialmente indicada para:
1. Proveedores y aserraderos que no cuentan con lector automático específico de DTE/PDF (por ejemplo: Arauco, JCE, BYC, Fátima).
2. Procesos de digitación o carga manual asistida por operaciones.
3. Ingesta a través del motor `madenat_ingestion_engine`, garantizando normalización limpia hacia el contrato unificado de cabecera y líneas sin requerir código a la medida por proveedor.

---

## 2. Estructura del Archivo Excel

El archivo contiene una cabecera de metadatos en las primeras filas, seguida de la tabla de detalle con 11 columnas homologadas.

### 2.1 Metadatos de Cabecera (Fila 2)

Los metadatos se ubican en pares `ETIQUETA` | `VALOR` y son extraídos automáticamente por el motor:

| Etiqueta | Celda | Ejemplo | Campo Extraído | Descripción |
| :--- | :---: | :--- | :--- | :--- |
| `CLIENTE` | `A2:B2` | `MADENAT S.A.` | `customer_name` | Razón social o nombre del cliente / consignatario |
| `GUIA DESPACHO` | `D2:E2` | `12345` | `guide_number` | Folio de la guía de despacho de origen |
| `FECHA` | `G2:H2` | `2026-10-17` | `guide_date` | Fecha de emisión de la guía (`YYYY-MM-DD`) |
| `ORDEN COMPRA` | `J2:K2` | `OC-2026-001` | `oc_reference` | Orden de compra asociada (opcional) |

### 2.2 Columnas de Detalle (Fila 4 en adelante)

| Columna | Nombre Cabecera | Unidad / Formato | Obligatorio | Descripción y Reglas de Validación |
| :---: | :--- | :---: | :---: | :--- |
| **A** | `N°` | Entero | Sí | Número de paquete o tarja correlativo (`1, 2, 3...`). |
| **B** | `CODIGO` | Texto | Sí | Código de producto o SKU de la escuadría (ej: `1000203040501`). |
| **C** | `PRODUCTO` | Texto | Sí | Descripción de la madera (ej: `PINO ASERRADO SECO KD`). |
| **D** | `LOTE` | Texto | Sí* | Identificador de etiqueta o lote del proveedor. (*Si viene vacío, el motor sintetiza `LOTE-{CODIGO}`). |
| **E** | `ESPESOR` | Milímetros (`mm`) | Sí | Espesor nominal. Para sistema métrico debe ser `>= 10 mm` (ej: `38.1, 45.0, 50.0`). |
| **F** | `ANCHO` | Milímetros (`mm`) | Sí | Ancho nominal de la pieza (ej: `125.0, 150.0, 170.0`). |
| **G** | `LARGO` | Metros (`m`) | Sí | Largo nominal de la pieza (ej: `3.60, 4.00, 4.05`). |
| **H** | `FILAS` | Entero | Opcional | Número de capas verticales de madera en el paquete. |
| **I** | `COLUMNAS` | Entero | Opcional | Número de piezas por capa a lo ancho del paquete. |
| **J** | `PIEZAS` | Entero | Sí | Cantidad total de piezas contenidas en el paquete físico. |
| **K** | `VOLUMEN` | Metros Cúbicos (`m³`) | Sí | Volumen métrico total del paquete. |

---

## 3. Fórmulas y Cálculos Estándar

### 3.1 Cálculo del Volumen Métrico ($m^3$)

$$\text{Volumen } (m^3) = \frac{\text{Espesor } (mm)}{1000} \times \frac{\text{Ancho } (mm)}{1000} \times \text{Largo } (m) \times \text{Piezas}$$

*Ejemplo*:  
- Espesor = $38.1\text{ mm}$
- Ancho = $170\text{ mm}$
- Largo = $4.05\text{ m}$
- Piezas = $150$  
$$\text{Volumen} = 0.0381 \times 0.170 \times 4.05 \times 150 = 3.935\text{ } m^3$$

### 3.2 Relación de Piezas en Paquete Regular

$$\text{Piezas} = \text{Filas} \times \text{Columnas}$$

En caso de paquetes despuntados o incompletos, el valor de la columna `PIEZAS` prevalece sobre el producto filas × columnas.

---

## 4. Detección y Comportamiento del Motor (`madenat_ingestion_engine`)

1. **Autodetección de Perfil**: El motor inspecciona las primeras filas de datos. Si el valor de la columna `ESPESOR` es numérico y $\ge 10$, clasifica el archivo automáticamente bajo `packing_metrico_aserrada`.
2. **Normalización de Texto**: Las tildes, mayúsculas/minúsculas y caracteres ordinales (`N°`, `Nº`, `N`) son normalizados sin distorsión.
3. **Manejo de Lotes Omitidos**:
   - Si una fila tiene `LOTE` vacío pero la fila anterior tenía lote, se aplica **forward-fill** (herencia).
   - Si ninguna fila previa tenía lote, se genera un lote sintetizado: `LOTE-{CODIGO}`.
4. **Filas Vacías**: Filas intermedias o al final sin datos son ignoradas automáticamente sin generar errores ni advertencias espurias.
