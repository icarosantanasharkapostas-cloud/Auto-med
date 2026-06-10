import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.database.config import engine, Base, SessionLocal
from backend.api.routes import router
from bot.client_manager import manager
from backend.database.models import Client, Log, Pagamento, Fila

# Inicializa banco de dados
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
