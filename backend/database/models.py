# backend/database/models.py
# ===================================================================
# MODELOS DO BANCO DE DADOS (SQLAlchemy)
# ===================================================================
# ⚠️ CORREÇÃO IMPORTANTE (Railway):
#   Antes o modelo Fila usava ARRAY(String) do PostgreSQL. Esse tipo
#   NÃO existe no SQLite e quebrava a criação da tabela no Railway com:
#       sqlalchemy.exc.CompileError ... type ARRAY
#   Agora usamos o tipo JSON genérico (funciona em SQLite E PostgreSQL),
#   guardando a lista de jogadores como JSON. 100% compatível. ✅
#
# ✅ As colunas abaixo foram alinhadas EXATAMENTE com o que o código do
#    bot e das rotas realmente usa, corrigindo os erros "no such column"
#    (pagamentos.status, pagamentos.pagador, clients.criado_em, etc).
# ===================================================================
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy import JSON as SA_JSON
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
    config_json = Column(SA_JSON, nullable=True, default=dict)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    # 🔑 Colunas usadas pelo login/painel (routes.py e reset_admin.py).
    #    Antes elas NÃO existiam e o login pelo banco quebrava.
    username = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    # Campos antigos mantidos (opcionais) para compatibilidade.
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
    # 🏷️ 'tipo' é usado pelo bot (_log_to_db) e pelo frontend (l.tipo).
    #    Antes não existia e todo log falhava silenciosamente.
    tipo = Column(String, default="info")
    mensagem = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=True)
    # 👤 Nome de quem pagou (o bot salva em 'nome_pagador').
    nome_pagador = Column(String, nullable=True)
    valor = Column(Float, nullable=True)
    # 🕒 Horário em texto (ISO) — o bot grava com datetime.utcnow().isoformat().
    horario = Column(String, nullable=True)
    # 📺 Canal do Discord onde o pagamento foi registrado.
    canal_id = Column(String, nullable=True)
    status = Column(String, default="CONFIRMADO")
    meta = Column(Text, nullable=True)
    # Mantido por compatibilidade com dados/consultas antigas.
    timestamp = Column(DateTime, default=datetime.utcnow)


class Fila(Base):
    __tablename__ = "filas"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    canal_id = Column(String, nullable=False)
    # ✅ JSON no lugar de ARRAY -> compatível com SQLite e PostgreSQL.
    #    Guarda a lista de jogadores, ex.: ["Joao", "Maria"].
    jogadores = Column(SA_JSON, nullable=True, default=list)
    status = Column(String, default="AGUARDANDO_PAGAMENTO")
    tipo_partida = Column(String, default="NORMAL")
    valor_esperado = Column(Float, nullable=True)
    placar_final = Column(String, nullable=True)
    timestamp_finalizacao = Column(DateTime, nullable=True)
    meta = Column(Text, nullable=True)

    def __repr__(self):
        return (f"<Fila id={self.id} canal_id={self.canal_id} "
                f"status={self.status} tipo={self.tipo_partida} valor={self.valor_esperado}>")
