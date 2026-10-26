# ACLARACIÓN — Evidencia documental y cobertura del respaldo

## 1. Evidencia documental de la guía 33152 (exacta)

| Concepto | Cantidad | Detalle |
|---|---|---|
| `mail.message` existentes | **5** | notificaciones (ids 136411, 136412, 136414, 136415, 136416) |
| `ir.attachment` existentes | **4** | ids 65071–65074 |
| Mensajes incluidos en el snapshot | **4** | se **excluye el aviso automático de creación** |
| Adjuntos de chatter incluidos en el snapshot | **2** | `15183.xls` (65073), `GUIA 15183 MADENAT 02-09-2026.pdf` (65074) |
| Adjuntos de **campo binario** **excluidos** del snapshot | **2** | `guide_pdf_file` (65071), `excel_file` (65072) |

Detalle de adjuntos:

| id | name | store_fname | bytes | ¿en snapshot? |
|---|---|---|---|---|
| 65071 | `guide_pdf_file` (campo binario) | `0f/0fa994e5f3e215cd588fc971745e0e3ea0847553` | 240 505 | **No** |
| 65072 | `excel_file` (campo binario) | `82/82eab5a2ff2624cd72b454f8cb1f88ffd3f0eba7` | 50 176 | **No** |
| 65073 | `15183.xls` (chatter) | `82/82eab5a2ff2624cd72b454f8cb1f88ffd3f0eba7` | 50 176 | **Sí** |
| 65074 | `GUIA 15183 MADENAT 02-09-2026.pdf` (chatter) | `0f/0fa994e5f3e215cd588fc971745e0e3ea0847553` | 240 505 | **Sí** |

> **El snapshot firmado de eliminación NO es un inventario documental completo.**
> Preserva metadatos de **4 mensajes y 2 adjuntos de chatter**. **No** conserva los
> 2 adjuntos de **campo binario** (`guide_pdf_file`, `excel_file`). No se modifica el
> código para ampliar el snapshot en esta fase.

## 2. Cobertura del respaldo protegido (comprobación de contenido — NO restauración)

Respaldo: `backups/FASE_B_20261007_153214/` (`madenat_test.dump` + `filestore_madenat_test.tar.gz`).

**2.1 Guía en la base de datos (lectura del dump, sin restaurar):**

- Extracción de datos `pg_restore -a -t madenat_guia_processing -f -` del dump.
- Resultado: **1 fila** con `id=33152`; contiene los tokens `15183`, `cancelled`, `service`.
- Evidencia: `verif_dump_guia_33152.sql`.

**2.2 Adjuntos en la base de datos (lectura del dump):**

- Extracción `pg_restore -a -t ir_attachment -f -` del dump.
- Resultado: **4 filas** `65071–65074`, con `name` y `store_fname` esperados.
- Evidencia: `verif_dump_adjuntos_65071_65074.sql`.

**2.3 Archivos físicos en el filestore de respaldo:**

- El tar contiene los **2 archivos físicos** que cubren los 4 adjuntos
  (direccionados por contenido; 65071≡65074 y 65072≡65073):
  - `madenat_test/0f/0fa994e5f3e215cd588fc971745e0e3ea0847553`
  - `madenat_test/82/82eab5a2ff2624cd72b454f8cb1f88ffd3f0eba7`
- **sha256 respaldo == sha256 volumen en vivo**:
  - `6f45b61d6bd2234ae2972b9ec30c27947a156da01f8d0a0af365f3a102ea9a03` (0fa994…)
  - `c456c794fcc03b65fde27fce2fd19890bdbd915b377413d0938a076684e3c732` (82eab5…)
  - Tamaños: 240 505 y 50 176 bytes (coinciden con `ir_attachment.file_size`).

## 3. Distinción exigida

- Lo anterior es **comprobación de contenido** (lectura del dump y comparación de hashes
  tar ↔ volumen). **NO** es una **restauración de prueba**: no se recreó la base ni se
  reextrajo un entorno funcional desde el respaldo.
- **Cobertura:** los 4 adjuntos y la guía **están cubiertos** por el respaldo protegido
  (guía en el dump; archivos físicos en el filestore con hash verificado). **No** hay
  archivo sin cobertura comprobada.
- **Límite:** el respaldo permite **recuperación completa** (restaurando dump + filestore),
  pero esa restauración **no** se ha ejecutado ni probado.
