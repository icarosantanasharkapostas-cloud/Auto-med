import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from bot.client_manager import manager
from .schemas import ClientCreate, ClientUpdate, ClientOut, LoginSchema, TokenSchema
from backend.database.models import Client, Log, Pagamento, Fila
from backend.database.config import get_db
import os
import jwt
from datetime import datetime, timedelta

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "minha_chave_secreta_padrao")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- AUTENTICAÇÃO ---
@router.post("/auth/login", response_model=TokenSchema)
def login(dados: LoginSchema):
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin")
    
    if dados.username != admin_user or dados.password != admin_pass:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
    token = create_access_token({"sub": admin_user})
    return {"access_token": token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# --- CLIENTES CRUD ---
@router.get("/clients", response_model=list[ClientOut])
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()

@router.post("/clients", response_model=ClientOut)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(**client_data.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    if manager.is_running(client_id):
        await manager.stop_client(client_id)
        
    db.delete(db_client)
    db.commit()
    return {"message": "Cliente removido"}

# --- CONTROLE BOT ---
@router.post("/clients/{client_id}/start")
async def start_client_bot(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
         raise HTTPException(status_code=404)
         
    db_client.ativo = True
    db.commit()
    
    success = await manager.start_client({
        "id": db_client.id,
        "nome": db_client.nome,
        "token": db_client.token,
        "email": db_client.email,
        "senha_email": db_client.senha_email,
        "config_json": db_client.config_json
    })
    
    return {"success": success, "status": "online" if success else "erro"}

@router.post("/clients/{client_id}/stop")
async def stop_client_bot(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if db_client:
        db_client.ativo = False
        db.commit()
        
    success = await manager.stop_client(client_id)
    return {"success": success, "status": "offline"}

@router.get("/clients/{client_id}/status")
def client_status(client_id: int):
    return {"online": manager.is_running(client_id)}

# --- ESTATÍSTICAS E LOGS ---
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_clientes = db.query(Client).count()
    clientes_ativos = sum(1 for c in db.query(Client).all() if manager.is_running(c.id))
    salas_criadas = db.query(Fila).count()
    pagamentos_processados = db.query(Pagamento).count()
    return {
        "total_clientes": total_clientes,
        "clientes_ativos": clientes_ativos,
        "salas_criadas": salas_criadas,
        "pagamentos_processados": pagamentos_processados
    }

@router.get("/logs/{client_id}")
def get_logs(client_id: int, limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(Log).filter(Log.client_id == client_id).order_by(Log.timestamp.desc()).limit(limit).all()
    return logs
    
# --- WEBSOCKET PARA LOGS LIVE ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

ws_manager = ConnectionManager()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Apenas mantém conexão viva
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
