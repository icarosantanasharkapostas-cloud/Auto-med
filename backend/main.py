import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from backend.database.config import engine, Base, SessionLocal

# --- CORREÇÃO PREVENTIVA (executa ANTES de importar models/router/manager) ---
def correcao_preventiva_sqlite():
    """
    Tenta adicionar colunas faltantes diretamente no banco (compatível com SQLite/Postgres).
    Executa antes de importar models/rotas para evitar erro de "no such column" durante startup.
    """
    # Usamos engine.begin() para garantir transação/commit automático
    try:
        with engine.begin() as conn:
            # Colunas que podem ser enviadas pelo painel para clients
            colunas_clients = [
                ("categoria_salas_id", "VARCHAR"),
                ("cargo_mediador_id", "VARCHAR"),
                ("criado_em", "TIMESTAMP")
            ]
            for col, tipo in colunas_clients:
                try:
                    conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col} {tipo}"))
                    print(f"[DB-FIX] Tentativa: adicionar coluna clients.{col}")
                except Exception:
                    # ignora se já existir ou se não for suportado
                    pass

            # Colunas para a tabela filas
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
                    print(f"[DB-FIX] Tentativa: adicionar coluna filas.{col}")
                except Exception:
                    pass
        print("[DB-FIX] verificação concluída.")
    except Exception as e:
        # Log para debug; não impede a continuação
        print(f"[DB-FIX] Erro ao tentar correção preventiva: {e}")

# Executa a correção antes de importar models/routers que possam ler as tabelas
correcao_preventiva_sqlite()
# ---------------------------------------------------------------------------

# Agora importamos os models e as rotas/manager com segurança
from backend.database.models import Client, Log, Pagamento, Fila, Admin
from backend.api.routes import router
from bot.client_manager import manager

# Inicializa banco de dados (cria tabelas novas se não existirem)
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
