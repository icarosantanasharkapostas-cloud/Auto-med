import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text, create_engine
from backend.database.config import DATABASE_URL, engine, Base, SessionLocal
from backend.api.routes import router
from bot.client_manager import manager

# --- CORREÇÃO DE EMERGÊNCIA (RODA ANTES DE TUDO) ---
def correcao_preventiva_sqlite():
    # Conecta diretamente via engine para garantir que as colunas existam ANTES do app carregar os models
    with engine.connect() as conn:
        # 1. Colunas para a tabela clients
        colunas_clients = ["categoria_salas_id", "cargo_mediador_id"]
        for col in colunas_clients:
            try:
                conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col} VARCHAR"))
                conn.commit()
                print(f"[DB-FIX] Coluna {col} adicionada em clients.")
            except Exception:
                # Se der erro é porque a coluna provavelmente já existe
                pass

        # 2. Colunas para a tabela filas
        colunas_filas = {
            "status": "VARCHAR DEFAULT 'AGUARDANDO_PAGAMENTO'",
            "tipo_partida": "VARCHAR DEFAULT 'NORMAL'",
            "valor_esperado": "NUMERIC",
            "placar_final": "VARCHAR",
            "timestamp_finalizacao": "TIMESTAMP",
            "meta": "TEXT"
        }
        for col, tipo in colunas_filas.items():
            try:
                conn.execute(text(f"ALTER TABLE filas ADD COLUMN {col} {tipo}"))
                conn.commit()
                print(f"[DB-FIX] Coluna {col} adicionada em filas.")
            except Exception:
                pass

# Executa a correção ANTES de importar os models que causam o erro
correcao_preventiva_sqlite()

# Agora importamos os models com segurança
from backend.database.models import Client, Log, Pagamento, Fila, Admin

# Inicializa banco de dados padrão
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

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.on_event("startup")
async def startup_event():
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
