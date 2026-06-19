# backend/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy import JSON as SA_JSON
from sqlalchemy.dialects.postgresql import ARRAY
from backend.database.config import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    token = Column(String, nullable=False)
    email = Column(String, nullable=True)
    senha_email = Column(String, nullable=True)
    categoria_salas_id = Column(String, nullable=True)
    cargo_mediador_id = Column(String, nullable=True)
    config_json = Column(SA_JSON, nullable=True, default={})
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)
    discord_id = Column(String, nullable=True)
    nome = Column(String, nullable=True)
    nivel = Column(String, default="moderador")
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)
    mensagem = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)
    valor = Column(Float, nullable=True)
    pagador = Column(String, nullable=True)   # nome do pagador / identificador
    status = Column(String, default="PENDENTE")  # esta coluna causou o erro antes
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta = Column(Text, nullable=True)

class Fila(Base):
    __tablename__ = "filas"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    canal_id = Column(String, nullable=False)
    jogadores = Column(ARRAY(String))
    status = Column(String, default="AGUARDANDO_PAGAMENTO")
    tipo_partida = Column(String, default="NORMAL")
    valor_esperado = Column(Float, nullable=True)
    placar_final = Column(String, nullable=True)
    timestamp_finalizacao = Column(DateTime, nullable=True)
    meta = Column(Text, nullable=True)

    def __repr__(self):
        return (f"<Fila id={self.id} canal_id={self.canal_id} "
                f"status={self.status} tipo={self.tipo_partida} valor={self.valor_esperado}>")
