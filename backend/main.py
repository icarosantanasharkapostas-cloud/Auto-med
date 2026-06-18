# backend/main.py
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from backend.database.config import engine, Base, SessionLocal

# ---------------- CORREÇÃO ONE-SHOT E NORMALIZAÇÃO ----------------
def correcao_preventiva_total():
    """
    Garante que colunas esperadas existam no banco (compatível com SQLite e Postgres).
    Também normaliza config_json vazio para '{}' em clients.
    Executar ANTES de importar os models para evitar Import/OperationalError.
    """
    try:
        with engine.begin() as conn:
            # Clients: adiciona colunas se faltarem
            clients_cols = [
                ("categoria_salas_id", "TEXT"),
                ("cargo_mediador_id", "TEXT"),
                ("criado_em", "TIMESTAMP"),
            ]
            for col, coltype in clients_cols:
                try:
                    conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col} {coltype}"))
                    print(f"[DB-FIX] Tentativa: adicionar clients.{col}")
                except Exception:
                    # ignora se já existir / SQLite retornará erro se já existe
                    pass

            # Filas: adiciona colunas que usamos no fluxo
            filas_cols = [
                ("status", "TEXT"),
                ("tipo_partida", "TEXT"),
                ("valor_esperado", "NUMERIC"),
                ("placar_final", "TEXT"),
                ("timestamp_finalizacao", "TIMESTAMP"),
                ("meta", "TEXT"),
            ]
            for col, coltype in filas_cols:
                try:
                    conn.execute(text(f"ALTER TABLE filas ADD COLUMN {col} {coltype}"))
                    print(f"[DB-FIX] Tentativa: adicionar filas.{col}")
                except Exception:
                    pass

            # Pagamentos: adiciona pagador e meta
            pagamentos_cols = [
                ("pagador", "TEXT"),
                ("meta", "TEXT")
            ]
            for col, coltype in pagamentos_cols:
                try:
                    conn.execute(text(f"ALTER TABLE pagamentos ADD COLUMN {col} {coltype}"))
                    print(f"[DB-FIX] Tentativa: adicionar pagamentos.{col}")
                except Exception:
                    pass

            # Normalizar config_json: atualizar valores NULL ou '' para '{}'
            try:
                # verifica se coluna existe (pragmatic)
                conn.execute(text("UPDATE clients SET config_json = '{}' WHERE config_json IS NULL OR config_json = ''"))
            except Exception:
                # Alguns DBs podem ter config_json com tipo JSON e essa UPDATE é válida mesmo assim.
                pass

        print("[DB-FIX] verificação concluída.")
    except Exception as e:
        print(f"[DB-FIX] Erro na correcao_preventiva_total: {e}")

# Executa correção antes de importar models/routers/manager
correcao_preventiva_total()
# ---------------- fim correção one-shot ----------------

# Agora é seguro importar models/rotas/manager
from backend.database.models import Client, Log, Pagamento, Fila, Admin
from backend.api.routes import router
from bot.client_manager import manager

# garante criação de tabelas novas (não altera tabelas existentes)
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
    db = SessionLocal()
    try:
        active_clients = db.query(Client).filter(Client.ativo == True).all()
        for c in active_clients:
            # garantir que config_json seja dict (pode vir como string de versões antigas)
            cfg = c.config_json
            if isinstance(cfg, str):
                try:
                    cfg = json.loads(cfg) if cfg.strip() else {}
                except Exception:
                    cfg = {}
            if cfg is None:
                cfg = {}
            success = await manager.start_client({
                "id": c.id,
                "nome": c.nome,
                "token": c.token,
                "email": c.email,
                "senha_email": c.senha_email,
                "config_json": cfg
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
