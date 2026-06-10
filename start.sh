#!/usr/bin/env bash
set -euo pipefail

echo "=============================================================="
echo "🚀 Iniciando Discord Mediação Bot (Square Cloud)"
echo "=============================================================="

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# -------- Funções utilitárias --------
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_tesseract_if_needed() {
  if command_exists tesseract; then
    echo "✅ Tesseract OCR já está instalado."
    return 0
  fi

  echo "⚠️ Tesseract OCR não encontrado. Tentando instalar..."

  if command_exists apt-get; then
    apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-por || true
  elif command_exists apk; then
    apk add --no-cache tesseract-ocr || true
  elif command_exists yum; then
    yum install -y tesseract tesseract-langpack-por || true
  else
    echo "⚠️ Não foi possível detectar um gerenciador de pacotes suportado (apt/apk/yum)."
  fi

  if command_exists tesseract; then
    echo "✅ Tesseract OCR instalado com sucesso."
  else
    echo "⚠️ Tesseract OCR continua indisponível. O sistema ainda pode funcionar,"
    echo "   mas recursos de OCR podem falhar dependendo da configuração."
  fi
}

# -------- Verificações iniciais --------
if ! command_exists python3; then
  echo "❌ Python3 não encontrado no ambiente."
  exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

if [ ! -f "requirements.txt" ]; then
  echo "❌ Arquivo requirements.txt não encontrado em $PROJECT_ROOT"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "⚠️ Arquivo .env não encontrado. Tentando criar a partir de .env.example..."
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✅ Arquivo .env criado automaticamente."
    echo "⚠️ IMPORTANTE: revise as variáveis no .env antes de usar em produção."
  else
    echo "❌ .env.example não encontrado. Crie manualmente o arquivo .env."
    exit 1
  fi
fi

# -------- Dependências Python --------
echo "📦 Verificando dependências Python..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "✅ Dependências Python instaladas."

# -------- Dependências de OCR --------
install_tesseract_if_needed

# -------- Inicialização --------
HOST="${API_HOST:-0.0.0.0}"
PORT="${PORT:-${API_PORT:-8000}}"

echo "🌐 Iniciando aplicação em ${HOST}:${PORT}"
exec python3 -m uvicorn backend.main:app --host "$HOST" --port "$PORT"
