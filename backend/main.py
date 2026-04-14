from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Inicializar nuestra API Principal (Synapse Backend)
app = FastAPI(title="Synapse Business Suite API", version="2.0.0")

# Permisos para que el Portal Web Frontend (Nginx) pueda llamar a nuestro Backend API
# Incluso si corren bajo diferentes dominios o puertos en la red (CORS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """El Orquestador usa esto para saber si el Backend está vivo"""
    return {"status": "ok", "message": "Synapse API running inside Docker"}

# Aquí conectaremos los Enrutadores (Routers)
from routers.caja import router as caja_router
from routers.cxp import router as cxp_router
from routers.pedidos import router as pedidos_router

app.include_router(caja_router)
app.include_router(cxp_router)
app.include_router(pedidos_router)

# app.include_router(pedidos_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
