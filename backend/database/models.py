from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

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


