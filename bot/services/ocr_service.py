import aiohttp
import logging
import re
from typing import Optional, Dict, Any
import easyocr
import io

# Carregar leitor apenas uma vez na inicialização para economizar recursos, 
# se houver memória suficiente.
import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import easyocr
    reader = easyocr.Reader(['pt'], gpu=False)
except Exception as e:
    reader = None
    print(f"Error loading easyocr: {e}")

logger = logging.getLogger("OCRService")

class OCRService:
    @staticmethod
    async def extract_text_from_image_url(url: str) -> str:
        """Faz o download da imagem e extrai o texto com OCR"""
        if not reader:
            logger.error("EasyOCR não está inicializado corretamente.")
            return ""
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        
                        # Extrai texto (retorna lista de tuplas)
                        # det[1] contém o texto
                        results = reader.readtext(image_bytes)
                        text = " ".join([det[1] for det in results])
                        return text
                    
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
