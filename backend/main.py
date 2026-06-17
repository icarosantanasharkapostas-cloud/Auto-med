# --- INÍCIO DO BLOCO: atualização única de schema (cole tudo junto) ---
from sqlalchemy import text
from backend.database.config import SessionLocal

def atualizar_banco_automatico():
    """
    Executa ALTER TABLE IF NOT EXISTS para garantir que as colunas novas existam.
    Funciona como operação one-shot ao iniciar a aplicação.
    """
    db = SessionLocal()
    try:
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
                print("[update-db] OK:", sql)
            except Exception as e:
                db.rollback()
                print("[update-db] erro (ignorado):", sql, "->", str(e))
        print("[update-db] verificação concluída.")
    finally:
        db.close()
# --- FIM DO BLOCO ---
