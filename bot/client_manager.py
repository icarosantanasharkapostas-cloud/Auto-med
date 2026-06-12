import sys
import os
import asyncio
import logging
import traceback
from typing import Dict, Optional, Any, List
from sqlalchemy import text

# Ajuste o sys.path para garantir que o Python veja as pastas raiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bot.handlers.bot_instance import MediacaoBot
from backend.database.config import SessionLocal

# TENTATIVA DE IMPORTAR O MODELO (Ajustado para sua pasta 'banco de dados')
try:
    # No Python, espaços em nomes de pastas podem causar erro de importação.
    # Se a pasta no GitHub se chama exatamente "banco de dados" (com espaço), 
    # o ideal é renomeá-la para "database" ou "banco_de_dados".
    # Vou usar o fallback para garantir que o bot ligue mesmo se o import falhar.
    from backend.database.models import Client
except ImportError:
    try:
        # Outra tentativa caso a pasta use sublinhado
        from backend.banco_de_dados.models import Client
    except ImportError:
        Client = None

logger = logging.getLogger("ClientManager")
logger.setLevel(logging.INFO)

class ClientManager:
    """Gerencia múltiplas instâncias de clientes Discord (self-bots)."""

    def __init__(self, db_session_factory=SessionLocal):
        self.active_clients: Dict[int, MediacaoBot] = {}
        self.tasks: Dict[int, asyncio.Task] = {}
        self._stop_flags: Dict[int, asyncio.Event] = {}
        self.db_session_factory = db_session_factory
        self.max_retries = 5
        self.retry_base_delay = 3 

    async def _client_runner(self, client_id: int, bot: MediacaoBot, token: str):
        """Wrapper que roda o bot e faz retries em caso de falha."""
        attempt = 0
        stop_event = self._stop_flags.get(client_id) or asyncio.Event()
        self._stop_flags[client_id] = stop_event

        while not stop_event.is_set():
            try:
                logger.info(f"[{client_id}] Iniciando bot (tentativa {attempt + 1}).")
                await bot.start(token)
                break
            except asyncio.CancelledError:
                logger.info(f"[{client_id}] Task cancelada. Encerrando bot.")
                try: await bot.close()
                except: pass
                break
            except Exception as exc:
                attempt += 1
                logger.error(f"[{client_id}] Erro na execução do bot: {exc}")
                if attempt >= self.max_retries: break
                delay = self.retry_base_delay * attempt
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=delay)
                    if stop_event.is_set(): break
                except asyncio.TimeoutError:
                    continue

        self.tasks.pop(client_id, None)
        self.active_clients.pop(client_id, None)

    async def start_client(self, client_data: dict) -> bool:
        client_id = client_data.get("id")
        if client_id in self.active_clients: return False
        token = client_data.get("token")
        if not token: return False

        try:
            bot = MediacaoBot(client_data, db_session_factory=self.db_session_factory)
            self.active_clients[client_id] = bot
            task = asyncio.create_task(self._client_runner(client_id, bot, token), name=f"client-{client_id}")
            self.tasks[client_id] = task
            return True
        except Exception as e:
            logger.error(f"Falha ao iniciar cliente {client_id}: {e}")
            return False

    async def stop_client(self, client_id: int) -> bool:
        if client_id not in self.tasks: return False
        if client_id in self._stop_flags: self._stop_flags[client_id].set()
        task = self.tasks.get(client_id)
        if task: task.cancel()
        bot = self.active_clients.get(client_id)
        if bot:
            try: await bot.close()
            except: pass
        self.tasks.pop(client_id, None)
        self.active_clients.pop(client_id, None)
        return True

    async def start_all_from_db(self, only_enabled: bool = True) -> List[int]:
        """Lê clientes do banco e inicia os que não estão rodando."""
        started = []
        session = None
        try:
            session = self.db_session_factory()
            
            # Se o Client (ORM) foi importado, usa ele. Se não, usa SQL PURO.
            if Client:
                query = session.query(Client)
                if only_enabled:
                    query = query.filter(Client.enabled == True)
                clients = query.all()
                for c in clients:
                    c_data = {"id": c.id, "token": c.token, "nome": getattr(c, "nome", "Bot")}
                    if await self.start_client(c_data): started.append(c.id)
            else:
                # FALLBACK SQL PURO (Funciona mesmo se o import de models quebrar)
                sql = "SELECT id, token, nome FROM clients"
                if only_enabled: sql += " WHERE enabled = 1"
                result = session.execute(text(sql))
                for row in result:
                    # tenta pegar os campos independente de ser objeto ou dicionário
                    r = row._asdict() if hasattr(row, '_asdict') else row
                    c_data = {"id": r[0], "token": r[1], "nome": r[2]}
                    if await self.start_client(c_data): started.append(r[0])
            
            return started
        except Exception as e:
            logger.error(f"Erro no start_all_from_db: {e}")
            return started
        finally:
            if session: session.close()

# Instância global
manager = ClientManager()
