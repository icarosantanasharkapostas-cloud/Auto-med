import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from backend.database.config import engine, Base, SessionLocal

# --- CORREÇÃO COMPLETA PARA SQUARE CLOUD (SQLite) ---
def correcao_preventiva_total():
    with engine.begin() as conn:
        # 1. Colunas para CLIENTS
        for col in [("categoria_salas_id", "TEXT"), ("cargo_mediador_id", "TEXT"), ("criado_em", "TIMESTAMP")]:
            try: conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col[0]} {col[1]}"))
            except: pass

        # 2. Colunas para FILAS
        for col in [("status", "TEXT"), ("tipo_partida", "TEXT"), ("valor_esperado", "NUMERIC"), ("placar_final", "TEXT"), ("timestamp_finalizacao", "TIMESTAMP"), ("meta", "TEXT")]:
            try: conn.execute(text(f"ALTER TABLE filas ADD COLUMN {col[0]} {col[1]}"))
            except: pass

        # 3. Colunas para PAGAMENTOS (O erro da imagem 10 e 18)
        for col in [("pagador", "TEXT"), ("meta", "TEXT")]:
            try: conn.execute(text(f"ALTER TABLE pagamentos ADD COLUMN {col[0]} {col[1]}"))
            except: pass
    print("[DB-FIX] Todas as colunas verificadas!")

correcao_preventiva_total()

# Agora importa o restante
from backend.database.models import Client, Log, Pagamento, Fila, Admin
from backend.api.routes import router
from bot.client_manager import manager

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Mediação Bot API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        active_clients = db.query(Client).filter(Client.ativo == True).all()
        for c in active_clients:
            # Garante que config_json nunca seja None para evitar o erro da imagem 13
            config = c.config_json if c.config_json else "{}"
            await manager.start_client({
                "id": c.id, "nome": c.nome, "token": c.token,
                "email": c.email, "senha_email": c.senha_email,
                "config_json": config
            })
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    await manager.shutdown_all()

@app.get("/")
async def dashboard(request: Request): return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request): return templates.TemplateResponse("login.html", {"request": request})
