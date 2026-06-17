from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from backend.database.config import Base
from datetime import datetime

# Tabela de Clientes (Bots)
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    token = Column(String, nullable=False)
    email = Column(String)
    senha_email = Column(String)
    config_json = Column(Text)
    ativo = Column(Boolean, default=True)

# Tabela de Logs
class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    mensagem = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Tabela de Pagamentos
class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    valor = Column(Float)
    pagador = Column(String)
    status = Column(String) # PENDENTE, CONFIRMADO
    timestamp = Column(DateTime, default=datetime.utcnow)

# Tabela de Filas (A que atualizamos antes)
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
        return f"<​Fila id={self.id} status={self.status}>"
