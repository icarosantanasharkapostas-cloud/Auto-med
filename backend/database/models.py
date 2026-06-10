from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .config import Base

class Client(Base):
    """Modelo para representar um cliente do bot (a conta de um mediador)"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    token = Column(String)
    email = Column(String, nullable=True)
    senha_email = Column(String, nullable=True) # Idealmente criptografada em um sistema real
    ativo = Column(Boolean, default=False)
    config_json = Column(JSON, default={})
    discord_id = Column(String, nullable=True) # Pra salvar o ID da conta do cliente
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    logs = relationship("Log", back_populates="client", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="client", cascade="all, delete-orphan")
    filas = relationship("Fila", back_populates="client", cascade="all, delete-orphan")


class Log(Base):
    """Modelo para logs do sistema por cliente"""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    tipo = Column(String) # info, warning, error, success
    mensagem = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="logs")


class Pagamento(Base):
    """Modelo para pagamentos verificados"""
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    nome_pagador = Column(String)
    valor = Column(Float)
    horario = Column(String) # Horário que consta no recibo
    canal_id = Column(String) # Canal do discord onde foi enviado o comprovante
    processado_em = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="pagamentos")


class Fila(Base):
    """Modelo de fila/sala de jogo criada"""
    __tablename__ = "filas"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    canal_id = Column(String)
    jogadores = Column(JSON, default=[]) # Lista de menções ou nomes
    status = Column(String) # aberta, fechada, em_andamento
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="filas")

