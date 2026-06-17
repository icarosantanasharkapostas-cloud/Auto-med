from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from backend.database.config import Base
from datetime import datetime
import json

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    token = Column(String)
    email = Column(String)
    senha_email = Column(String)
    categoria_salas_id = Column(String)
    cargo_mediador_id = Column(String)
    config_json = Column(Text, default="{}") # Mudamos para Text puro para evitar erro de validação
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    discord_id = Column(String)
    nome = Column(String)
    nivel = Column(String, default="moderador")
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    mensagem = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    valor = Column(Float)
    pagador = Column(String) # Esta é a coluna que estava faltando!
    status = Column(String, default="PENDENTE")
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta = Column(Text)

class Fila(Base):
    __tablename__ = "filas"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    canal_id = Column(String, nullable=False)
    jogadores = Column(ARRAY(String))
    status = Column(String, default="AGUARDANDO_PAGAMENTO")
    tipo_partida = Column(String, default="NORMAL")
    valor_esperado = Column(Float)
    placar_final = Column(String)
    timestamp_finalizacao = Column(DateTime)
    meta = Column(Text)
