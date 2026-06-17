# backend/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from backend.database.config import Base
from datetime import datetime

# Tabela de Clientes (Bots)
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    token = Column(String, nullable=False)
    email = Column(String, nullable=True)
    senha_email = Column(String, nullable=True)
    # Campos do painel / frontend
    categoria_salas_id = Column(String, nullable=True)   # ID Categoria Salas
    cargo_mediador_id = Column(String, nullable=True)    # ID Cargo Mediador
    config_json = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

# Tabela de Admins (usuários/admins vinculados ao client)
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)   # opcional: vincular a um client
    discord_id = Column(String, nullable=True)   # id do usuário no Discord (se aplicável)
    nome = Column(String, nullable=True)
    nivel = Column(String, default="moderador")  # exemplo: moderador, admin
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

# Tabela de Logs
class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)
    mensagem = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Tabela de Pagamentos
class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)
    valor = Column(Float, nullable=True)
    pagador = Column(String, nullable=True)
    status = Column(String, default="PENDENTE") # PENDENTE, CONFIRMADO
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta = Column(Text, nullable=True)

# Tabela de Filas (sala / partida)
class Fila(Base):
    __tablename__ = "filas"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    canal_id = Column(String, nullable=False)                # ID do canal/text channel
    jogadores = Column(ARRAY(String))                         # lista dos nomes dos jogadores
    status = Column(String, default="AGUARDANDO_PAGAMENTO")   # AGUARDANDO_PAGAMENTO | EM_ANDAMENTO | FINALIZADA | PAGA
    tipo_partida = Column(String, default="NORMAL")           # NORMAL | GELO_INFINITO
    valor_esperado = Column(Float, nullable=True)             # valor esperado da partida (pode ser NULL)
    placar_final = Column(String, nullable=True)              # "9 x 7", por exemplo
    timestamp_finalizacao = Column(DateTime, nullable=True)   # data/hora em que a partida foi finalizada
    meta = Column(Text, nullable=True)                        # campo livre para armazenar JSON/texto auxiliar

    def __repr__(self):
        return (f"<​Fila id={self.id} canal_id={self.canal_id} "
                f"status={self.status} tipo={self.tipo_partida} valor_esperado={self.valor_esperado}>")
