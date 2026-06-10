import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
import logging
from typing import Dict
from bot.handlers.bot_instance import MediacaoBot
from backend.database.config import SessionLocal

logger = logging.getLogger("ClientManager")

class ClientManager:
    """Gerencia múltiplas instâncias de clientes Discord (self-bots)"""
    def __init__(self):
        self.active_clients: Dict[int, MediacaoBot] = {}
        self.tasks: Dict[int, asyncio.Task] = {}

    async def start_client(self, client_data: dict) -> bool:
        client_id = client_data.get("id")
        
        if client_id in self.active_clients:
            logger.warning(f"Cliente {client_id} já está rodando.")
            return False
            
        token = client_data.get("token")
        if not token:
            logger.error(f"Cliente {client_id} não possui token.")
            return False

        try:
            bot = MediacaoBot(client_data, db_session_factory=SessionLocal)
            self.active_clients[client_id] = bot
            
            # Criar task para rodar o bot de forma assíncrona
            task = asyncio.create_task(bot.start(token))
            self.tasks[client_id] = task
            
            logger.info(f"Cliente {client_id} ({client_data.get('nome')}) iniciado com sucesso.")
            return True
            
        except Exception as e:
            logger.error(f"Falha ao iniciar cliente {client_id}: {str(e)}")
            if client_id in self.active_clients:
                del self.active_clients[client_id]
            import traceback
            traceback.print_exc()
            return False

    async def stop_client(self, client_id: int) -> bool:
        if client_id not in self.active_clients:
            logger.warning(f"Cliente {client_id} não está rodando.")
            return False
            
        try:
            # Fechar conexão do Discord
            bot = self.active_clients[client_id]
            await bot.close()
            
            # Cancelar a task
            if client_id in self.tasks:
                self.tasks[client_id].cancel()
                del self.tasks[client_id]
                
            del self.active_clients[client_id]
            logger.info(f"Cliente {client_id} parado com sucesso.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar cliente {client_id}: {str(e)}")
            return False
            
    def is_running(self, client_id: int) -> bool:
        return client_id in self.active_clients and not self.active_clients[client_id].is_closed()

    async def shutdown_all(self):
        """Para todos os clientes ativos."""
        client_ids = list(self.active_clients.keys())
        for cid in client_ids:
            await self.stop_client(cid)

# Instância global do gerenciador
manager = ClientManager()
