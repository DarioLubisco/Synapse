import os
import io
import uvicorn
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from database import get_db_connection
from datetime import date
from typing import List, Optional
import pyodbc
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

router = APIRouter()

# Pydantic Schemas for validation (Phase 1)
class BilletesItem(BaseModel):
    denominacion: int
    cantidad: int
    total: float

class TarjetaItem(BaseModel):
    tipo: str
    punto_de_venta: str
    referencia: str
    monto: float

class DiferenciaItem(BaseModel):
    category: str
    sistema: float
    manual: float
    diferencia: float

class ConciliarRequest(BaseModel):
    vendedor_codigo: str
    vendedor_nombre: str | None = None
    fecha_ini: str
    fecha_fin: str
    efectivo_desglose: list[BilletesItem] = []
    divisa_desglose: list[BilletesItem] = []
    tarjeta_desglose: list[TarjetaItem] = []
    diferencias: list[DiferenciaItem] = []
    # Totals
    manual_efectivo_bs: float
    manual_divisas: float
    manual_euros: float
    manual_tdd: float
    manual_tdc: float
    manual_biopago: float
    manual_pago_movil: float = 0.0
    manual_transferencia: float = 0.0

@router.get("/caja/vendedores")
async def get_vendedores():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT CodVend, Descrip FROM dbo.SAVEND WHERE Activo = 1 ORDER BY Descrip")
        vendedores = [{"codigo": r[0].strip(), "nombre": r[1].strip() if r[1] else r[0].strip()} for r in cursor.fetchall()]
        return {"status": "success", "data": vendedores}
    except pyodbc.Error as strErr:
        raise HTTPException(status_code=500, detail=f"Database error: {str(strErr)}")
    finally:
        cursor.close()
        conn.close()

@router.get("/caja/puntos_venta")
async def get_puntos_venta():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.id, p.nombre_pos, p.tipo, b.nombre AS banco_nombre, p.categoria
            FROM Custom.CajaPuntosVenta p
            JOIN Custom.CajaBancos b ON p.banco_id = b.id
            WHERE p.activo = 1 AND b.activo = 1
            ORDER BY p.categoria, b.nombre, p.nombre_pos
        """)
        puntos = [
            {"id": r[0], "nombre": f"{r[1]} ({r[3]})", "tipo": r[2].strip(), "categoria": r[4].strip()}
            for r in cursor.fetchall()
        ]
        return {"status": "success", "data": puntos}
    except pyodbc.Error as strErr:
        raise HTTPException(status_code=500, detail=f"Database error: {str(strErr)}")
    finally:
        cursor.close()
        conn.close()

@router.get("/caja/tasa_del_dia")
async def get_tasa_del_dia():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT TOP 1 DolarBCV FROM dbo.DolarToday ORDER BY Fecha DESC")
        row = cursor.fetchone()
        tasa = float(row[0]) if row else 40.50 # Valor por defecto si no hay datos
        return {"status": "success", "tasa": tasa}
    except pyodbc.Error as strErr:
        raise HTTPException(status_code=500, detail=f"Database error: {str(strErr)}")
    finally:
        cursor.close()
        conn.close()

# Endpoint to test /caja/sistema/totales
@router.get("/caja/sistema/totales")
async def get_totales(vendedor_codigo: str, fecha: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Totales de Efectivo y Cheque desde SAFACT
        cursor.execute("""
            SELECT 
                ISNULL(SUM(CancelE), 0) AS TotEfectivo,
                ISNULL(SUM(CancelC), 0) AS TotCheque
            FROM dbo.SAFACT
            WHERE CodVend = ? 
              AND CAST(FechaE AS DATE) = ? 
              AND TipoFac IN ('A', 'C')
        """, (vendedor_codigo, fecha))
        row_totales = cursor.fetchone()
        tot_efectivo = float(row_totales[0] if row_totales else 0.0)
        tot_cheque   = float(row_totales[1] if row_totales else 0.0)

        # 2. Desglose dinámico por Categoría Madre (TipoIns) excluyendo Efectivo (006) y Divisas (021)
        cursor.execute("""
            SELECT 
                ISNULL(SUM(CASE WHEN t.TipoIns = 2 AND i.CodTarj NOT IN ('006', '021') THEN i.Monto ELSE 0 END), 0) AS TotDispositivos,
                ISNULL(SUM(CASE WHEN t.TipoIns = 3 AND i.CodTarj NOT IN ('006', '021') THEN i.Monto ELSE 0 END), 0) AS TotBancos,
                ISNULL(SUM(CASE WHEN i.CodTarj = '006' THEN i.Monto ELSE 0 END), 0) AS TotEfectivoT,
                ISNULL(SUM(CASE WHEN t.TipoIns NOT IN (2, 3) AND i.CodTarj NOT IN ('006', '021') THEN i.Monto ELSE 0 END), 0) AS TotOtros
            FROM dbo.SAIPAVTA i
            JOIN dbo.SAFACT   f ON i.NumeroD = f.NumeroD AND i.TipoFac = f.TipoFac
            LEFT JOIN dbo.SATARJ t ON i.CodTarj = t.CodTarj
            WHERE f.CodVend = ?
              AND CAST(f.FechaE AS DATE) = ?
              AND f.TipoFac IN ('A', 'C')
        """, (vendedor_codigo, fecha))
        row_elec = cursor.fetchone()
        tot_dispositivos = float(row_elec[0] if row_elec else 0.0)
        tot_bancos       = float(row_elec[1] if row_elec else 0.0)
        tot_efectivot    = float(row_elec[2] if row_elec else 0.0)
        tot_otros        = float(row_elec[3] if row_elec else 0.0)
        
        tot_efectivo += tot_efectivot
        tot_tarjeta   = tot_dispositivos + tot_bancos + tot_otros

        totales_sistema = {
            "totefectivo":     tot_efectivo,
            "tottarjeta":      tot_tarjeta,
            "totdispositivos": tot_dispositivos,
            "totbancos":       tot_bancos,
            "totcheque":       tot_cheque,
            "tototros":        tot_otros
        }

        # 2. Check for an active Precierre (estado = 'BORRADOR')
        cursor.execute('''
            SELECT id, manual_efectivo_bs, manual_divisas, manual_euros, manual_tdd, manual_tdc, manual_biopago, manual_pago_movil, ISNULL(manual_transferencia, 0)
            FROM Custom.CajaCierre
            WHERE vendedor_codigo = ? AND CAST(fecha_ini AS DATE) = ? AND estado = 'BORRADOR'
        ''', (vendedor_codigo, fecha))
        
        borrador_row = cursor.fetchone()
        
        has_precierre = False
        borrador_actual = {}
        
        if borrador_row:
            has_precierre = True
            cierre_id = borrador_row[0]
            borrador_actual = {
                "cierre_id": cierre_id,
                "manual_efectivo_bs": float(borrador_row[1]),
                "manual_divisas": float(borrador_row[2]),
                "manual_euros": float(borrador_row[3]),
                "manual_tdd": float(borrador_row[4]),
                "manual_tdc": float(borrador_row[5]),
                "manual_biopago": float(borrador_row[6]),
                "manual_pago_movil": float(borrador_row[7] if borrador_row[7] is not None else 0),
                "manual_transferencia": float(borrador_row[8]),
                "detalles_efectivo": [],
                "detalles_tarjetas": []
            }
            
            # Fetch detailed denominations
            cursor.execute("SELECT denominacion, cantidad, total FROM Custom.CajaCierreEfectivo WHERE cierre_id = ?", (cierre_id,))
            borrador_actual["detalles_efectivo"] = [{"denominacion": r[0], "cantidad": r[1], "total": float(r[2])} for r in cursor.fetchall()]
            
            # Fetch detailed card transactions
            cursor.execute("SELECT tipo, punto_de_venta, referencia, monto FROM Custom.CajaCierreTarjeta WHERE cierre_id = ?", (cierre_id,))
            borrador_actual["detalles_tarjetas"] = [{"tipo": r[0], "punto_de_venta": r[1], "referencia": r[2], "monto": float(r[3])} for r in cursor.fetchall()]
            
        return {
            "status": "success",
            "has_precierre": has_precierre,
            "totales_sistema": totales_sistema,
            "borrador_actual": borrador_actual
        }
        
    except pyodbc.Error as strErr:
        raise HTTPException(status_code=500, detail=f"Database error: {str(strErr)}")
    finally:
        cursor.close()
        conn.close()

@router.post("/caja/conciliar/guardar_borrador")
async def guardar_borrador(payload: ConciliarRequest):
    return await _upsert_cierre(payload, estado="BORRADOR")

@router.post("/caja/conciliar/finalizar")
async def finalizar_cuadre(payload: ConciliarRequest):
    return await _upsert_cierre(payload, estado="FINALIZADO")


async def _upsert_cierre(payload: ConciliarRequest, estado: str):
    """Core upsert logic for both Precierre and Cierre Definitivo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check for an existing BORRADOR to update instead of creating a duplicate
        cursor.execute('''
            SELECT id FROM Custom.CajaCierre
            WHERE vendedor_codigo = ?
              AND CAST(fecha_ini AS DATE) = ?
              AND estado = 'BORRADOR'
        ''', (payload.vendedor_codigo, payload.fecha_ini))
        existing = cursor.fetchone()
        
        if existing:
            cierre_id = existing[0]
            # Update the header
            cursor.execute('''
                UPDATE Custom.CajaCierre SET
                    vendedor_nombre    = ?,
                    manual_efectivo_bs = ?,
                    manual_divisas     = ?,
                    manual_euros       = ?,
                    manual_tdd         = ?,
                    manual_tdc         = ?,
                    manual_biopago     = ?,
                    manual_pago_movil  = ?,
                    manual_transferencia = ?,
                    estado             = ?
                WHERE id = ?
            ''', (payload.vendedor_nombre, payload.manual_efectivo_bs, payload.manual_divisas, payload.manual_euros,
                  payload.manual_tdd, payload.manual_tdc, payload.manual_biopago, payload.manual_pago_movil, payload.manual_transferencia,
                  estado, cierre_id))
            # Wipe detail tables before re-inserting
            cursor.execute("DELETE FROM Custom.CajaCierreEfectivo WHERE cierre_id = ?", (cierre_id,))
            cursor.execute("DELETE FROM Custom.CajaCierreDivisa    WHERE cierre_id = ?", (cierre_id,))
            cursor.execute("DELETE FROM Custom.CajaCierreTarjeta   WHERE cierre_id = ?", (cierre_id,))
            cursor.execute("DELETE FROM Custom.CajaCierreDiferencia WHERE cierre_id = ?", (cierre_id,))
        else:
            # Insert new header
            cursor.execute('''
                INSERT INTO Custom.CajaCierre
                    (vendedor_codigo, vendedor_nombre, fecha_ini, fecha_fin,
                     manual_efectivo_bs, manual_divisas, manual_euros,
                     manual_tdd, manual_tdc, manual_biopago, manual_pago_movil, manual_transferencia, estado)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (payload.vendedor_codigo, payload.vendedor_nombre,
                  payload.fecha_ini, payload.fecha_fin,
                  payload.manual_efectivo_bs, payload.manual_divisas, payload.manual_euros,
                  payload.manual_tdd, payload.manual_tdc, payload.manual_biopago, payload.manual_pago_movil, payload.manual_transferencia, estado))
            cierre_id = int(cursor.fetchone()[0])
        
        # ── Insert denomination breakdown (Bs) ────────────────────────────
        for item in payload.efectivo_desglose:
            if item.cantidad > 0:
                cursor.execute(
                    "INSERT INTO Custom.CajaCierreEfectivo (cierre_id, denominacion, cantidad, total) VALUES (?,?,?,?)",
                    (cierre_id, item.denominacion, item.cantidad, item.total)
                )
        
        # ── Insert USD denominations ──────────────────────────────────────
        for item in payload.divisa_desglose:
            if item.cantidad > 0:
                cursor.execute(
                    "INSERT INTO Custom.CajaCierreDivisa (cierre_id, moneda, denominacion, cantidad, total) VALUES (?,?,?,?,?)",
                    (cierre_id, 'USD', item.denominacion, item.cantidad, item.total)
                )

        # ── Insert POS tickets ────────────────────────────────────────────
        for ticket in payload.tarjeta_desglose:
            cursor.execute(
                "INSERT INTO Custom.CajaCierreTarjeta (cierre_id, tipo, punto_de_venta, referencia, monto) VALUES (?,?,?,?,?)",
                (cierre_id, ticket.tipo, ticket.punto_de_venta, ticket.referencia, ticket.monto)
            )
        
        # ── Insert differences (always, for audit/reporting) ──────────────
        for diff in payload.diferencias:
            cursor.execute(
                "INSERT INTO Custom.CajaCierreDiferencia (cierre_id, vendedor_codigo, vendedor_nombre, category, sistema, manual) VALUES (?,?,?,?,?,?)",
                (cierre_id, payload.vendedor_codigo, payload.vendedor_nombre, diff.category, diff.sistema, diff.manual)
            )
        
        conn.commit()
        
        msg = "Precierre guardado correctamente" if estado == 'BORRADOR' else "Cierre finalizado y sellado"
        return {"status": "success", "message": msg, "cierre_id": cierre_id}

    except pyodbc.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# ── Módulo de Reportes ──────────────────────────────────────────

@router.get("/caja/reportes/lista")
async def listar_reportes(fecha_desde: str, fecha_hasta: str, vendedor_codigo: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = '''
            SELECT id, vendedor_codigo, vendedor_nombre, fecha_ini, estado, 
                   manual_efectivo_bs, manual_divisas, manual_tdd, manual_tdc, manual_biopago, manual_pago_movil
            FROM Custom.CajaCierre
            WHERE CAST(fecha_ini AS DATE) >= ? AND CAST(fecha_ini AS DATE) <= ?
        '''
        params = [fecha_desde, fecha_hasta]
        
        if vendedor_codigo:
            query += " AND vendedor_codigo = ?"
            params.append(vendedor_codigo)
            
        query += " ORDER BY fecha_ini DESC"
        
        cursor.execute(query, params)
        cols = [column[0] for column in cursor.description]
        cierres = [dict(zip(cols, row)) for row in cursor.fetchall()]
        
        for c in cierres:
            c['manual_efectivo_bs'] = float(c['manual_efectivo_bs'] or 0)
            c['manual_divisas'] = float(c['manual_divisas'] or 0)
            c['manual_tdd'] = float(c['manual_tdd'] or 0)
            c['manual_tdc'] = float(c['manual_tdc'] or 0)
            c['manual_biopago'] = float(c['manual_biopago'] or 0)
            c['manual_pago_movil'] = float(c['manual_pago_movil'] or 0)
            
        return {"status": "success", "data": cierres}
    except pyodbc.Error as strErr:
        raise HTTPException(status_code=500, detail=f"Database error: {str(strErr)}")
    finally:
        cursor.close()
        conn.close()

@router.get("/caja/reportes/detalle/{cierre_id}")
async def detalle_reporte(cierre_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, vendedor_codigo, vendedor_nombre, fecha_ini, estado, manual_efectivo_bs, manual_divisas, manual_tdd, manual_tdc, manual_biopago, manual_pago_movil, ISNULL(manual_transferencia, 0) FROM Custom.CajaCierre WHERE id = ?", (cierre_id,))
        header_row = cursor.fetchone()
        if not header_row:
            raise HTTPException(status_code=404, detail="Cierre no encontrado")
            
        header = {
            "id": header_row[0], "vendedor_codigo": header_row[1], "vendedor_nombre": header_row[2],
            "fecha_ini": header_row[3], "estado": header_row[4],
            "manual_efectivo_bs": float(header_row[5] or 0), "manual_divisas": float(header_row[6] or 0),
            "manual_tdd": float(header_row[7] or 0), "manual_tdc": float(header_row[8] or 0),
            "manual_biopago": float(header_row[9] or 0), "manual_pago_movil": float(header_row[10] or 0),
            "manual_transferencia": float(header_row[11])
        }
            
        # Differences
        cursor.execute("SELECT category, sistema, manual FROM Custom.CajaCierreDiferencia WHERE cierre_id = ?", (cierre_id,))
        diferencias = [{"category": r[0], "sistema": float(r[1]), "manual": float(r[2]), "diferencia": float(r[2]-r[1])} for r in cursor.fetchall()]
        
        # Tickets
        cursor.execute("SELECT tipo, punto_de_venta, referencia, monto FROM Custom.CajaCierreTarjeta WHERE cierre_id = ?", (cierre_id,))
        tickets = [{"tipo": r[0], "punto_de_venta": r[1], "referencia": r[2], "monto": float(r[3])} for r in cursor.fetchall()]
        
        # Billetes
        cursor.execute("SELECT denominacion, cantidad, total FROM Custom.CajaCierreEfectivo WHERE cierre_id = ?", (cierre_id,))
        efectivo = [{"denominacion": r[0], "cantidad": r[1], "total": float(r[2])} for r in cursor.fetchall()]
        
        cursor.execute("SELECT denominacion, cantidad, total FROM Custom.CajaCierreDivisa WHERE cierre_id = ?", (cierre_id,))
        divisas = [{"denominacion": r[0], "cantidad": r[1], "total": float(r[2])} for r in cursor.fetchall()]

        return {
            "status": "success", 
            "data": {
                "header": header,
                "diferencias": diferencias,
                "tickets": tickets,
                "efectivo": efectivo,
                "divisas": divisas
            }
        }
    except pyodbc.Error as strErr:
        raise HTTPException(status_code=500, detail=f"Database error: {str(strErr)}")
    finally:
        cursor.close()
        conn.close()

# ── Admin: Autenticación y Panel Global ──────────────────────────────────────

@router.get("/caja/usuario/perfil")
async def get_perfil_usuario(cod_usua: str):
    """
    Consulta SSUSRS para obtener el perfil del usuario: 
    su nombre, nivel (1=admin, 4=vendedor), el código de vendedor asociado,
    y si está activo.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT CodUsua, Descrip, Level, CodVend, Activo FROM SSUSRS WHERE CodUsua = ? AND Activo = 1",
            (cod_usua,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
        
        nivel = int(row[2]) if row[2] is not None else 4
        # Level 1 = SuperAdmin, Level 2 = Supervisor/Admin – ambos tienen acceso al Panel Global
        es_admin = (nivel <= 2)
        
        return {
            "status": "success",
            "data": {
                "cod_usua": str(row[0]).strip(),
                "nombre": str(row[1]).strip(),
                "level": nivel,
                "es_admin": es_admin,
                "cod_vend": str(row[3]).strip() if row[3] else None,
                "activo": bool(row[4])
            }
        }
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/caja/admin/resumen_diario")
async def get_resumen_diario(fecha: str):
    """
    Vista exclusiva del Administrador:
    - Muestra todos los vendedores activos con ventas ese día.
    - Indica si tienen un cierre FINALIZADO o BORRADOR o si están PENDIENTES.
    - Incluye los totales del sistema (desde SAFACT) para cada uno.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Totales del sistema por vendedor para la fecha indicada
        cursor.execute('''
            WITH TotalesFactura AS (
                SELECT 
                    f.CodVend,
                    COUNT(f.NumeroD) AS nro_facturas,
                    SUM(ISNULL(f.CancelE, 0)) AS base_efectivo,
                    SUM(ISNULL(f.CancelT, 0)) AS base_tarjeta
                FROM dbo.SAFACT f
                WHERE CAST(f.FechaE AS DATE) = ?
                  AND f.TipoFac IN ('A', 'C')
                GROUP BY f.CodVend
            ),
            EfecEnTarj AS (
                SELECT 
                    f.CodVend,
                    SUM(ISNULL(i.Monto, 0)) AS efec_tarj
                FROM dbo.SAIPAVTA i
                JOIN dbo.SAFACT f ON i.NumeroD = f.NumeroD AND i.TipoFac = f.TipoFac
                WHERE CAST(f.FechaE AS DATE) = ?
                  AND f.TipoFac IN ('A', 'C')
                  AND i.CodTarj = '006'
                GROUP BY f.CodVend
            )
            SELECT 
                t.CodVend,
                v.Descrip AS nombre,
                t.base_efectivo + ISNULL(e.efec_tarj, 0) AS tot_efectivo_sis,
                t.base_tarjeta - ISNULL(e.efec_tarj, 0) AS tot_tarjeta_sis,
                t.nro_facturas
            FROM TotalesFactura t
            JOIN dbo.SAVEND v ON t.CodVend = v.CodVend
            LEFT JOIN EfecEnTarj e ON t.CodVend = e.CodVend
        ''', (fecha, fecha))
        
        vendedores_sis = {}
        for r in cursor.fetchall():
            vendedores_sis[str(r[0]).strip()] = {
                "cod_vend": str(r[0]).strip(),
                "nombre": str(r[1]).strip(),
                "tot_efectivo_sis": float(r[2]),
                "tot_tarjeta_sis": float(r[3]),
                "nro_facturas": int(r[4]),
                "estado_cierre": "PENDIENTE",
                "cierre_id": None,
                "manual_efectivo_bs": 0.0,
                "manual_total_pos": 0.0,
            }
        
        # 2. Verificar el estado del cierre de cada vendedor
        cursor.execute('''
            SELECT vendedor_codigo, id, estado, 
                   manual_efectivo_bs, manual_divisas,
                   manual_tdd, manual_tdc, manual_biopago, manual_pago_movil
            FROM Custom.CajaCierre
            WHERE CAST(fecha_ini AS DATE) = ?
        ''', (fecha,))
        
        for r in cursor.fetchall():
            cod = str(r[0]).strip()
            if cod in vendedores_sis:
                vendedores_sis[cod]["estado_cierre"] = str(r[2]).strip()
                vendedores_sis[cod]["cierre_id"] = int(r[1])
                vendedores_sis[cod]["manual_efectivo_bs"] = float(r[3] or 0)
                # Sumar todos los electrónicos para el resumen
                vendedores_sis[cod]["manual_total_pos"] = float((r[5] or 0) + (r[6] or 0) + (r[7] or 0) + (r[8] or 0))
        
        # 3. Totales globales
        resultado = list(vendedores_sis.values())
        total_global_sis = sum(v["tot_efectivo_sis"] + v["tot_tarjeta_sis"] for v in resultado)
        total_global_manual = sum(v["manual_efectivo_bs"] + v["manual_total_pos"] for v in resultado)
        
        pendientes = [v for v in resultado if v["estado_cierre"] == "PENDIENTE"]
        borradores = [v for v in resultado if v["estado_cierre"] == "BORRADOR"]
        finalizados = [v for v in resultado if v["estado_cierre"] == "FINALIZADO"]
        
        return {
            "status": "success",
            "fecha": fecha,
            "resumen": {
                "total_vendedores": len(resultado),
                "pendientes": len(pendientes),
                "borradores": len(borradores),
                "finalizados": len(finalizados),
                "total_global_sistema": total_global_sis,
                "total_global_manual": total_global_manual,
                "diferencia_global": total_global_manual - total_global_sis
            },
            "data": sorted(resultado, key=lambda x: x["nombre"])
        }
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# ── Calculadora Mixta — Modelo de datos ──────────────────────────────────────
class GuardarTransaccionRequest(BaseModel):
    vendedor_codigo: str | None = None
    observacion: str | None = None
    tasa_bcv: float
    # Factura
    factura_bs: float
    factura_usd: float
    # Entradas USD
    rec_ef_usd: float = 0.0
    rec_on_usd: float = 0.0
    # Entradas Bs
    rec_ef_bs: float = 0.0
    rec_pm_bs: float = 0.0
    rec_bio_bs: float = 0.0
    # Totales recibidos
    total_rec_usd: float = 0.0
    total_rec_bs: float = 0.0
    # Vuelto
    vuelto_usd: float = 0.0
    vuelto_bs: float = 0.0
    vuelto_pm_bs: float = 0.0
    total_vuelto_usd: float = 0.0
    # Resultado
    resultado: str = "EXACTO"
    diff_usd: float = 0.0
    diff_bs: float = 0.0


@router.post("/caja/calculadora/guardar")
async def guardar_transaccion(payload: GuardarTransaccionRequest):
    """Persiste una transacción de la Calculadora Mixta."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO Custom.CajaTransaccionesDolares
                (vendedor_codigo, observacion, tasa_bcv,
                 factura_bs, factura_usd,
                 rec_ef_usd, rec_on_usd,
                 rec_ef_bs, rec_pm_bs, rec_bio_bs,
                 total_rec_usd, total_rec_bs,
                 vuelto_usd, vuelto_bs, vuelto_pm_bs, total_vuelto_usd,
                 resultado, diff_usd, diff_bs)
            OUTPUT INSERTED.id, INSERTED.fecha
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            payload.vendedor_codigo, payload.observacion, payload.tasa_bcv,
            payload.factura_bs, payload.factura_usd,
            payload.rec_ef_usd, payload.rec_on_usd,
            payload.rec_ef_bs, payload.rec_pm_bs, payload.rec_bio_bs,
            payload.total_rec_usd, payload.total_rec_bs,
            payload.vuelto_usd, payload.vuelto_bs, payload.vuelto_pm_bs, payload.total_vuelto_usd,
            payload.resultado, payload.diff_usd, payload.diff_bs
        ))
        row = cursor.fetchone()
        conn.commit()
        return {
            "status": "success",
            "message": "Transacción guardada",
            "id": row[0],
            "fecha": str(row[1])
        }
    except pyodbc.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@router.delete("/caja/calculadora/transaccion/{transaccion_id}")
async def eliminar_transaccion_dolares(transaccion_id: int, cod_usua: str):
    """Anula una transacción del registro histórico de la Calculadora Mixta. Requiere permisos Admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check permissions
        cursor.execute("SELECT Level FROM SSUSRS WHERE CodUsua = ? AND Activo = 1", (cod_usua,))
        user_db = cursor.fetchone()
        if not user_db or int(user_db[0] if user_db[0] is not None else 4) > 2:
            raise HTTPException(status_code=403, detail="Permisos insuficientes. Sólo administradores pueden anular transacciones.")

        cursor.execute("UPDATE Custom.CajaTransaccionesDolares SET anulado = 1, observacion = ISNULL(observacion, '') + ' [ANULADO]' WHERE id = ?", (transaccion_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
        conn.commit()
        return {"status": "success", "message": "Transacción eliminada correctamente."}
    except pyodbc.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@router.get("/caja/calculadora/reporte")
async def reporte_dolares(fecha: str | None = None, vendedor_codigo: str | None = None):
    """
    Retorna el resumen de dólares del día (o de la fecha indicada):
    - Total efectivo USD recibido
    - Total Zelle recibido
    - Total vuelto USD dado
    - Saldo neto USD en caja
    - Últimas N transacciones
    Filtra opcionalmente por un vendedor en específico.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if not fecha:
            fecha = date.today().isoformat()

        # Armar lógica condicional de filtrado para el vendedor
        filtro_vend_sql = ""
        params_summary = [fecha]
        if vendedor_codigo:
            filtro_vend_sql = " AND vendedor_codigo = ?"
            params_summary.append(vendedor_codigo)

        cursor.execute(f'''
            SELECT
                COUNT(*)                              AS nro_transacciones,
                ISNULL(SUM(rec_ef_usd), 0)            AS total_efectivo_usd,
                ISNULL(SUM(rec_on_usd), 0)            AS total_zelle_usd,
                ISNULL(SUM(rec_ef_usd + rec_on_usd), 0) AS total_entrada_usd,
                ISNULL(SUM(rec_ef_bs),  0)            AS total_entrada_bs_ef,
                ISNULL(SUM(rec_pm_bs),  0)            AS total_entrada_bs_pm,
                ISNULL(SUM(rec_bio_bs), 0)            AS total_entrada_bs_bio,
                ISNULL(SUM(vuelto_usd), 0)            AS total_vuelto_usd,
                ISNULL(SUM(rec_ef_usd + rec_on_usd), 0)
                    - ISNULL(SUM(vuelto_usd), 0)      AS saldo_usd_caja
            FROM Custom.CajaTransaccionesDolares
            WHERE CAST(fecha AS DATE) = ? AND anulado = 0 {filtro_vend_sql}
        ''', tuple(params_summary))
        summary_row = cursor.fetchone()

        summary = {
            "fecha": fecha,
            "nro_transacciones": int(summary_row[0]),
            "total_efectivo_usd": float(summary_row[1]),
            "total_zelle_usd":    float(summary_row[2]),
            "total_entrada_usd":  float(summary_row[3]),
            "total_entrada_bs_ef": float(summary_row[4]),
            "total_entrada_bs_pm": float(summary_row[5]),
            "total_entrada_bs_bio": float(summary_row[6]),
            "total_vuelto_usd":   float(summary_row[7]),
            "saldo_usd_caja":     float(summary_row[8]),
        }

        # Últimas 50 transacciones del día
        cursor.execute(f'''
            SELECT TOP 50
                id, fecha, vendedor_codigo, observacion, tasa_bcv,
                factura_bs, factura_usd,
                rec_ef_usd, rec_on_usd, rec_ef_bs, rec_pm_bs, rec_bio_bs,
                total_rec_usd, total_rec_bs,
                vuelto_usd, vuelto_bs, vuelto_pm_bs, total_vuelto_usd,
                resultado, diff_usd, diff_bs, anulado
            FROM Custom.CajaTransaccionesDolares
            WHERE CAST(fecha AS DATE) = ? {filtro_vend_sql}
            ORDER BY fecha DESC
        ''', tuple(params_summary))

        cols = [c[0] for c in cursor.description]
        transacciones = [dict(zip(cols, row)) for row in cursor.fetchall()]
        # Serialise datetime/decimal
        for t in transacciones:
            for k, v in t.items():
                if hasattr(v, 'isoformat'):
                    t[k] = v.isoformat()
                elif v is None:
                    t[k] = None
                else:
                    try:
                        t[k] = float(v)
                    except (TypeError, ValueError):
                        t[k] = str(v)

        return {"status": "success", "summary": summary, "transacciones": transacciones}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# ── PDF Reporte de Cierre ─────────────────────────────────────────────────────

@router.get("/caja/reportes/{cierre_id}/pdf")
async def generar_pdf_cierre(cierre_id: int):
    """Genera un PDF del precierre o cierre de caja. Funciona para BORRADOR y FINALIZADO."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Cabecera del cierre
        cursor.execute("""
            SELECT id, vendedor_codigo, vendedor_nombre, fecha_ini, estado,
                   manual_efectivo_bs, manual_divisas, manual_tdd, manual_tdc, manual_biopago, manual_pago_movil
            FROM Custom.CajaCierre WHERE id = ?
        """, (cierre_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Cierre no encontrado")

        cierre = {
            "id": row[0], "cod_vend": str(row[1]).strip(),
            "nombre": str(row[2]).strip() if row[2] else str(row[1]).strip(),
            "fecha": str(row[3])[:10], "estado": str(row[4]).strip(),
            "ef_bs": float(row[5] or 0), "divisas": float(row[6] or 0),
            "tdd": float(row[7] or 0), "tdc": float(row[8] or 0),
            "biopago": float(row[9] or 0), "pago_movil": float(row[10] or 0),
        }

        # 2. Última venta del vendedor ese día (hora de factura)
        cursor.execute("""
            SELECT TOP 1 CONVERT(varchar(8), FechaE, 8) as hora, NumeroD
            FROM dbo.SAFACT
            WHERE CodVend = ? AND CAST(FechaE AS DATE) = ? AND TipoFac IN ('A','C')
            ORDER BY FechaE DESC
        """, (cierre["cod_vend"], cierre["fecha"]))
        ult_vta = cursor.fetchone()
        hora_ultima_venta = str(ult_vta[0]).strip() if ult_vta else "--:--:--"
        ultima_factura = str(ult_vta[1]).strip() if ult_vta else "N/A"

        # 3. Totales del sistema para ese vendedor ese día
        cursor.execute("""
            WITH TotalesFactura AS (
                SELECT 
                    SUM(ISNULL(CancelE, 0)) AS base_efectivo,
                    SUM(ISNULL(CancelT, 0)) AS base_tarjeta,
                    COUNT(NumeroD) AS nro_facturas
                FROM dbo.SAFACT 
                WHERE CodVend = ? AND CAST(FechaE AS DATE) = ? AND TipoFac IN ('A','C')
            ),
            EfecEnTarj AS (
                SELECT 
                    SUM(ISNULL(i.Monto, 0)) AS efec_tarj
                FROM dbo.SAIPAVTA i
                JOIN dbo.SAFACT f ON i.NumeroD = f.NumeroD AND i.TipoFac = f.TipoFac
                WHERE f.CodVend = ? AND CAST(f.FechaE AS DATE) = ? AND f.TipoFac IN ('A','C')
                  AND i.CodTarj = '006'
            )
            SELECT 
                ISNULL(t.base_efectivo, 0) + ISNULL(e.efec_tarj, 0),
                ISNULL(t.base_tarjeta, 0) - ISNULL(e.efec_tarj, 0),
                ISNULL(t.nro_facturas, 0)
            FROM TotalesFactura t
            LEFT JOIN EfecEnTarj e ON 1=1
        """, (cierre["cod_vend"], cierre["fecha"], cierre["cod_vend"], cierre["fecha"]))
        sys_row = cursor.fetchone()
        sis_efectivo = float(sys_row[0] if sys_row else 0)
        sis_tarjeta  = float(sys_row[1] if sys_row else 0)
        nro_facturas = int(sys_row[2] if sys_row else 0)

        # 4. Tickets de tarjeta anotados
        cursor.execute("""
            SELECT tipo, punto_de_venta, referencia, monto
            FROM Custom.CajaCierreTarjeta WHERE cierre_id = ?
            ORDER BY tipo, monto DESC
        """, (cierre_id,))
        tickets = [{"tipo": r[0], "pos": r[1], "ref": r[2], "monto": float(r[3])} for r in cursor.fetchall()]

        # 5. Desglose de billetes Bs. y divisa
        cursor.execute("SELECT denominacion, cantidad, total FROM Custom.CajaCierreEfectivo WHERE cierre_id = ? ORDER BY denominacion DESC", (cierre_id,))
        billetes_bs = [{"denom": r[0], "cant": r[1], "sub": float(r[2])} for r in cursor.fetchall()]

        cursor.execute("SELECT denominacion, cantidad, total FROM Custom.CajaCierreDivisa WHERE cierre_id = ? ORDER BY denominacion DESC", (cierre_id,))
        billetes_usd = [{"denom": r[0], "cant": r[1], "sub": float(r[2])} for r in cursor.fetchall()]

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    # ── Construir PDF ────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    # Paleta de colores corporativa
    DARK  = colors.HexColor("#0f172a")
    BLUE  = colors.HexColor("#3b82f6")
    GREEN = colors.HexColor("#10b981")
    RED   = colors.HexColor("#ef4444")
    GOLD  = colors.HexColor("#f59e0b")
    LGRAY = colors.HexColor("#f1f5f9")
    MGRAY = colors.HexColor("#94a3b8")

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", fontSize=20, textColor=DARK, spaceAfter=4, fontName="Helvetica-Bold", alignment=TA_CENTER)
    h2 = ParagraphStyle("h2", fontSize=13, textColor=BLUE, spaceAfter=6, fontName="Helvetica-Bold")
    normal = ParagraphStyle("normal", fontSize=9, textColor=DARK, fontName="Helvetica")
    small  = ParagraphStyle("small", fontSize=8, textColor=MGRAY, fontName="Helvetica")
    mono   = ParagraphStyle("mono", fontSize=9, textColor=DARK, fontName="Courier")
    right  = ParagraphStyle("right", fontSize=9, textColor=DARK, fontName="Helvetica", alignment=TA_RIGHT)

    def fmt(n): return f"Bs. {float(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    def fmtN(n): return f"{float(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    estado_color = GREEN if cierre["estado"] == "FINALIZADO" else GOLD
    estado_label = f"{'✓ CIERRE FINALIZADO' if cierre['estado'] == 'FINALIZADO' else '⚠ PRECIERRE (BORRADOR)'}"

    story = []

    # ── Encabezado ───────────────────────────────────────────────────────────
    story.append(Paragraph("PORTAL FINANCIERO AMC", h1))
    story.append(Paragraph("Farmacia Americana · Cuadre de Caja", 
        ParagraphStyle("sub", fontSize=10, textColor=MGRAY, fontName="Helvetica", alignment=TA_CENTER)))
    story.append(Spacer(1, 0.3*cm))

    # Badge de estado
    badge_data = [[Paragraph(estado_label, ParagraphStyle("badge", fontSize=11, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER))]]
    badge_tbl = Table(badge_data, colWidths=[16*cm])
    badge_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), estado_color),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(badge_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── Info del turno ────────────────────────────────────────────────────────
    info_data = [
        [Paragraph("<b>Responsable</b>", normal), Paragraph(cierre["nombre"], mono),
         Paragraph("<b>Código</b>", normal), Paragraph(cierre["cod_vend"], mono)],
        [Paragraph("<b>Fecha Turno</b>", normal), Paragraph(cierre["fecha"], mono),
         Paragraph("<b>Cierre ID</b>", normal), Paragraph(f"#{cierre_id}", mono)],
        [Paragraph("<b>Última Venta</b>", normal), Paragraph(f"{hora_ultima_venta}", ParagraphStyle("hora", fontSize=10, textColor=BLUE, fontName="Courier-Bold")),
         Paragraph("<b>Última Factura</b>", normal), Paragraph(f"#{ultima_factura}", mono)],
        [Paragraph("<b>Facturas del día</b>", normal), Paragraph(str(nro_facturas), mono),
         Paragraph("<b>Estado</b>", normal), Paragraph(cierre["estado"], ParagraphStyle("st", fontSize=9, textColor=estado_color, fontName="Helvetica-Bold"))],
    ]
    info_tbl = Table(info_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 4*cm])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LGRAY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [LGRAY, colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Comparativo Sistema vs Manual ─────────────────────────────────────────
    story.append(Paragraph("COMPARATIVO SISTEMA vs DECLARADO", h2))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    story.append(Spacer(1, 0.2*cm))

    man_ef  = cierre["ef_bs"] + cierre["divisas"]
    man_pos = cierre["tdd"] + cierre["tdc"] + cierre["biopago"] + cierre["pago_movil"]
    diff_ef  = man_ef  - sis_efectivo
    diff_pos = man_pos - sis_tarjeta

    def diff_color(v): return GREEN if v >= 0 else RED
    def diff_str(v): return ("+ " if v >= 0 else "- ") + fmtN(abs(v))

    comp_header = [Paragraph("<b>Categoría</b>", normal), 
                   Paragraph("<b>Sistema</b>", right), 
                   Paragraph("<b>Declarado</b>", right), 
                   Paragraph("<b>Diferencia</b>", right)]
    comp_rows = [
        comp_header,
        [Paragraph("Efectivo Bs.", normal), Paragraph(fmt(sis_efectivo), right),
         Paragraph(fmt(man_ef), right),
         Paragraph(diff_str(diff_ef), ParagraphStyle("d", fontSize=9, fontName="Helvetica-Bold", textColor=diff_color(diff_ef), alignment=TA_RIGHT))],
        [Paragraph("POS / Electrónico", normal), Paragraph(fmt(sis_tarjeta), right),
         Paragraph(fmt(man_pos), right),
         Paragraph(diff_str(diff_pos), ParagraphStyle("d2", fontSize=9, fontName="Helvetica-Bold", textColor=diff_color(diff_pos), alignment=TA_RIGHT))],
        [Paragraph("<b>TOTAL</b>", ParagraphStyle("tb", fontSize=9, fontName="Helvetica-Bold")), 
         Paragraph(fmt(sis_efectivo + sis_tarjeta), ParagraphStyle("tr", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
         Paragraph(fmt(man_ef + man_pos), ParagraphStyle("tr2", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
         Paragraph(diff_str(diff_ef + diff_pos), ParagraphStyle("td", fontSize=9, fontName="Helvetica-Bold", textColor=diff_color(diff_ef + diff_pos), alignment=TA_RIGHT))],
    ]
    comp_tbl = Table(comp_rows, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("BACKGROUND", (0,-1), (-1,-1), LGRAY),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LGRAY]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
    ]))
    story.append(comp_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Desglose Efectivo Bs. ─────────────────────────────────────────────────
    if billetes_bs:
        story.append(Paragraph("DESGLOSE EFECTIVO BOLÍVARES", h2))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        story.append(Spacer(1, 0.2*cm))
        ef_rows = [[Paragraph("<b>Denominación</b>", normal), Paragraph("<b>Cantidad</b>", right), Paragraph("<b>Subtotal</b>", right)]]
        for b in billetes_bs:
            ef_rows.append([
                Paragraph(f"Bs. {b['denom']:,.0f}", mono),
                Paragraph(str(b["cant"]), right),
                Paragraph(fmt(b["sub"]), right),
            ])
        ef_rows.append([Paragraph("<b>TOTAL</b>", ParagraphStyle("t", fontSize=9, fontName="Helvetica-Bold")),
                        Paragraph("", right),
                        Paragraph(fmt(cierre["ef_bs"]), ParagraphStyle("tr", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT))])
        ef_tbl = Table(ef_rows, colWidths=[6*cm, 5*cm, 5*cm])
        ef_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), DARK), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("BACKGROUND", (0,-1), (-1,-1), LGRAY),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LGRAY]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ]))
        story.append(ef_tbl)
        story.append(Spacer(1, 0.6*cm))

    # ── Desglose USD ──────────────────────────────────────────────────────────
    if billetes_usd:
        story.append(Paragraph("DESGLOSE DIVISAS (USD)", h2))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        story.append(Spacer(1, 0.2*cm))
        usd_rows = [[Paragraph("<b>Billete</b>", normal), Paragraph("<b>Cantidad</b>", right), Paragraph("<b>Subtotal</b>", right)]]
        for b in billetes_usd:
            usd_rows.append([
                Paragraph(f"$ {b['denom']:,.0f}", mono),
                Paragraph(str(b["cant"]), right),
                Paragraph(f"$ {fmtN(b['sub'])}", right),
            ])
        usd_rows.append([Paragraph("<b>TOTAL</b>", ParagraphStyle("t", fontSize=9, fontName="Helvetica-Bold")),
                         Paragraph("", right),
                         Paragraph(f"$ {fmtN(cierre['divisas'])}", ParagraphStyle("tr", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT))])
        usd_tbl = Table(usd_rows, colWidths=[6*cm, 5*cm, 5*cm])
        usd_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), DARK), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("BACKGROUND", (0,-1), (-1,-1), LGRAY),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LGRAY]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ]))
        story.append(usd_tbl)
        story.append(Spacer(1, 0.6*cm))

    # ── Tickets POS ───────────────────────────────────────────────────────────
    if tickets:
        story.append(Paragraph("TICKETS POS / ELECTRÓNICOS ANOTADOS", h2))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        story.append(Spacer(1, 0.2*cm))
        tk_rows = [[Paragraph("<b>Tipo</b>", normal), Paragraph("<b>Terminal</b>", normal),
                    Paragraph("<b>Referencia</b>", normal), Paragraph("<b>Monto</b>", right)]]
        for t in tickets:
            tk_rows.append([
                Paragraph(t["tipo"], mono),
                Paragraph(t["pos"], ParagraphStyle("ps", fontSize=8, fontName="Helvetica")),
                Paragraph(t["ref"], mono),
                Paragraph(fmt(t["monto"]), right),
            ])
        tk_rows.append([
            Paragraph("", normal), Paragraph("", normal),
            Paragraph("<b>TOTAL TICKETS</b>", ParagraphStyle("tt", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            Paragraph(fmt(man_pos), ParagraphStyle("tm", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ])
        tk_tbl = Table(tk_rows, colWidths=[2.5*cm, 6.5*cm, 3*cm, 4*cm])
        tk_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), DARK), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("BACKGROUND", (0,-1), (-1,-1), LGRAY),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LGRAY]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ]))
        story.append(tk_tbl)
        story.append(Spacer(1, 0.6*cm))

    # ── Pie de Página ─────────────────────────────────────────────────────────
    from datetime import datetime
    story.append(HRFlowable(width="100%", thickness=1, color=MGRAY))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')} · Portal Financiero AMC · Cierre #{cierre_id}",
        ParagraphStyle("foot", fontSize=7.5, textColor=MGRAY, fontName="Helvetica", alignment=TA_CENTER)
    ))
    if cierre["estado"] == "BORRADOR":
        story.append(Spacer(1, 0.15*cm))
        story.append(Paragraph(
            "⚠ Este documento es un PRECIERRE no oficial. El cierre definitivo aún no ha sido finalizado.",
            ParagraphStyle("warn", fontSize=8, textColor=GOLD, fontName="Helvetica-Bold", alignment=TA_CENTER)
        ))

    doc.build(story)
    buffer.seek(0)

    filename = f"cierre_{cierre_id}_{cierre['estado'].lower()}_{cierre['fecha']}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )


# ── Pago Móvil — Bandeja de Captura ─────────────────────────────────────────

class CapturarPagoMovilRequest(BaseModel):
    registros_ids: List[int]             # IDs de Procurement.CajaPagoMovil a capturar
    cod_usua: str                        # Quien captura (usuario Saint)
    cierre_id: Optional[int] = None      # ID del cierre al que se asocian (opcional, para vincular)


@router.get("/caja/pagomovil/pendientes")
async def get_pagomovil_pendientes(fecha: Optional[str] = None):
    """
    Retorna todos los registros de Procurement.CajaPagoMovil que aún no han sido
    procesados (procesado = 0), opcionalmente filtrados por fecha.
    Muestra el id único para trazabilidad.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if fecha:
            cursor.execute("""
                SELECT id, banco, monto, referencia, texto_original, created_at
                FROM Procurement.CajaPagoMovil
                WHERE (procesado = 0 OR procesado IS NULL)
                  AND CAST(created_at AS DATE) = ?
                ORDER BY created_at DESC
            """, (fecha,))
        else:
            # Sin filtro de fecha: muestra pendientes de hoy y ayer (ventana de 2 días)
            cursor.execute("""
                SELECT id, banco, monto, referencia, texto_original, created_at
                FROM Procurement.CajaPagoMovil
                WHERE (procesado = 0 OR procesado IS NULL)
                  AND created_at >= DATEADD(DAY, -1, CAST(GETDATE() AS DATE))
                ORDER BY created_at DESC
            """)

        cols = [c[0] for c in cursor.description]
        rows = []
        for r in cursor.fetchall():
            item = dict(zip(cols, r))
            # Serialise datetime / decimal
            for k, v in item.items():
                if hasattr(v, 'isoformat'):
                    item[k] = v.isoformat()
                elif v is None:
                    item[k] = None
                else:
                    try:
                        item[k] = float(v) if isinstance(v, object) and hasattr(v, '__float__') else v
                    except Exception:
                        item[k] = str(v)
            rows.append(item)

        return {"status": "success", "total": len(rows), "data": rows}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/caja/pagomovil/capturar")
async def capturar_pagomovil(payload: CapturarPagoMovilRequest):
    """
    Marca uno o más registros de Procurement.CajaPagoMovil como procesados.
    Registra el usuario que los capturó (cod_usua) y el cierre_id si se provee.
    Opera de forma atómica — si algún registro ya fue procesado, ignora ese ID.
    Retorna la lista de registros efectivamente capturados para que el frontend
    los agregue como tickets al cuadre activo.
    """
    if not payload.registros_ids:
        raise HTTPException(status_code=400, detail="Debe indicar al menos un ID.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Construir placeholders para IN clause
        placeholders = ",".join(["?" for _ in payload.registros_ids])

        # Leer los registros pendientes que aún no fueron tomados (previene doble captura)
        cursor.execute(f"""
            SELECT id, banco, monto, referencia
            FROM Procurement.CajaPagoMovil
            WHERE id IN ({placeholders})
              AND (procesado = 0 OR procesado IS NULL)
        """, payload.registros_ids)

        disponibles = cursor.fetchall()
        if not disponibles:
            return {"status": "warning", "message": "Todos los registros seleccionados ya fueron procesados.", "capturados": []}

        ids_disponibles = [r[0] for r in disponibles]
        placeholders2 = ",".join(["?" for _ in ids_disponibles])

        # Marcar como procesados en bloque atómico
        params = [1, payload.cod_usua]
        if payload.cierre_id:
            params.append(payload.cierre_id)
            cursor.execute(f"""
                UPDATE Procurement.CajaPagoMovil
                SET procesado      = ?,
                    capturado_por  = ?,
                    capturado_en   = GETDATE(),
                    cierre_id      = ?
                WHERE id IN ({placeholders2})
            """, params + ids_disponibles)
        else:
            cursor.execute(f"""
                UPDATE Procurement.CajaPagoMovil
                SET procesado      = ?,
                    capturado_por  = ?,
                    capturado_en   = GETDATE()
                WHERE id IN ({placeholders2})
            """, params + ids_disponibles)

        conn.commit()

        # Armar respuesta con detalles de los capturados
        capturados = [
            {
                "id": r[0],
                "banco": str(r[1]).strip() if r[1] else "N/A",
                "monto": float(r[2]) if r[2] else 0.0,
                "referencia": str(r[3]).strip() if r[3] else ""
            }
            for r in disponibles
        ]

        return {
            "status": "success",
            "message": f"{len(capturados)} registro(s) capturado(s) por {payload.cod_usua}",
            "capturados": capturados
        }

    except pyodbc.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
