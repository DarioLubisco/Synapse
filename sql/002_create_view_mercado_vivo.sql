-- ============================================================
-- 002_create_view_mercado_vivo.sql
-- Vista consolidada de TODAS las tablas de proveedores
-- Normaliza las 5 variantes de columnas en una estructura única
-- Orden recomendado: ORDER BY codigo_barras, precio_unitario_final
-- ============================================================

IF EXISTS (SELECT * FROM sys.views WHERE name = 'Mercado_Vivo' AND schema_id = SCHEMA_ID('Analitica'))
    DROP VIEW [Analitica].[Mercado_Vivo];
GO

CREATE VIEW [Analitica].[Mercado_Vivo]
AS

-- ===== VARIANTE A: Estándar Completo (13 tablas) =====
SELECT proveedor, NULL AS sucursal, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL AS marca_proveedor, fecha_carga
FROM [Proveedores].[Andicar_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Biogenetica_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[BLV_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Cobeca13_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Cristmed_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Drodelca_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Dropharma_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Drosolveca_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Emmanuelle_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Gama_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Intercontinental_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[Mastranto_Inventario]

-- ===== VARIANTE B: Reducido — DROCERCA, ITS, NENA =====
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, NULL AS pct_oferta_vigente, precio_unitario_final,
       stock_disponible, NULL AS articulo_indexado, NULL AS descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[DROCERCA_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, NULL, precio_unitario_final,
       stock_disponible, NULL, NULL, NULL, fecha_carga
FROM [Proveedores].[ITS_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, NULL, precio_unitario_final,
       stock_disponible, NULL, NULL, NULL, fecha_carga
FROM [Proveedores].[NENA_Inventario]

-- ===== VARIANTE C: Extendido con Sucursal — Insuaminca x3 =====
UNION ALL
SELECT proveedor, sucursal, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, CAST(CASE WHEN indexado_monto = 'INDEXADO' THEN 1 ELSE 0 END AS BIT),
       NULL, marca_proveedor, fecha_carga
FROM [Proveedores].[InsuamincaM_Inventario]
UNION ALL
SELECT proveedor, sucursal, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, CAST(CASE WHEN indexado_monto = 'INDEXADO' THEN 1 ELSE 0 END AS BIT),
       NULL, marca_proveedor, fecha_carga
FROM [Proveedores].[InsuamincaB_Inventario]
UNION ALL
SELECT proveedor, sucursal, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente, precio_unitario_final,
       stock_disponible, CAST(CASE WHEN indexado_monto = 'INDEXADO' THEN 1 ELSE 0 END AS BIT),
       NULL, marca_proveedor, fecha_carga
FROM [Proveedores].[InsuamincaG_Inventario]

-- ===== VARIANTE D: Nombres diferentes — VitalClinic, Zakipharma =====
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, pct_oferta_vigente_dp AS pct_oferta_vigente, precio_unitario_final,
       stock_disponible, articulo_indexado, descuento_adicional_da AS descuento_adicional, NULL, fecha_carga
FROM [Proveedores].[VitalClinic_Inventario]
UNION ALL
SELECT proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_lote, precio_unitario, porcentaje_oferta_vigente AS pct_oferta_vigente, precio_unitario_final,
       stock_disponible, NULL, NULL, NULL, fecha_carga
FROM [Proveedores].[Zakipharma_Inventario]

-- ===== VARIANTE E: Email Ingestion =====
UNION ALL
SELECT proveedor_nombre AS proveedor, NULL, codigo_producto, codigo_barras, descripcion_producto,
       fecha_vencimiento AS fecha_lote, precio_unitario, NULL, NULL AS precio_unitario_final,
       stock_disponible, NULL, NULL, NULL, fecha_carga
FROM [Proveedores].[Email_Ingestion_Inventario]

GO

PRINT '✅ Vista [Analitica].[Mercado_Vivo] creada (21 tablas consolidadas).';
GO
