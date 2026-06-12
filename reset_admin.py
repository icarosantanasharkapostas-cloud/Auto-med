#!/usr/bin/env python3
"""
===================================================================
 reset_admin.py — Cria ou redefine o usuário admin da dashboard
===================================================================
Use este script quando NÃO conseguir fazer login no painel
(por exemplo, quando as variáveis ADMIN_USERNAME / ADMIN_PASSWORD
não funcionam na hospedagem).

Ele conecta no MESMO banco de dados configurado em DATABASE_URL,
cria (ou atualiza) o usuário admin com uma senha padrão e guarda
a senha com HASH (passlib), nunca em texto puro.

COMO USAR:
  No terminal, dentro da pasta do projeto, rode:
      python3 reset_admin.py

  Para usar um usuário/senha diferentes do padrão:
      python3 reset_admin.py meu_usuario minha_senha

Depois de logar, TROQUE a senha por uma forte! 🔐
===================================================================
"""

import os
import sys

# Garante que conseguimos importar os módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from passlib.context import CryptContext

from backend.database.config import engine, SessionLocal, Base
from backend.database.models import Admin

# Credenciais padrão (podem ser trocadas via argumentos de linha de comando)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

# Mesmo esquema de hash usado no login (pbkdf2_sha256 = puro Python)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def reset_admin(username: str, password: str) -> None:
    """Cria ou atualiza o usuário admin no banco de dados."""
    # Garante que as tabelas existam (cria se ainda nao existirem)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        password_hash = pwd_context.hash(password)

        admin = db.query(Admin).filter(Admin.username == username).first()
        if admin:
            admin.password_hash = password_hash
            acao = "ATUALIZADO"
        else:
            admin = Admin(username=username, password_hash=password_hash)
            db.add(admin)
            acao = "CRIADO"

        db.commit()

        print("=" * 55)
        print(f"✅ Usuário admin {acao} com sucesso!")
        print("=" * 55)
        print(f"  👤 Usuário: {username}")
        print(f"  🔑 Senha:   {password}")
        print("=" * 55)
        print("⚠️  Faça login com essas credenciais e TROQUE a senha depois!")
        print("=" * 55)
    except Exception as e:
        db.rollback()
        print("❌ Erro ao redefinir o admin:", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Permite passar usuario e senha como argumentos (opcional)
    usuario = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    senha = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASSWORD

    db_url = os.getenv("DATABASE_URL", "sqlite:///./mediacao.db")
    print(f"🗄️  Banco de dados em uso: {db_url}")
    reset_admin(usuario, senha)
