import sys
import os

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import discord
import asyncio
import logging
from bot.utils.anti_detection import AntiDetectionUtils, RateLimiter
from bot.services.ocr_service import OCRService
from bot.services.gmail_service import GmailService
from backend.database.models import Log, Fila, Pagamento # Adicionando imports
import traceback

class MediacaoBot(discord.Client):
    def __init__(self, client_data: dict, db_session_factory):
        # Utilizar args do discord-py-self
        super().__init__()
        self.db_client_id = client_data.get("id")
        self.client_name = client_data.get("nome")
        
        # Configurações do cliente
        self.config = client_data.get("config_json", {})
        self.email = client_data.get("email")
        self.email_senha = client_data.get("senha_email")
        
        self.logger = logging.getLogger(f"Bot-{self.client_name}")
        self.db_session_factory = db_session_factory
        self.rate_limiter = RateLimiter(actions_per_minute=20)
        
        self.prefix = self.config.get("prefix", "!")
        self.categoria_id = self.config.get("categoria_id") # Categoria onde as salas são criadas
        self.cargo_mediador_id = self.config.get("cargo_mediador_id")

    async def start(self, token: str):
        # We need to wrap it since start is blocking
        try:
            await super().start(token)
        except Exception as e:
            self.logger.error(f"Error in bot start: {e}")
            import traceback
            traceback.print_exc()

    async def on_ready(self):
        self.logger.info(f"Bot {self.client_name} logado como {self.user}!")
        self._log_to_db("info", f"Bot {self.client_name} online como {self.user}")

    def _log_to_db(self, log_type: str, message: str):
        """Salva logs no banco de dados para a dashboard."""
        try:
            db = self.db_session_factory()
            new_log = Log(client_id=self.db_client_id, tipo=log_type, mensagem=message)
            db.add(new_log)
            db.commit()
            db.close()
        except Exception as e:
            self.logger.error(f"Erro ao salvar log no BD: {str(e)}")
            import traceback
            traceback.print_exc()

    async def on_message(self, message):
        # Ignorar mensagens do próprio bot
        if message.author == self.user:
            return

        asyncio.create_task(self.process_message(message))

    async def process_message(self, message):
        try:
            # Rate limiting check
            await self.rate_limiter.wait_if_needed()

            if message.content.startswith(f"{self.prefix}criar_sala"):
                await self.cmd_criar_sala(message)
                
            elif message.content.startswith(f"{self.prefix}verificar_pix"):
                await self.cmd_verificar_pix(message)
                
            # Verificar se é um comprovante em imagem
            if message.attachments:
                await self.check_comprovante_print(message)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {traceback.format_exc()}")
            self._log_to_db("error", f"Erro no bot: {str(e)}")

    async def cmd_criar_sala(self, message):
        """!criar_sala @jogador1 @jogador2 valor"""
        args = message.content.split()[1:]
        if len(args) < 3 or len(message.mentions) < 2:
            await AntiDetectionUtils.natural_action(
                message.reply,
                "Formato correto: `!criar_sala @jog1 @jog2 valor`"
            )
            return

        valor = args[-1]
        
        # Obter guild
        guild = message.guild
        
        # Encontrar categoria
        category = None
        if self.categoria_id:
            category = guild.get_channel(int(self.categoria_id))
            
        # Permissões
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            message.mentions[0]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            message.mentions[1]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        if self.cargo_mediador_id:
            role = guild.get_role(int(self.cargo_mediador_id))
            if role:
                 overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        room_name = f"fila-{message.mentions[0].name}-vs-{message.mentions[1].name}"
        
        await AntiDetectionUtils.random_delay(1.0, 3.0)
        
        channel = await guild.create_text_channel(
            name=room_name,
            category=category,
            overwrites=overwrites
        )

        # Usar Anti-detecção para enviar a msg
        msg_content = (f"Sala criada! {message.mentions[0].mention} e {message.mentions[1].mention}\n"
                       f"Valor da partida: R$ **{valor}**.\n"
                       f"Por favor, enviem o comprovante por print aqui, ou eu posso consultar via `!verificar_pix NOME VALOR` se já foi enviado.")
                       
        await AntiDetectionUtils.natural_action(channel.send, msg_content)
        
        # Gravar no BD
        try:
            db = self.db_session_factory()
            nova_fila = Fila(
                client_id=self.db_client_id,
                canal_id=str(channel.id),
                jogadores=[m.name for m in message.mentions],
                status="aberta"
            )
            db.add(nova_fila)
            db.commit()
            db.close()
            self._log_to_db("success", f"Sala '{room_name}' criada com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao salvar BD fila: {e}")

    async def cmd_verificar_pix(self, message):
        """!verificar_pix Nome Do Jogador Valor"""
        if not self.email or not self.email_senha:
            await AntiDetectionUtils.natural_action(message.reply, "E-mail não configurado.")
            return

        partes = message.content.split(' ', 1)
        if len(partes) < 2:
             await AntiDetectionUtils.natural_action(message.reply, "Formato: !verificar_pix Nome valor")
             return
             
        # Tenta extrair o último termo como valor, e os anteriores como nome
        argumentos = partes[1].split()
        if len(argumentos) < 2:
            return
            
        valor = argumentos[-1]
        nome = " ".join(argumentos[:-1])
        
        await AntiDetectionUtils.natural_action(message.reply, f"Verificando e-mail por Pix de '{nome}' no valor de R${valor}...")
        
        def run_sync_gmail():
             return GmailService.check_payment_email(self.email, self.email_senha, nome, valor)
             
        loop = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(None, run_sync_gmail)
        
        if resultado:
             await AntiDetectionUtils.natural_action(
                 message.channel.send,
                 f"✅ **Pagamento Confirmado via E-mail**!\n"
                 f"Nome: {resultado['nome']}\n"
                 f"Valor: R$ {resultado['valor']}\n"
                 f"Data: {resultado['data']}"
             )
             self._salvar_pagamento(resultado['nome'], resultado['valor'], str(message.channel.id))
        else:
             await AntiDetectionUtils.natural_action(
                 message.channel.send,
                 f"❌ Não encontrei nenhum pix de '{nome}' com valor R${valor} nos emails recentes."
             )

    async def check_comprovante_print(self, message):
        """Verifica se a imagem é um comprovante usando OCR."""
        # Apenas processa se estiver numa sala "fila-*"
        if not message.channel.name.startswith("fila-"):
            return
            
        image_url = message.attachments[0].url
        if not image_url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return

        await AntiDetectionUtils.natural_action(
             message.reply,
             "Analisando comprovante..."
        )
        
        # Executar OCR
        text = await OCRService.extract_text_from_image_url(image_url)
        if not text:
            await AntiDetectionUtils.natural_action(message.channel.send, "Não consegui ler o comprovante.")
            return
            
        # Usamos uma string de 'sucesso' padrao ou verificamos se tem PIX/Transação
        if "comprovante" in text.lower() or "pix" in text.lower() or "transferência" in text.lower():
            # Aprovado via print
            await AntiDetectionUtils.natural_action(
                message.reply,
                "✅ Comprovante reconhecido pelo sistema (OCR)!"
            )
            self._log_to_db("success", f"Comprovante reconhecido no canal {message.channel.name}")
            self._salvar_pagamento(message.author.name, "0", str(message.channel.id)) # Pode refinar para extrair valor depois

    def _salvar_pagamento(self, nome, valor, canal_id):
        try:
            db = self.db_session_factory()
            if isinstance(valor, str):
                valor = valor.replace(',', '.')
            else:
                valor = "0.0"
            pg = Pagamento(
                client_id=self.db_client_id,
                nome_pagador=nome,
                valor=float(valor) if valor else 0.0,
                horario="Agors",
                canal_id=canal_id
            )
            db.add(pg)
            db.commit()
            db.close()
        except Exception as e:
            self.logger.error(f"Erro salvar pag DB: {e}")
