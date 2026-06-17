# backend/main.py
import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from backend.database.config import engine, Base, SessionLocal
from backend.api.routes import router
from bot.client_manager import manager
from backend.database.models import Client, Log, Pagamento, Fila, Admin

# --- FUNÇÃO DE ATUALIZAÇÃO ONE-SHOT (Squad Cloud / ambientes sem acesso a psql) ---
def atualizar_banco_automatico():
    """
    Executa ALTER TABLE IF NOT EXISTS para garantir colunas que o frontend pode enviar.
    One-shot: é seguro executá-lo no startup (usa IF NOT EXISTS) — depois remova o bloco.
    """
    db = SessionLocal()
    try:
        colunas = [
            # Colunas para a tabela filas
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'AGUARDANDO_PAGAMENTO'",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS tipo_partida VARCHAR DEFAULT 'NORMAL'",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS valor_esperado NUMERIC",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS placar_final VARCHAR",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS timestamp_finalizacao TIMESTAMP",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS meta TEXT",
            # Colunas adicionais para clients (fields do painel)
            "ALTER TABLE clients ADD COLUMN IF NOT EXISTS categoria_salas_id VARCHAR",
            "ALTER TABLE clients ADD COLUMN IF NOT EXISTS cargo_mediador_id VARCHAR",
            # Caso precise adicionar outras colunas no futuro, inclua aqui
        ]
        for sql in colunas:
            try:
                db.execute(text(sql))
                db.commit()
                print(f"[DB-UPDATE] OK: {sql}")
            except Exception as e:
                db.rollback()
                # Ignora erros esperados (ex.: permissão) mas loga para depuração
                print(f"[DB-UPDATE] Ignorado/Erro: {sql} -> {e}")
        print("[DB-UPDATE] verificação concluída.")
    finally:
        db.close()
# -----------------------------------------------------------------------------

# Inicializa banco de dados (Cria tabelas novas se não existirem)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mediação Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Montar frontend
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.on_event("startup")
async def startup_event():
    # Roda a atualização de colunas (one-shot) no início
    atualizar_banco_automatico()

    # Inicializar bots marcados como "ativos" no banco
    db = SessionLocal()
    try:
        active_clients = db.query(Client).filter(Client.ativo == True).all()
        for c in active_clients:
            success = await manager.start_client({
                "id": c.id,
                "nome": c.nome,
                "token": c.token,
                "email": c.email,
                "senha_email": c.senha_email,
                "config_json": c.config_json
            })
            print(f"Startup client {c.id} start status: {success}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    await manager.shutdown_all()

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
