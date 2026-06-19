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
    Tenta adicionar colunas faltantes no banco (SQLite/Postgres).
    Executa antes de importar models para evitar problemas de 'no such column'.
    Após confirmar que tudo está ok, remova a chamada a essa função.
    """
    try:
        with engine.begin() as conn:
            # CLIENTS
            clients_cols = [
                ("categoria_salas_id", "TEXT"),
                ("cargo_mediador_id", "TEXT"),
                ("criado_em", "TIMESTAMP")
            ]
            for col, coltype in clients_cols:
                try:
                    conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col} {coltype}"))
                    print(f"[DB-FIX] Tentativa: adicionar clients.{col}")
                except Exception:
                    pass

            # FILAS
            filas_cols = [
                ("status", "TEXT"),
                ("tipo_partida", "TEXT"),
                ("valor_esperado", "NUMERIC"),
                ("placar_final", "TEXT"),
                ("timestamp_finalizacao", "TIMESTAMP"),
                ("meta", "TEXT")
            ]
            for col, coltype in filas_cols:
                try:
                    conn.execute(text(f"ALTER TABLE filas ADD COLUMN {col} {coltype}"))
                    print(f"[DB-FIX] Tentativa: adicionar filas.{col}")
                except Exception:
                    pass

            # PAGAMENTOS (adiciona status, pagador e meta)
            pagamentos_cols = [
                ("status", "TEXT"),
                ("pagador", "TEXT"),
                ("meta", "TEXT")
            ]
            for col, coltype in pagamentos_cols:
                try:
                    conn.execute(text(f"ALTER TABLE pagamentos ADD COLUMN {col} {coltype}"))
                    print(f"[DB-FIX] Tentativa: adicionar pagamentos.{col}")
                except Exception:
                    pass

            # Normaliza config_json (para evitar erro de validação no frontend)
            try:
                conn.execute(text("UPDATE clients SET config_json = '{}' WHERE config_json IS NULL OR config_json = ''"))
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
