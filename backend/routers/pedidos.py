import os
import io
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import pyodbc
import math
import database

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

# Ruta absoluta/relativa a la query
QUERY_PATH = os.path.join(os.path.dirname(__file__), "..", "queries", "pedidos.sql")

def load_query():
    try:
        with open(QUERY_PATH, 'r', encoding='utf-8-sig') as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Error cargando query de pedidos: {e}")
        return None

@router.get("/categories")
async def get_categories():
    try:
        conn = database.get_db_connection()
        query = """
            SELECT CodInst, Descrip, InsPadre 
            FROM dbo.SAINSTA 
            ORDER BY Descrip
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Limpieza básica
        df = df.dropna(subset=['Descrip']).copy()
        df = df[df['Descrip'].str.strip() != '']
        
        categories = []
        for _, row in df.iterrows():
            categories.append({
                "id": str(row['CodInst']),
                "name": str(row['Descrip']).strip(),
                "parentId": str(int(row['InsPadre'])) if pd.notna(row['InsPadre']) else "0"
            })
        
        return {"categories": categories}
    except Exception as e:
        logging.error(f"Error fetching categories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_report(
    pedido_days: str = Form(...),
    num_rows: int = Form(...),
    categories: Optional[str] = Form(None),
    subtraction_files: Optional[List[UploadFile]] = File(None),
    umbral_rotacion: float = Form(0.0),
    forced_includes: Optional[str] = Form(None),
    preview_mode: str = Form("false"),
    is_generic: str = Form("false")
):
    try:
        query = load_query()
        if not query:
            raise HTTPException(status_code=500, detail="No se pudo cargar la consulta SQL maestra.")

        if is_generic.lower() == "true":
            query = query.replace('AND NOT EXISTS (', 'AND EXISTS (')

        # Validar entradas
        if num_rows <= 0:
            num_rows = 5000
        
        # Procesar archivos de resta
        subtraction_dfs = []
        if subtraction_files:
            for file in subtraction_files:
                if file.filename:
                    try:
                        content = await file.read()
                        if len(content) > 0:
                            df_sub = pd.read_excel(io.BytesIO(content))
                            subtraction_dfs.append(df_sub)
                    except Exception as e:
                        logging.warning(f"Error procesando archivo de resta {file.filename}: {e}")

        # Ejecutar Query Maestra
        conn = database.get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            raise HTTPException(status_code=404, detail="No se encontraron datos en la base de datos para generar el pedido.")

        # Filtrar por categorías si aplica
        if categories:
            parsed_categories = [cat.strip() for cat in categories.split(",") if cat.strip()]
            if 'Instancia' in df.columns:
                df = df[df['Instancia'].isin(parsed_categories)]

        # Lógica de Generación (Cálculo dinámico en Python)
        df['RotacionMensual'] = pd.to_numeric(df.get('RotacionMensual', 0.0), errors='coerce').fillna(0.0)
        df['Existen'] = pd.to_numeric(df.get('Existen', 0), errors='coerce').fillna(0)
        
        try:
            days = float(pedido_days)
        except ValueError:
            days = 14.0
            
        df['CANTIDAD'] = (df['RotacionMensual'] * days / 30.0) - df['Existen']
        df['CANTIDAD'] = df['CANTIDAD'].round().astype(int)

        cols_to_keep = ['CodProd', 'CANTIDAD', 'RotacionMensual', 'Existen']
        if 'Descrip' in df.columns: cols_to_keep.append('Descrip')
        
        df_final = df[cols_to_keep].copy()
        df_final.rename(columns={'CodProd': 'BARRA'}, inplace=True)

        # Aplicar Resta si hay archivos
        if subtraction_dfs:
            valid_sub_dfs = []
            for sub_df in subtraction_dfs:
                if not sub_df.empty and 'BARRA' in sub_df.columns and 'CANTIDAD' in sub_df.columns:
                    sub_df['BARRA'] = sub_df['BARRA'].astype(str)
                    valid_sub_dfs.append(sub_df)
            
            if valid_sub_dfs:
                combined_sub = pd.concat(valid_sub_dfs, ignore_index=True)
                agg_sub = combined_sub.groupby('BARRA', as_index=False)['CANTIDAD'].sum()
                
                df_merged = pd.merge(df_final, agg_sub, on='BARRA', how='left', suffixes=('', '_subtract'))
                df_merged['CANTIDAD_subtract'] = df_merged['CANTIDAD_subtract'].fillna(0)
                df_merged['CANTIDAD'] = df_merged['CANTIDAD'] - df_merged['CANTIDAD_subtract']
                df_final = df_merged.copy()

        df_final['RotacionMensual'] = pd.to_numeric(df_final['RotacionMensual'], errors='coerce').fillna(0.0)

        # Separar por umbral de rotación ANTES de filtrar CANTIDAD > 0
        # Excluidos: todos los que tengan rotación por debajo del umbral (para que el usuario los force si quiere)
        df_excluidos = df_final[df_final['RotacionMensual'] < umbral_rotacion].copy()
        df_excluidos = df_excluidos.drop_duplicates(subset=['BARRA'])

        # Prefiltrados: los que tienen buena rotación Y ADEMÁS tienen CANTIDAD calculada > 0
        df_prefiltrados = df_final[(df_final['RotacionMensual'] >= umbral_rotacion) & (df_final['CANTIDAD'] > 0)].copy()
        df_prefiltrados = df_prefiltrados.drop_duplicates(subset=['BARRA'])

        if preview_mode.lower() == "true":
            excluidos_list = df_excluidos.to_dict(orient='records')
            
            # Limpiar valores NaN/Infinity para asegurar serialización JSON válida
            for item in excluidos_list:
                for k, v in item.items():
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        item[k] = 0.0
            
            return JSONResponse(content={"excluidos": excluidos_list})

        # Aplicar inclusiones forzadas de productos excluidos seleccionados por el usuario
        forced_barcodes = []
        if forced_includes:
            forced_barcodes = [b.strip() for b in forced_includes.split(",") if b.strip()]

        df_forced = df_excluidos[df_excluidos['BARRA'].astype(str).isin(forced_barcodes)].copy()
        df_final_export = pd.concat([df_prefiltrados, df_forced], ignore_index=True)

        # Ordenar opcionalmente si hiciera falta (mantendremos el orden natural)
        # Aplicar Límite al final
        df_final_export = df_final_export.head(num_rows)

        # Limpieza final: Forzar mínimo de 1 para evitar CANTIDAD=0 en Excel exportado
        df_final_export['CANTIDAD'] = df_final_export['CANTIDAD'].astype(int)
        df_final_export.loc[df_final_export['CANTIDAD'] < 1, 'CANTIDAD'] = 1
        df_final_export['BARRA'] = df_final_export['BARRA'].astype(str)

        # Dejar solo las columnas requeridas para el Excel
        df_excel = df_final_export[['BARRA', 'CANTIDAD']].copy()

        # Crear Excel en Memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_excel.to_excel(writer, sheet_name='Precios', index=False)
        output.seek(0)

        tipo_pedido = "Generico" if is_generic.lower() == "true" else "Marcas"
        filename = f"Pedido_Synapse_{tipo_pedido}_{datetime.now().strftime('%Y%m%d')}_{pedido_days}Dias.xlsx"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            output, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        logging.error(f"Error generando reporte de pedidos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
