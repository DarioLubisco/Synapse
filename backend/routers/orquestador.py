import json
import asyncio
import httpx
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection

import os

def write_log(msg):
    try:
        with open("/app/orq.log", "a") as f:
            f.write(msg + "\\n")
    except:
        pass

router = APIRouter(prefix="/api/orquestador", tags=["Orquestador"])
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
class AutomationTask(BaseModel):
    TriggerID: int
    ActionCommand: str
    IsActive: bool
    LastTriggered: Optional[str] = None

def fetch_pending_records(limit=100):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"""
        SELECT TOP {limit} codigo, codbarras, descrip1art 
        FROM Procurement.por_aprobacion_equivalencias 
        WHERE origen_dato IS NULL OR origen_dato != 'IA_INVESTIGATED_V10_CLEANSE'
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        lote = [{"codigo": r[0], "codbarras": r[1], "descripcion_original": r[2]} for r in rows]
        conn.close()
        return lote
    except Exception as e:
        write_log(f"Error DB: {e}")
        return []

async def analyze_with_ai(lote):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    batch_str = json.dumps(lote, ensure_ascii=False)
    prompt = f"""
    Actúa como el Agente Investigador Farmacéutico. Recibirás un lote de productos.
    Para cada producto, extrae los siguientes atributos basándote en la descripción:
    - principio_activo (string o null si no aplica)
    - concentracion (string o null)
    - forma_farmaceutica (string o null)

    IMPORTANTE: Devuelve ÚNICAMENTE un array JSON válido con este formato, sin markdown extra:
    [
      {{
        "registro": {{"codigo": "...", "codbarras": "...", "descripcion_original": "..."}},
        "atributos": {{"principio_activo": "...", "concentracion": "...", "forma_farmaceutica": "..."}}
      }}
    ]

    LOTE A PROCESAR:
    {batch_str}
    """
    
    data = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=data)
            result = resp.json()
            content = result['choices'][0]['message']['content']
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except Exception as e:
            write_log(f"Error AI: {e}")
            return []

async def run_scraper_task(task: AutomationTask):
    write_log(f"[Orquestador] Iniciando tarea: {task.ActionCommand} (ID: {task.TriggerID})")
    webhook_url = "https://n8n.farmaciaamericana.es/webhook/osint-resultados"
    try:
        # Traer registros de base de datos
        lote = await asyncio.to_thread(fetch_pending_records, 100)
        
        if not lote:
            write_log("[Orquestador] No hay registros pendientes.")
            # Mandar webhook de todos modos para que n8n cierre el trigger
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json={"TriggerID": task.TriggerID, "status": "Vacio", "data": []}, timeout=30.0)
            return

        write_log(f"[Orquestador] Procesando {len(lote)} registros con IA...")
        resultados_ia = await analyze_with_ai(lote)

        scraped_results = []
        for item in resultados_ia:
            reg = item.get("registro", {})
            atr = item.get("atributos", {})
            scraped_results.append({
                "codigo": reg.get("codigo"),
                "principio_activo_Des": atr.get("principio_activo"),
                "concentracion_Des": atr.get("concentracion"),
                "forma_farmaceutica_Des": atr.get("forma_farmaceutica")
            })

        write_log(f"[Orquestador] IA finalizada. Enviando {len(scraped_results)} items a n8n...")

        payload = {
            "TriggerID": task.TriggerID,
            "status": "Completado",
            "ActionCommand": task.ActionCommand,
            "data": scraped_results
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=30.0)
            if response.status_code == 200:
                write_log(f"[Orquestador] Webhook exitoso.")
            else:
                write_log(f"[Orquestador] Webhook falló: {response.status_code}")

    except Exception as e:
        write_log(f"[Orquestador] Error crítico en tarea {task.TriggerID}: {e}")
        try:
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json={"TriggerID": task.TriggerID, "status": "Error", "data": []})
        except:
            pass

@router.post("/start")
async def start_orquestador(task: AutomationTask, background_tasks: BackgroundTasks):
    if not task:
        return {"status": "ignored", "message": "No task"}
        
    background_tasks.add_task(run_scraper_task, task)
    return {"status": "started", "task_queued": task.TriggerID}
