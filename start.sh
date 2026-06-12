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

  # Tenta com 'sudo' caso esteja disponível (alguns ambientes exigem root).
  local SUDO=""
  if command_exists sudo; then
    SUDO="sudo"
  fi

  if command_exists apt-get; then
    $SUDO apt-get update -y || true
    $SUDO apt-get install -y tesseract-ocr tesseract-ocr-por || true
  elif command_exists apk; then
    $SUDO apk add --no-cache tesseract-ocr tesseract-ocr-data-por || true
  elif command_exists yum; then
    $SUDO yum install -y tesseract tesseract-langpack-por || true
  elif command_exists dnf; then
    $SUDO dnf install -y tesseract tesseract-langpack-por || true
  else
    echo "⚠️ Não foi possível detectar um gerenciador de pacotes suportado (apt/apk/yum/dnf)."
  fi

  # -------- Verificação do que foi instalado --------
  echo "🔎 Verificando se o Tesseract ficou disponível..."
  if command_exists tesseract; then
    echo "✅ Tesseract OCR encontrado em: $(command -v tesseract)"
    echo "ℹ️ Versão do Tesseract:"
    tesseract --version 2>&1 | head -n 1 || true
  else
    echo "=============================================================="
    echo "⚠️ ATENÇÃO: O Tesseract OCR NÃO pôde ser instalado neste ambiente."
    echo "   (Em alguns servidores, como a Square Cloud, NÃO há permissão"
    echo "    de root/apt para instalar programas do sistema.)"
    echo ""
    echo "👉 O bot continuará funcionando normalmente! Só a leitura de"
    echo "   imagens (print de comprovante) ficará indisponível."
    echo ""
    echo "✅ SOLUÇÃO: para confirmar um pagamento, digite no canal:"
    echo "      pg Nome do Jogador"
    echo "   Assim o bot busca o Pix direto no Gmail, sem precisar do OCR. 🎉"
    echo "=============================================================="
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
