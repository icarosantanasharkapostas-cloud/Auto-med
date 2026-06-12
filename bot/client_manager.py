
import sys
import os
import asyncio
import logging
import traceback
from typing import Dict, Optional, Any, List

# Ajuste o sys.path se necessário (mantive sua lógica original)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bot.handlers.bot_instance import MediacaoBot
from backend.database.config import SessionLocal
from backend.models import Client  # ajuste o import conforme seu modelo real, se diferente

logger = logging.getLogger("ClientManager")
logger.setLevel(logging.INFO)

class ClientManager:
    """Gerencia múltiplas instâncias de clientes Discord (self-bots)."""

    def __init__(self, db_session_factory=SessionLocal):
        self.active_clients: Dict[int, MediacaoBot] = {}
        self.tasks: Dict[int, asyncio.Task] = {}
        self._stop_flags: Dict[int, asyncio.Event] = {}
        self.db_session_factory = db_session_factory
        # parâmetros de retry configuráveis
        self.max_retries = 5
        self.retry_base_delay = 3  # segundos

    async def _client_runner(self, client_id: int, bot: MediacaoBot, token: str):
        """Wrapper que roda o bot e faz retries em caso de falha."""
        attempt = 0
        stop_event = self._stop_flags.get(client_id) or asyncio.Event()
        self._stop_flags[client_id] = stop_event

        while not stop_event.is_set():
            try:
                logger.info(f"[{client_id}] Iniciando bot (tentativa {attempt + 1}).")
                # Obs: bot.start é uma coroutine que roda até o bot ser finalizado.
                await bot.start(token)
                # Se start retornar normalmente, é porque o bot finalizou sem exceção.
                logger.info(f"[{client_id}] Bot finalizou a execução normalmente.")
                break

            except asyncio.CancelledError:
                logger.info(f"[{client_id}] Task cancelada. Encerrando bot.")
                try:
                    await bot.close()
                except Exception:
                    logger.exception(f"[{client_id}] Erro ao fechar o bot após cancelamento.")
                break

            except Exception as exc:
                attempt += 1
                logger.exception(f"[{client_id}] Erro na execução do bot: {exc}")
                if attempt >= self.max_retries:
                    logger.error(f"[{client_id}] Atingido max_retries ({self.max_retries}). Parando tentativas.")
                    break

                delay = self.retry_base_delay * attempt
                logger.info(f"[{client_id}] Retentando em {delay}s (attempt {attempt}/{self.max_retries}).")
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=delay)
                    # se stop_event.set() aconteceu, saímos do loop
                    if stop_event.is_set():
                        break
                except asyncio.TimeoutError:
                    # timeout => vamos tentar de novo
                    continue

        # limpeza após sair do loop
        logger.info(f"[{client_id}] Limpando estado local do manager.")
        self.tasks.pop(client_id, None)
        self._stop_flags.pop(client_id, None)
        self.active_clients.pop(client_id, None)

    async def start_client(self, client_data: dict) -> bool:
        """
        Inicia um cliente novo.
        client_data deve conter ao menos: { "id": int, "token": str, "nome": str, ... }
        """
        client_id = client_data.get("id")
        if client_id is None:
            logger.error("Dados do cliente inválidos: falta 'id'.")
            return False

        if client_id in self.active_clients:
            logger.warning(f"Cliente {client_id} já está rodando.")
            return False

        token = client_data.get("token")
        if not token:
            logger.error(f"Cliente {client_id} não possui token.")
            return False

        try:
            # Cria instância do bot (seu construtor deve aceitar client_data e factory)
            bot = MediacaoBot(client_data, db_session_factory=self.db_session_factory)
            self.active_clients[client_id] = bot

            # Cria e armazena a task wrapper
            task = asyncio.create_task(self._client_runner(client_id, bot, token), name=f"client-{client_id}")
            self.tasks[client_id] = task

            logger.info(f"Cliente {client_id} ({client_data.get('nome')}) iniciado com sucesso.")
            return True

        except Exception as e:
            logger.exception(f"Falha ao iniciar cliente {client_id}: {e}")
            # garantia de limpeza
            self.active_clients.pop(client_id, None)
            self.tasks.pop(client_id, None)
            return False

    async def stop_client(self, client_id: int, wait_timeout: float = 8.0) -> bool:
        """Para cliente: sinaliza stop, cancela task e fecha conexão do bot."""
        if client_id not in self.tasks and client_id not in self.active_clients:
            logger.warning(f"Cliente {client_id} não está rodando.")
            return False

        logger.info(f"[{client_id}] Solicitando parada do cliente.")
        # sinaliza para o runner parar
        if client_id in self._stop_flags:
            self._stop_flags[client_id].set()

        # cancel task explicitamente
        task = self.tasks.get(client_id)
        if task:
            task.cancel()

            try:
                await asyncio.wait_for(task, timeout=wait_timeout)
            except asyncio.TimeoutError:
                logger.warning(f"[{client_id}] Task não finalizou em {wait_timeout}s após cancelamento.")

        # garante fechamento do bot
        bot = self.active_clients.get(client_id)
        if bot:
            try:
                await bot.close()
            except Exception:
                logger.exception(f"[{client_id}] Erro ao fechar o bot durante stop_client.")

        # limpeza final
        self.tasks.pop(client_id, None)
        self._stop_flags.pop(client_id, None)
        self.active_clients.pop(client_id, None)

        logger.info(f"Cliente {client_id} parado com sucesso.")
        return True

    def is_running(self, client_id: int) -> bool:
        """Retorna True se existe task em execução para o client_id."""
        task = self.tasks.get(client_id)
        if not task:
            return False
        return not task.done()

    async def shutdown_all(self):
        """Para todos os clientes ativos."""
        logger.info("Shutting down all clients...")
        client_ids = list(self.tasks.keys())
        # signal all to stop
        for cid in client_ids:
            if cid in self._stop_flags:
                self._stop_flags[cid].set()
            if cid in self.tasks:
                self.tasks[cid].cancel()
        # await tasks
        for cid in client_ids:
            task = self.tasks.get(cid)
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception(f"Erro ao aguardar task do cliente {cid} durante shutdown.")
        logger.info("Shutdown completo.")

    async def start_all_from_db(self, only_enabled: bool = True) -> List[int]:
        """
        Lê clientes do banco e inicia os que não estão rodando.
        Retorna a lista de client_ids iniciados com sucesso.
        """
        started = []
        session = None
        try:
            session = self.db_session_factory()
            # Ajuste a query conforme seu modelo Client
            query = session.query(Client)
            if only_enabled:
                query = query.filter(Client.enabled == True)
            clients = query.all()
            for c in clients:
                client_dict = {
                    "id": c.id,
                    "token": c.token,
                    "nome": getattr(c, "nome", f"client-{c.id}"),
                    # inclua outros campos se necessário
                }
                if client_dict["id"] in self.active_clients:
                    logger.debug(f"[{c.id}] Já está rodando, pulando.")
                    continue
                ok = await self.start_client(client_dict)
                if ok:
                    started.append(c.id)
            return started

        except Exception:
            logger.exception("Erro ao iniciar clients a partir do DB.")
            return started

        finally:
            if session:
                session.close()

# Instância global do gerenciador
manager = ClientManager()
