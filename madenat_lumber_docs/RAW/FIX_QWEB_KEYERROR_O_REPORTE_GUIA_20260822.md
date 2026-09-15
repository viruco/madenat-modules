# Fix — QWeb KeyError 'o' en reporte de guía

## Error observado
`QWebException KeyError: 'o'` en el template `madenat_lumber_core.report_madenat_guia_document`, nodo `<span t-field="o.name"/>`, al generar el PDF vía `_render_qweb_pdf()`.

## Causa técnica
El template llamaba `t-call="web.external_layout"` directamente (L4) **sin definir `o`** en el contexto: no había `t-foreach="docs"` ni `t-set="o"`. Los reportes QWeb proveen `docs`, `doc_ids`, `doc_model` por defecto, pero no `o`.

## Estructura previa del template
```xml
<template id="report_madenat_guia_document">
    <t t-call="web.external_layout">
        <div class="page"> ... <span t-field="o.name"/> ... </div>
    </t>
</template>
```

## Cambio aplicado (Opción 1 — estándar)
```xml
<template id="report_madenat_guia_document">
    <t t-foreach="docs" t-as="o">
        <t t-call="web.html_container">
            <t t-call="web.external_layout">
                <div class="page"> ... </div>
            </t>
        </t>
    </t>
</template>
```
`o` queda definido por iteración de `docs`; el contenido del PDF se preserva intacto (sin renombrar campos).

## Validación ejecutada
- XML válido (`ElementTree.parse`): `FOREACH=docs | AS=o | hijo1=t (html_container) | hijo2=t (external_layout)`.
- Sin tests de reporte en el módulo; se documenta validación manual/técnica.

## Resultado esperado en UAT
- Descarga/impresión del PDF sin `RPC_ERROR`/`KeyError: 'o'`.
- Mantener: o.name, o.partner_id.name, o.date_processed, o.processing_line_ids, o.vol_fisico, o.total_paquetes.

## Riesgos y límites
- Solo estructura QWeb modificada; sin cambios de lógica de negocio, modelos ni core.
- Se recomienda UAT con 1-2 guías reales para confirmar el PDF completo.