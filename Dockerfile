# ===================================================================
# Dockerfile — Deploy no Railway
# ===================================================================
# Usamos Python 3.11 porque a lib 'discord.py-self' depende do módulo
# 'audioop', que foi REMOVIDO no Python 3.13. No 3.11 tudo funciona
# sem gambiarra. ✅
#
# Diferente da Square Cloud, no Railway TEMOS permissão para instalar
# o Tesseract OCR (via apt), então a leitura de comprovantes por
# imagem também funciona aqui. 🎉
# ===================================================================
FROM python:3.11-slim

WORKDIR /app

# Dependências de sistema:
#  - tesseract-ocr + idioma português (leitura de comprovantes/prints)
#  - postgresql-client (útil para depurar o banco)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências Python primeiro (aproveita cache de build).
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto.
COPY . .

# O Railway injeta a porta na variável de ambiente PORT.
# Se não existir (rodando local), usamos 8000 como padrão.
ENV PORT=8000

# Usamos a forma "shell" do CMD para que a variável $PORT seja expandida.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
