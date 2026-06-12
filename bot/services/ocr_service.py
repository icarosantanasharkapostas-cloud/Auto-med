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
    async def extract_text_from_image_url(url: str) -> str:
        """Faz o download da imagem e extrai o texto com OCR (Tesseract)."""
        if not _OCR_DISPONIVEL:
            logger.error("pytesseract/Pillow não estão disponíveis.")
            return ""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        image = Image.open(io.BytesIO(image_bytes))

                        try:
                            text = pytesseract.image_to_string(image, lang=_OCR_LANG)
                        except pytesseract.TesseractError:
                            # Fallback para ingles caso o idioma 'por' nao exista
                            logger.warning(
                                "Idioma '%s' indisponível no Tesseract; usando 'eng'.",
                                _OCR_LANG,
                            )
                            text = pytesseract.image_to_string(image, lang="eng")

                        return text.strip()

            return ""
        except Exception as e:
            logger.error(f"Erro no OCR: {str(e)}")
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
