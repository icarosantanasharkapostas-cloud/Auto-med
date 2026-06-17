from sqlalchemy import text

# Script temporário para atualizar o banco na Squad Cloud
def atualizar_banco_squad():
    db = SessionLocal()
    try:
        # Tenta adicionar as colunas uma por uma
        colunas = [
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'AGUARDANDO_PAGAMENTO'",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS tipo_partida VARCHAR DEFAULT 'NORMAL'",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS valor_esperado NUMERIC",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS placar_final VARCHAR",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS timestamp_finalizacao TIMESTAMP",
            "ALTER TABLE filas ADD COLUMN IF NOT EXISTS meta TEXT"
        ]
        for sql in colunas:
            try:
                db.execute(text(sql))
                db.commit()
            except Exception:
                db.rollback() 
        print("Banco de dados verificado e atualizado!")
    finally:
        db.close()
