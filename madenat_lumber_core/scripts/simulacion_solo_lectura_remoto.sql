-- =============================================================================
-- CONSULTA DE SOLO LECTURA: SIMULACIÓN DE IMPACTO ANCHO S2S (WP-B)
-- Autor: Mauricio / Antigravity
-- Base de datos objetivo: madenat_test (Local o TEST remoto)
-- Propósito: Medir la variación de volumen de exportación m3 sin alterar datos.
-- =============================================================================

WITH s2s_mapping AS (
    SELECT * FROM (VALUES
        (75, 2.625),
        (80, 2.750),
        (85, 2.9375),
        (90, 3.125),
        (100, 3.625),
        (105, 3.750),
        (110, 4.000),
        (115, 4.125),
        (120, 4.375),
        (125, 4.500),
        (130, 4.750),
        (140, 5.125),
        (145, 5.375), -- Valor Crítico
        (150, 5.500),
        (155, 5.750)
    ) AS t(ancho_mm, s2s_inches)
),
calculated_lines AS (
    SELECT
        l.id,
        p.name AS guia_name,
        l.lot_name,
        l.espesor_mm,
        l.ancho_mm,
        l.largo_m,
        l.pieces,
        l.vol_shipment_m3 AS vol_almacenado,
        CASE
            WHEN m.s2s_inches IS NOT NULL THEN
                ROUND(((l.espesor_mm * (m.s2s_inches * 25.4) * l.largo_m * l.pieces) / 1000000.0)::numeric, 3)
            ELSE
                ROUND(((l.espesor_mm * l.ancho_mm * l.largo_m * l.pieces) / 1000000.0)::numeric, 3)
        END AS vol_s2s_calculado
    FROM madenat_guia_processing_line l
    JOIN madenat_guia_processing p ON p.id = l.processing_id
    LEFT JOIN s2s_mapping m ON m.ancho_mm = ROUND(l.ancho_mm)
    WHERE p.state != 'cancel'
)
SELECT
    id,
    guia_name,
    lot_name,
    espesor_mm,
    ancho_mm,
    largo_m,
    pieces,
    vol_almacenado,
    vol_s2s_calculado,
    ROUND((vol_s2s_calculado - vol_almacenado)::numeric, 3) AS delta_m3,
    CASE
        WHEN vol_almacenado > 0 THEN
            ROUND((((vol_s2s_calculado - vol_almacenado) / vol_almacenado) * 100.0)::numeric, 2)
        ELSE 0.0
    END AS pct_cambio
FROM calculated_lines
ORDER BY id;

-- Resumen global:
WITH s2s_mapping AS (
    SELECT * FROM (VALUES
        (75, 2.625), (80, 2.750), (85, 2.9375), (90, 3.125),
        (100, 3.625), (105, 3.750), (110, 4.000), (115, 4.125),
        (120, 4.375), (125, 4.500), (130, 4.750), (140, 5.125),
        (145, 5.375), (150, 5.500), (155, 5.750)
    ) AS t(ancho_mm, s2s_inches)
),
totals AS (
    SELECT
        COUNT(*) AS total_lineas,
        SUM(l.vol_shipment_m3) AS total_vol_almacenado,
        SUM(
            CASE
                WHEN m.s2s_inches IS NOT NULL THEN
                    ROUND(((l.espesor_mm * (m.s2s_inches * 25.4) * l.largo_m * l.pieces) / 1000000.0)::numeric, 3)
                ELSE
                    ROUND(((l.espesor_mm * l.ancho_mm * l.largo_m * l.pieces) / 1000000.0)::numeric, 3)
            END
        ) AS total_vol_s2s,
        COUNT(CASE WHEN ABS(
            (CASE WHEN m.s2s_inches IS NOT NULL THEN ROUND(((l.espesor_mm * (m.s2s_inches * 25.4) * l.largo_m * l.pieces) / 1000000.0)::numeric, 3)
             ELSE ROUND(((l.espesor_mm * l.ancho_mm * l.largo_m * l.pieces) / 1000000.0)::numeric, 3) END) - l.vol_shipment_m3
        ) >= 0.001 THEN 1 END) AS lineas_con_cambio
    FROM madenat_guia_processing_line l
    JOIN madenat_guia_processing p ON p.id = l.processing_id
    LEFT JOIN s2s_mapping m ON m.ancho_mm = ROUND(l.ancho_mm)
    WHERE p.state != 'cancel'
)
SELECT
    total_lineas,
    lineas_con_cambio,
    ROUND(total_vol_almacenado::numeric, 3) AS vol_almacenado_m3,
    ROUND(total_vol_s2s::numeric, 3) AS vol_s2s_m3,
    ROUND((total_vol_s2s - total_vol_almacenado)::numeric, 3) AS delta_m3,
    ROUND((((total_vol_s2s - total_vol_almacenado) / NULLIF(total_vol_almacenado, 0)) * 100.0)::numeric, 2) AS delta_pct
FROM totals;
