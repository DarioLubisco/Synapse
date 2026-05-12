import os
import io
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import pyodbc
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
        
        # Limpieza b├ísica
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
    subtraction_files: Optional[List[UploadFile]] = File(None)
):
    try:
        query = load_query()
        if not query:
            raise HTTPException(status_code=500, detail="No se pudo cargar la consulta SQL maestra.")

        # Validar entradas
        if num_rows <= 0:
            num_rows = 5000
        
        valid_days = ['9', '14', '21', '30', '45', '60', '75', '90', '120']
        if pedido_days not in valid_days:
            pedido_days = '30'

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

        # Filtrar por categor├¡as si aplica
        if categories:
            parsed_categories = [cat.strip() for cat in categories.split(",") if cat.strip()]
            if 'Instancia' in df.columns:
                df = df[df['Instancia'].isin(parsed_categories)]

        # L├│gica de Generaci├│n
        pedido_column = f'Pedido{pedido_days}'
        if pedido_column not in df.columns:
            # Fallback a la primera columna tipo Pedido que encontremos o error
            cols_pedido = [c for c in df.columns if c.startswith('Pedido')]
            if cols_pedido:
                pedido_column = cols_pedido[0]
            else:
                raise ValueError(f"La columna {pedido_column} no existe en el set de datos.")

        df_filtered = df[df[pedido_column] > 0].copy()
        df_final = df_filtered[['CodProd', pedido_column]].copy()
        df_final.rename(columns={'CodProd': 'BARRA', pedido_column: 'CANTIDAD'}, inplace=True)
        
        # Aplicar L├¡mite
        df_final = df_final.head(num_rows)

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
                df_final = df_merged[df_merged['CANTIDAD'] > 0][['BARRA', 'CANTIDAD']].copy()

        # Limpieza final
        df_final['CANTIDAD'] = df_final['CANTIDAD'].astype(int)
        df_final['BARRA'] = df_final['BARRA'].astype(str)

        # Crear Excel en Memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name='Precios', index=False)
        output.seek(0)

        filename = f"Pedido_Synapse_{datetime.now().strftime('%Y%m%d')}_{pedido_days}Dias.xlsx"
        
        return StreamingResponse(
            output, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        logging.error(f"Error generando reporte de pedidos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
