import asyncio
import random
from typing import Callable, Any
import logging

logger = logging.getLogger("AntiDetection")

class AntiDetectionUtils:
    """
    Utilitários para simular comportamento humano e evitar que as contas sejam marcadas como self-bot.
    """

    @staticmethod
    async def random_delay(min_sec: float = 2.0, max_sec: float = 5.0):
        """Adiciona um atraso aleatório para simular tempo de reação humana.
        Delays AUMENTADOS (2 a 5 segundos) para o bot parecer mais humano. 🧑"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    @staticmethod
    async def simulate_typing(channel, duration: float = None):
        """Simula o indicador de digitação por um tempo."""
        try:
            if not duration:
                duration = random.uniform(1.5, 4.0)
            async with channel.typing():
                await asyncio.sleep(duration)
        except Exception as e:
            logger.error(f"Erro ao simular digitação: {e}")

    @staticmethod
    def get_random_user_agent():
        """Retorna um user agent realista."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        ]
        return random.choice(user_agents)

    @staticmethod
    async def natural_action(func: Callable, *args, **kwargs) -> Any:
        """
        Executa uma função (como enviar mensagem) encapsulada com delays e digitação, simulando a ação natural.
        Uso:
        await AntiDetectionUtils.natural_action(channel.send, "Olá!")
        """
        # Delay de reação inicial ANTES de responder (2 a 5s) — parece mais humano 🧑
        await AntiDetectionUtils.random_delay(2.0, 5.0)
        
        # Simula tempo de digitação baseando-se no tamanho da mensagem (se for um send)
        content_length = 0
        if len(args) > 0 and isinstance(args[0], str):
            content_length = len(args[0])
        elif 'content' in kwargs and isinstance(kwargs['content'], str):
            content_length = len(kwargs['content'])
            
        typing_time = min(8.0, max(2.0, content_length * 0.08)) # ~80ms por caractere, min 2s, max 8s
        
        # Obter o object (channel) da função se possível para chamar digitação
        channel = getattr(func.__self__, 'typing', None)
        if channel:
            async with func.__self__.typing():
                await asyncio.sleep(typing_time)
        else:
            await asyncio.sleep(typing_time)

        # Pequena variação antes de apertar 'Enter'
        await AntiDetectionUtils.random_delay(0.1, 0.4)
        
        return await func(*args, **kwargs)

class RateLimiter:
    """Implementa limite de taxas para evitar spam e deteções de automação excessiva."""
    def __init__(self, actions_per_minute: int = 5):
        # Máximo de 5 ações por minuto por padrão (antes era 15).
        # Menos ações = menos chance de o Discord detectar automação. 🐢
        self.actions_per_minute = actions_per_minute
        self.action_timestamps = []

    async def wait_if_needed(self):
        now = asyncio.get_event_loop().time()
        
        # Limpar timestamps antigos (> 60s)
        self.action_timestamps = [t for t in self.action_timestamps if now - t < 60]
        
        if len(self.action_timestamps) >= self.actions_per_minute:
            # Precisa esperar até que a ação mais antiga complete 1 minuto
            oldest = self.action_timestamps[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                logger.warning(f"Rate limit atingido. Esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
        self.action_timestamps.append(asyncio.get_event_loop().time())
