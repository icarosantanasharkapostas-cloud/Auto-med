# backend/main.py
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from backend.database.config import engine, Base, SessionLocal

# ---------------- CORREÇÃO ONE-SHOT (executa ANTES dos models) ----------------
def correcao_preventiva_total():
    """
    Garante que TODAS as colunas usadas pelo código existam no banco
    (SQLite ou PostgreSQL), evitando os erros "no such column".

    ✅ Funciona tanto em banco NOVO (Railway) quanto em banco ANTIGO
       (que veio da Square Cloud com colunas faltando). É idempotente:
       se a coluna já existe, apenas ignora.
    """
    # Descobre se estamos em PostgreSQL para usar o tipo de data correto.
    is_postgres = engine.url.get_backend_name().startswith("postgres")
    ts_type = "TIMESTAMP" if is_postgres else "TIMESTAMP"

    # Mapa: tabela -> lista de (coluna, tipo) que PRECISAM existir.
    colunas_por_tabela = {
        "clients": [
            ("categoria_salas_id", "TEXT"),
            ("cargo_mediador_id", "TEXT"),
            ("criado_em", ts_type),
            ("ativo", "BOOLEAN"),
        ],
        "admins": [
            ("username", "TEXT"),
            ("password_hash", "TEXT"),
            ("client_id", "INTEGER"),
            ("discord_id", "TEXT"),
            ("nome", "TEXT"),
            ("nivel", "TEXT"),
            ("ativo", "BOOLEAN"),
            ("criado_em", ts_type),
        ],
        "logs": [
            ("tipo", "TEXT"),
            ("client_id", "INTEGER"),
            ("timestamp", ts_type),
        ],
        "pagamentos": [
            ("nome_pagador", "TEXT"),
            ("valor", "NUMERIC"),
            ("horario", "TEXT"),
            ("canal_id", "TEXT"),
            ("status", "TEXT"),
            ("meta", "TEXT"),
            ("timestamp", ts_type),
        ],
        "filas": [
            ("status", "TEXT"),
            ("tipo_partida", "TEXT"),
            ("valor_esperado", "NUMERIC"),
            ("placar_final", "TEXT"),
            ("timestamp_finalizacao", ts_type),
            ("meta", "TEXT"),
        ],
    }

    try:
        with engine.begin() as conn:
            for tabela, colunas in colunas_por_tabela.items():
                for col, coltype in colunas:
                    try:
                        conn.execute(text(
                            f"ALTER TABLE {tabela} ADD COLUMN {col} {coltype}"
                        ))
                        print(f"[DB-FIX] Adicionada coluna {tabela}.{col}")
                    except Exception:
                        # Coluna já existe ou tabela ainda não criada — tudo bem.
                        pass

            # Normaliza config_json nulo/vazio para evitar erro de validação.
            try:
                conn.execute(text(
                    "UPDATE clients SET config_json = '{}' "
                    "WHERE config_json IS NULL OR config_json = ''"
                ))
                print("[DB-FIX] Normalizou config_json nulo/vazio.")
            except Exception:
                pass

        print("[DB-FIX] verificação concluída.")
    except Exception as e:
        print(f"[DB-FIX] Erro na correcao_preventiva_total: {e}")

# Executa a correção ANTES de importar models/rotas/manager
correcao_preventiva_total()
# ---------------------------------------------------------------------------

# Agora é seguro importar models/routers/manager
from backend.database.models import Client, Log, Pagamento, Fila, Admin
from backend.api.routes import router
from bot.client_manager import manager

# Garante criação de tabelas novas (não altera tabelas existentes)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mediação Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclua seu router principal
app.include_router(router, prefix="/api")

# Templates (ajuste o path se o seu projeto usa outra pasta)
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# (Opcional) Se você adicionou qr_routes conforme instruções anteriores, inclua também:
# from backend.api.qr_routes import router as qr_router
# app.include_router(qr_router)

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        active_clients = db.query(Client).filter(Client.ativo == True).all()
        for c in active_clients:
            # garantir que config_json seja dict
            cfg = c.config_json
            if isinstance(cfg, str):
                try:
                    cfg = json.loads(cfg) if cfg.strip() else {}
                except Exception:
                    cfg = {}
            if cfg is None:
                cfg = {}
            try:
                success = await manager.start_client({
                    "id": c.id,
                    "nome": c.nome,
                    "token": c.token,
                    "email": c.email,
                    "senha_email": c.senha_email,
                    "config_json": cfg
                })
                print(f"Startup client {c.id} start status: {success}")
            except Exception as e:
                print(f"Erro ao iniciar client {c.id}: {e}")
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
