import aiohttp
import logging
import io
from typing import Optional, Dict, Any

# OCR leve usando Tesseract (via pytesseract) + Pillow.
# Vantagens em relacao ao easyocr: nao puxa o torch e nao compila
# bibliotecas nativas, evitando falhas no deploy (Square Cloud).
# O binario do tesseract-ocr e instalado pelo start.sh.
try:
    import pytesseract
    from PIL import Image
    _OCR_DISPONIVEL = True
except Exception as e:  # pragma: no cover
    pytesseract = None
    Image = None
    _OCR_DISPONIVEL = False
    print(f"Error loading pytesseract/Pillow: {e}")

logger = logging.getLogger("OCRService")

# Idioma do OCR. "por" = portugues (requer o pacote tesseract-ocr-por).
# Se o pacote de portugues nao estiver instalado, cai para "eng".
_OCR_LANG = "por"


class OCRService:
    @staticmethod
    def tesseract_disponivel() -> bool:
        """Verifica se o Tesseract OCR está REALMENTE disponível para uso.

        Não basta o pytesseract estar instalado (a biblioteca Python):
        o PROGRAMA 'tesseract' do sistema também precisa estar instalado.
        Em servidores como a Square Cloud, muitas vezes não há permissão
        para instalar o programa, então checamos aqui antes de tentar usar.
        Retorna True só se tudo estiver pronto. ✅"""
        if not _OCR_DISPONIVEL:
            return False
        try:
            versao = pytesseract.get_tesseract_version()
            print(f"✅ [OCR] Tesseract disponível (versão {versao}).")
            return True
        except Exception as e:
            print(f"⚠️ [OCR] Tesseract NÃO disponível no sistema: {e}")
            return False

    @staticmethod
    async def extract_text_from_image_url(url: str) -> str:
        """Faz o download da imagem e extrai o texto com OCR (Tesseract).
        🔍 Com logs detalhados em cada etapa para facilitar o debug."""
        # Etapa 0: Verificar se o OCR está disponível
        if not _OCR_DISPONIVEL:
            logger.error("❌ [OCR] pytesseract/Pillow NÃO estão disponíveis. OCR desativado.")
            print("❌ [OCR] pytesseract/Pillow NÃO estão instalados! Verifique o requirements.txt e o tesseract-ocr.")
            return ""

        try:
            # Etapa 1: Baixar a imagem
            print(f"🔍 [OCR] Iniciando download da imagem...")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"🔍 [OCR] Status do download: {response.status}")
                    if response.status == 200:
                        image_bytes = await response.read()
                        print(f"✅ [OCR] Imagem baixada, tamanho: {len(image_bytes)} bytes")

                        # Etapa 2: Abrir a imagem com Pillow
                        print(f"🔍 [OCR] Abrindo imagem com Pillow...")
                        image = Image.open(io.BytesIO(image_bytes))
                        print(f"✅ [OCR] Imagem aberta. Formato: {image.format}, Tamanho: {image.size}")

                        # Etapa 3: Rodar o Tesseract (OCR)
                        print(f"🔍 [OCR] Iniciando OCR com Tesseract (idioma: '{_OCR_LANG}')...")
                        try:
                            text = pytesseract.image_to_string(image, lang=_OCR_LANG)
                        except pytesseract.TesseractError as te:
                            # Fallback para ingles caso o idioma 'por' nao exista
                            logger.warning(
                                "Idioma '%s' indisponível no Tesseract; usando 'eng'.",
                                _OCR_LANG,
                            )
                            print(f"⚠️ [OCR] Idioma 'por' indisponível ({te}). Tentando com 'eng'...")
                            text = pytesseract.image_to_string(image, lang="eng")

                        text = text.strip()
                        print(f"✅ [OCR] OCR concluído, texto extraído: {len(text)} caracteres")
                        return text
                    else:
                        print(f"❌ [OCR] Falha no download da imagem (status {response.status}).")

            return ""
        except Exception as e:
            logger.error(f"Erro no OCR: {str(e)}")
            print(f"❌ [OCR] ERRO durante o processamento: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return ""

    @staticmethod
    def verify_payment_data(text: str, expected_name: str, expected_value: str) -> bool:
        """Verifica se os dados esperados estão no texto extraído do OCR"""
        text = text.lower()
        expected_name = expected_name.lower()
        
        # Limpar símbolos de Real do valor
        val = expected_value.replace("r$", "").strip()
        val_point = val.replace(",", ".")
        val_comma = val.replace(".", ",")
        
        name_found = expected_name in text
        value_found = val_point in text or val_comma in text or val in text
        
        return name_found and value_found
