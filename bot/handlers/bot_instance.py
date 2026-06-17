import sys
import os
# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import discord
import asyncio
import logging
import re
from datetime import datetime, timedelta

# 🩹 Aplica a correção do bug do discord.py-self LOGO no início
from bot.utils.discord_patch import aplicar_patch_discord
aplicar_patch_discord()
from bot.utils.anti_detection import AntiDetectionUtils, RateLimiter
from bot.services.ocr_service import OCRService
from bot.services.gmail_service import GmailService
from backend.database.models import Log, Fila, Pagamento
import traceback

class MediacaoBot(discord.Client):
    def __init__(self, client_data: dict, db_session_factory):
        super().__init__()
        self.db_client_id = client_data.get("id")
        self.client_name = client_data.get("nome") or "SemNome"
        self.config = client_data.get("config_json") or {}
        if not isinstance(self.config, dict):
            self.config = {}
        self.email = client_data.get("email")
        self.email_senha = client_data.get("senha_email")
        self.logger = logging.getLogger(f"Bot-{self.client_name}")
        self.db_session_factory = db_session_factory
        self.rate_limiter = RateLimiter(actions_per_minute=5)
        self.prefix = self.config.get("prefix") or "!"
        self.categoria_id = self.config.get("categoria_id")
        self.cargo_mediador_id = self.config.get("cargo_mediador_id")
        self.palavras_chave_canal = self.config.get("palavras_chave_canal") or ["fila", "filas", "partidas", "pagar"]
        self.valor_fila_padrao = self.config.get("valor_fila_padrao") or 5.50
        self.nome_recebedor_pix = self.config.get("nome_recebedor_pix") or ""

        print("=" * 50)
        print(f"🤖 Inicializando bot do cliente: {self.client_name}")
        print(f"🔎 [DEBUG] config: {self.config}")
        print(f"🔎 [DEBUG] prefix: {self.prefix}")
        print(f"🔎 [DEBUG] categoria_id: {self.categoria_id}")
        print(f"🔎 [DEBUG] cargo_mediador_id: {self.cargo_mediador_id}")
        print(f"🔎 [DEBUG] palavras_chave_canal: {self.palavras_chave_canal}")
        print(f"🔎 [DEBUG] valor_fila_padrao: {self.valor_fila_padrao}")
        print(f"🔎 [DEBUG] nome_recebedor_pix: '{self.nome_recebedor_pix}'")
        print("=" * 50)

    # ------------------------
    # Início: Conexão e logs
    # ------------------------
    async def start(self, token: str):
        print(f"🚀 [DEBUG] Tentando iniciar o bot '{self.client_name}'...")
        if token is None:
            msg = "❌ ERRO: O token do bot está VAZIO (None). Verifique o cadastro do cliente no banco de dados!"
            self.logger.error(msg)
            self._log_to_db("error", msg)
            print(msg)
            return
        if not isinstance(token, str):
            msg = f"❌ ERRO: O token precisa ser um texto (str), mas veio como {type(token).__name__}."
            self.logger.error(msg)
            self._log_to_db("error", msg)
            print(msg)
            return
        token = token.strip()
        if token == "":
            msg = "❌ ERRO: O token do bot está em branco. Cadastre um token válido para este cliente!"
            self.logger.error(msg)
            self._log_to_db("error", msg)
            print(msg)
            return
        print(f"🔑 [DEBUG] Token recebido (tamanho: {len(token)} caracteres). Conectando...")
        max_tentativas = 3
        for tentativa in range(1, max_tentativas + 1):
            try:
                print(f"🔄 [DEBUG] Tentativa {tentativa} de {max_tentativas} de conexão...")
                await super().start(token)
                return
            except TypeError as e:
                msg = (f"⚠️ Tentativa {tentativa} falhou (erro de dados nulos): {e}. "
                       f"Isso geralmente é instabilidade temporária do Discord/internet.")
                self.logger.error(msg)
                print(msg)
                traceback.print_exc()
                if tentativa < max_tentativas:
                    print("⏳ Aguardando 5 segundos antes de tentar novamente...")
                    await asyncio.sleep(5)
                else:
                    erro_final = (f"❌ Não foi possível conectar o bot '{self.client_name}' "
                                  f"após {max_tentativas} tentativas. Erro: {e}")
                    self.logger.error(erro_final)
                    self._log_to_db("error", erro_final)
                    print(erro_final)
            except Exception as e:
                erro_final = f"❌ Erro ao iniciar o bot '{self.client_name}': {type(e).__name__}: {e}"
                self.logger.error(erro_final)
                self._log_to_db("error", erro_final)
                print(erro_final)
                traceback.print_exc()
                return

    async def on_ready(self):
        self.logger.info(f"Bot {self.client_name} logado como {self.user}!")
        self._log_to_db("info", f"Bot {self.client_name} online como {self.user}")
        print("=" * 50)
        print(f"🟢 BOT ONLINE: {self.user} (cliente: {self.client_name})")
        print(f"👀 Prefixo dos comandos: '{self.prefix}'")
        print(f"📡 Servidores conectados: {len(self.guilds)}")
        print("✅ Aguardando mensagens... (vou logar cada uma que chegar)")
        print("=" * 50)

    def _log_to_db(self, log_type: str, message: str):
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

    # ------------------------
    # Helpers: regex / normalização
    # ------------------------
    def _normalize_spaces(self, s: str) -> str:
        return re.sub(r'\s+', ' ', s).strip()

    def _detect_payment_mention(self, text: str):
        """
        Detecta variações de 'pagar' e tenta extrair um nome.
        Retorna None ou dict {'name': str|None, 'indicator': str}
        """
        if not text:
            return None
        t = text.strip()
        indicators = [
            r'\bpg\b', r'\bp\.g\b', r'\bp g\b', r'\bpgo\b', r'\bpago\b',
            r'\bpagou\b', r'\bpaguei\b', r'\bpag\b', r'\bpg\.\b'
        ]
        indicator_pat = re.compile('|'.join(indicators), re.IGNORECASE)

        pat1 = re.compile(
            r'^(?P<name>[A-Za-zÀ-ÿ0-9 .,_\-\[\]\(\)]{2,60})\s*(?P<ind>' + '|'.join([p.strip(r'\b') for p in indicators]) + r')\b',
            re.IGNORECASE
        )
        pat2 = re.compile(
            r'^(?P<ind>' + '|'.join([p.strip(r'\b') for p in indicators]) + r')[:\s\-]*\s*(?P<name>[A-Za-zÀ-ÿ0-9 .,_\-\[\]\(\)]{2,60})',
            re.IGNORECASE
        )
        pat3 = re.compile(r'[\[\(]?\s*(?P<name>[A-Za-zÀ-ÿ0-9 .,_\-\']{2,60})\s*[\]\)]?.{0,3}(?P<ind>' + '|'.join([p.strip(r'\b') for p in indicators]) + r')\b', re.IGNORECASE)

        for pat in (pat1, pat2, pat3):
            m = pat.search(t)
            if m:
                name = m.groupdict().get('name') or ""
                ind = m.groupdict().get('ind') or ""
                name = name.strip(" []()")
                name = self._normalize_spaces(name)
                if len(name) < 2:
                    return None
                return {'name': name, 'indicator': ind.lower()}
        if indicator_pat.search(t):
            return {'name': None, 'indicator': indicator_pat.search(t).group(0).lower()}
        return None

    async def _suggest_payment_format(self, message, detected):
        if detected.get('name'):
            suggested_cmd = f"pg {detected['name']}"
            example = f"Ex.: `pg {detected['name']}`"
            text = (f"⚠️ Parece que você informou que pagou, mas não no formato que eu entendo.\n"
                    f"Para eu confirmar automaticamente, use: `{suggested_cmd}` — {example}\n"
                    f"Se quiser, responda esse comando ou digite `pg Nome`.")
        else:
            text = ("⚠️ Detectei uma menção a pagamento, mas não encontrei um nome claro.\n"
                    "Para eu confirmar automaticamente, envie: `pg Nome` (ex.: `pg João Silva`).")

        sent = None
        try:
            sent = await AntiDetectionUtils.natural_action(message.reply, text)
        except Exception:
            pass

        if not sent:
            try:
                sent = await message.reply(text)
            except Exception:
                return

        async def _del_then_delete(msg, delay_seconds=12):
            try:
                await asyncio.sleep(delay_seconds)
                await msg.delete()
            except Exception:
                pass

        try:
            asyncio.create_task(_del_then_delete(sent, delay_seconds=12))
        except Exception:
            pass

    # ------------------------
    # Find player helper for ambiguity resolution
    # ------------------------
    def _find_player_in_fila(self, fila, nome_recebido: str):
        """
        Tenta encontrar qual jogador da fila corresponde ao nome recebido.
        Retorna:
          - nome_exato (string) se encontrou 1 correspondência clara
          - "AMBIGUO" se encontrou mais de 1 correspondência parcial
          - None se não encontrou
        """
        if not fila or not getattr(fila, "jogadores", None):
            return None
        nome_lower = (nome_recebido or "").lower().strip()
        matches = []
        for j in fila.jogadores:
            if not j:
                continue
            jclean = j.lower().strip()
            # correspondência exata
            if jclean == nome_lower:
                return j
            # correspondência parcial (sobrenome, parte do nome)
            if nome_lower in jclean or jclean in nome_lower:
                matches.append(j)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return "AMBIGUO"
        return None

    # ------------------------
    # Detect partner result messages (bot parceiro)
    # ------------------------
    def _is_partner_result_msg(self, message):
        parceiro_id = self.config.get("bote_parceiro_id")
        text = (message.content or "").lower()
        if parceiro_id and str(getattr(message.author, "id", "")) == str(parceiro_id):
            return True
        patterns = [r'partida.*encerrada', r'\d+\s*[x\-]\s*\d+', r'partida.*finalizada', r'resultado.*\d+']
        for p in patterns:
            if re.search(p, text):
                return True
        return False

    def _extract_score(self, text: str):
        score_pattern = r'(\d+)\s*[x\-]\s*(\d+)'
        m = re.search(score_pattern, text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} x {m.group(2)}"
        return None

    async def _handle_partner_result(self, message):
        try:
            placar = self._extract_score(message.content or "")
            db = self.db_session_factory()
            fila = db.query(Fila).filter_by(canal_id=str(message.channel.id)).order_by(Fila.id.desc()).first()
            if not fila:
                db.close()
                return
            fila.status = "FINALIZADA"
            fila.placar_final = placar
            fila.timestamp_finalizacao = datetime.utcnow()
            db.commit()
            janela = int(self.config.get("janela_pagamento_segundos", 120))
            await AntiDetectionUtils.natural_action(message.channel.send, f"🟢 Partida finalizada ({placar or 'placar não detectado'}). Janela de pagamento aberta por {janela//60} minuto(s).")
            asyncio.create_task(self._close_payment_window_after(fila.id, janela))
            db.close()
        except Exception as e:
            self.logger.error(f"Erro ao processar resultado parceiro: {e}")
            traceback.print_exc()

    async def _close_payment_window_after(self, fila_id, seconds):
        await asyncio.sleep(seconds)
        try:
            db = self.db_session_factory()
            fila = db.query(Fila).filter_by(id=fila_id).first()
            if fila and fila.status == "FINALIZADA":
                pagos = db.query(Pagamento).filter_by(client_id=fila.client_id, canal_id=fila.canal_id).count()
                channel = self.get_channel(int(fila.canal_id)) if fila.canal_id else None
                if pagos == 0 and channel:
                    await AntiDetectionUtils.natural_action(channel.send, "⏰ Janela de pagamento encerrada. Para registrar pagamento use: `pg Nome`.")
            db.close()
        except Exception:
            traceback.print_exc()

    # ------------------------
    # Classificação OCR: comprovante x histórico
    # ------------------------
    def _classify_image_text(self, text: str):
        t = (text or "").lower()
        pay_keywords = ["pix", "comprovante", "transferência", "transferencia", "valor recebido", "recebido", "pago", "valor"]
        history_keywords = ["placar", "resultado", "vencedor", "finalizado", "partida encerrada", "gols", "fim de partida", "histórico"]
        pay_score = sum(1 for k in pay_keywords if k in t)
        hist_score = sum(1 for k in history_keywords if k in t)
        if pay_score > hist_score:
            return "COMPROVANTE"
        if hist_score > pay_score:
            return "HISTORICO"
        return "INDETERMINADO"

    # ------------------------
    # Processamento principal de mensagens
    # ------------------------
    async def on_message(self, message):
        if message.author == self.user:
            return
        try:
            canal_nome = getattr(message.channel, "name", "DM/privado")
            conteudo = (message.content or "")[:100]
            print(f"📨 [MSG] Canal: #{canal_nome} | Autor: {message.author} | Texto: '{conteudo}' | Anexos: {len(message.attachments)}")
        except Exception as e:
            print(f"⚠️ [MSG] Erro ao logar mensagem recebida: {e}")
        asyncio.create_task(self.process_message(message))

    async def process_message(self, message):
        try:
            conteudo = (message.content or "").strip()

            # Sugerir formato 'pg' quando detectamos variações escritas
            try:
                detected = self._detect_payment_mention(conteudo)
                if detected and not conteudo.lower().startswith("pg "):
                    if len(conteudo) < 200:
                        await self._suggest_payment_format(message, detected)
            except Exception as e:
                self.logger.debug(f"Erro ao detectar menção de pagamento: {e}")

            # Prioridade: comando manual pg
            if conteudo.lower().startswith("pg "):
                print(f"✅ [CMD] Comando 'pg' detectado de {message.author}: '{conteudo[:60]}'")
                self._log_to_db("info", f"Comando 'pg' recebido de {message.author}")
                await self.cmd_pg(message)
                return

            # Comandos existentes
            if conteudo.startswith(f"{self.prefix}criar_sala"):
                print(f"✅ [CMD] Comando 'criar_sala' detectado de {message.author}")
                self._log_to_db("info", f"Comando criar_sala recebido de {message.author}")
                await self.cmd_criar_sala(message)
            elif conteudo.startswith(f"{self.prefix}verificar_pix"):
                print(f"✅ [CMD] Comando 'verificar_pix' detectado de {message.author}")
                self._log_to_db("info", f"Comando verificar_pix recebido de {message.author}")
                await self.cmd_verificar_pix(message)

            # Detectar mensagem do parceiro (resultado/histórico)
            if self._is_partner_result_msg(message):
                await self._handle_partner_result(message)
                # continue — ainda pode haver anexo a tratar

            # Verificar anexos (imagem)
            if message.attachments:
                print(f"🖼️ [IMG] Mensagem com {len(message.attachments)} anexo(s) — verificando se é comprovante...")
                await self.check_comprovante_print(message)
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {traceback.format_exc()}")
            print(f"❌ [ERRO] Falha ao processar mensagem: {e}")
            self._log_to_db("error", f"Erro no bot: {str(e)}")

    # ------------------------
    # Comandos existentes (criar sala / verificar_pix / pg)
    # ------------------------
    async def cmd_criar_sala(self, message):
        args = message.content.split()[1:]
        if len(args) < 3 or len(message.mentions) < 2:
            await AntiDetectionUtils.natural_action(
                message.reply,
                "Formato correto: `!criar_sala @jog1 @jog2 valor`"
            )
            return
        valor_text = args[-1]
        guild = message.guild
        category = None
        if self.categoria_id:
            category = guild.get_channel(int(self.categoria_id))
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
        msg_content = (f"Sala criada! {message.mentions[0].mention} e {message.mentions[1].mention}\n"
                       f"Valor da partida: R$ **{valor_text}**.\n"
                       f"Por favor, enviem o comprovante por print aqui, ou eu posso consultar via `!verificar_pix NOME VALOR` se já foi enviado.")
        await AntiDetectionUtils.natural_action(channel.send, msg_content)

        # Salvar no BD com status / tipo / valor_esperado
        try:
            db = self.db_session_factory()
            try:
                valor_float = float(str(valor_text).replace(',', '.'))
            except Exception:
                valor_float = None
            tipo_padrao = self.config.get("tipo_partida_padrao", "NORMAL")
            nova_fila = Fila(
                client_id=self.db_client_id,
                canal_id=str(channel.id),
                jogadores=[m.name for m in message.mentions],
                status="AGUARDANDO_PAGAMENTO",
                valor_esperado=valor_float,
                tipo_partida=tipo_padrao
            )
            db.add(nova_fila)
            db.commit()
            db.close()
            self._log_to_db("success", f"Sala '{room_name}' criada com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao salvar BD fila: {e}")

    async def cmd_verificar_pix(self, message):
        print(f"🔍 [VERIFICAR_PIX] Comando recebido: '{message.content[:100]}'")
        if not self.email or not self.email_senha:
            print(f"⚠️ [VERIFICAR_PIX] E-mail não configurado para este cliente. Abortando.")
            await AntiDetectionUtils.natural_action(message.reply, "E-mail não configurado.")
            return
        partes = message.content.split(' ', 1)
        if len(partes) < 2:
            print(f"⚠️ [VERIFICAR_PIX] Formato inválido (faltam argumentos).")
            await AntiDetectionUtils.natural_action(message.reply, "Formato: !verificar_pix Nome valor")
            return
        argumentos = partes[1].split()
        if len(argumentos) < 2:
            print(f"⚠️ [VERIFICAR_PIX] Faltam nome e/ou valor. Abortando.")
            return
        valor = argumentos[-1]
        nome = " ".join(argumentos[:-1])
        print(f"✅ [VERIFICAR_PIX] Nome extraído: '{nome}' | Valor extraído: '{valor}'")
        await AntiDetectionUtils.natural_action(message.reply, f"Verificando e-mail por Pix de '{nome}' no valor de R${valor}...")
        def run_sync_gmail():
            return GmailService.check_payment_email(self.email, self.email_senha, nome, valor)
        loop = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(None, run_sync_gmail)
        print(f"✅ [VERIFICAR_PIX] Busca no Gmail concluída. Encontrou pagamento? {'SIM' if resultado else 'NÃO'}")
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

    async def cmd_pg(self, message):
        print(f"🔍 [PG] Comando 'pg' recebido: '{message.content[:100]}'")
        if not self.email or not self.email_senha:
            print(f"⚠️ [PG] E-mail não configurado para este cliente. Abortando.")
            await AntiDetectionUtils.natural_action(
                message.reply,
                "⚠️ E-mail não configurado. Avise o administrador para configurar o Gmail."
            )
            return
        resto = message.content.strip()[3:].strip()
        argumentos = resto.split()
        if not argumentos:
            print(f"⚠️ [PG] Nenhum nome informado após 'pg'. Abortando.")
            await AntiDetectionUtils.natural_action(
                message.reply,
                "📝 Use assim: `pg Nome do Jogador`\nExemplo: `pg Juan`"
            )
            return
        valor = None
        ultimo = argumentos[-1].replace("R$", "").replace("r$", "").replace(",", ".").strip()
        if len(argumentos) >= 2:
            try:
                float(ultimo)
                valor = argumentos[-1]
                nome = " ".join(argumentos[:-1])
            except ValueError:
                nome = " ".join(argumentos)
        else:
            nome = " ".join(argumentos)
        valor_txt = f" no valor de R${valor}" if valor else ""
        print(f"✅ [PG] Nome extraído: '{nome}' | Valor: '{valor if valor else '(qualquer)'}'")
        await AntiDetectionUtils.natural_action(
            message.reply,
            f"🔎 Procurando no Gmail um Pix de **{nome}**{valor_txt}... Um instante! ⏳"
        )
        def run_sync_gmail():
            return GmailService.check_payment_email(self.email, self.email_senha, nome, valor)
        loop = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(None, run_sync_gmail)
        print(f"✅ [PG] Busca no Gmail concluída. Encontrou pagamento? {'SIM' if resultado else 'NÃO'}")
        if resultado:
            await AntiDetectionUtils.natural_action(
                message.channel.send,
                f"✅ **Pagamento Confirmado via E-mail (Gmail)!**\n"
                f"👤 Nome: {resultado['nome']}\n"
                f"💰 Valor: R$ {resultado['valor']}\n"
                f"🕒 Data: {resultado['data']}"
            )
            self._salvar_pagamento(
                resultado['nome'],
                resultado['valor'] if valor else "0",
                str(message.channel.id)
            )
        else:
            await AntiDetectionUtils.natural_action(
                message.channel.send,
                f"❌ Não encontrei nenhum Pix de **{nome}**{valor_txt} nos e-mails de hoje.\n"
                f"Confira se o nome está correto e se o comprovante já chegou no Gmail."
            )

    # ------------------------
    # OCR / comprovante handling
    # ------------------------
    async def check_comprovante_print(self, message):
        try:
            canal_nome = getattr(message.channel, "name", "DM/privado")
            print(f"🔍 [COMPROVANTE] Iniciando análise no canal: #{canal_nome}")
            if not canal_nome.startswith("fila-"):
                print(f"⏭️ [COMPROVANTE] Canal '#{canal_nome}' NÃO começa com 'fila-'. Ignorando imagem.")
                return
            image_url = message.attachments[0].url
            print(f"🔗 [COMPROVANTE] URL da imagem: {image_url[:120]}")
            if not image_url.lower().split('?')[0].endswith(('.png', '.jpg', '.jpeg', '.webp')):
                print(f"⏭️ [COMPROVANTE] O anexo NÃO é uma imagem suportada. Ignorando.")
                return
            if not OCRService.tesseract_disponivel():
                print("⚠️ [COMPROVANTE] Tesseract não disponível, usando modo texto apenas.")
                self.logger.warning("⚠️ Tesseract não disponível, usando modo texto apenas")
                self._log_to_db("warning", "Tesseract (OCR) indisponível — leitura de imagem desativada.")
                await AntiDetectionUtils.natural_action(
                    message.reply,
                    "⚠️ Não consigo ler imagens neste servidor (OCR indisponível).\n"
                    "✅ Para confirmar o pagamento, digite: `pg Nome do Jogador`\n"
                    "Exemplo: `pg Juan` — eu busco o Pix direto no Gmail! 🎉"
                )
                return
            await AntiDetectionUtils.natural_action(message.reply, "Analisando comprovante...")
            text = await OCRService.extract_text_from_image_url(image_url)
            print(f"✅ [COMPROVANTE] OCR concluído. Caracteres extraídos: {len(text) if text else 0}")
            if not text:
                await AntiDetectionUtils.natural_action(message.channel.send, "Não consegui ler o comprovante.")
                return

            classification = self._classify_image_text(text)
            print(f"🔍 [COMPROVANTE] Classificação OCR: {classification}")
            # Se histórico -> tratar como resultado/parceiro
            if classification == "HISTORICO":
                # atualiza fila como finalizada e abre janela
                await self._handle_partner_result(message)
                return

            # Se comprovante ou indeterminado, tentar extrair nome/valor do OCR
            detected = self._detect_payment_mention(text)
            if detected and detected.get("name"):
                # tenta salvar com nome detectado
                nome_detectado = detected.get("name")
                # tenta extrair valor do texto se houver
                valor_match = re.search(r'(\d+[.,]\d{1,2})', text)
                valor_text = valor_match.group(1) if valor_match else "0"
                await AntiDetectionUtils.natural_action(message.channel.send, "✅ Comprovante reconhecido pelo sistema (OCR)!")
                self._log_to_db("success", f"Comprovante reconhecido no canal {canal_nome}")
                # Tenta salvar pagamento (vai checar ambiguidades)
                self._salvar_pagamento(nome_detectado, valor_text, str(message.channel.id))
            else:
                # Não conseguimos extrair nome: pedir para enviar comando pg
                await AntiDetectionUtils.natural_action(
                    message.channel.send,
                    "⚠️ Não reconheci claramente o nome no comprovante. Por favor, digite `pg Nome Sobrenome` (ex.: `pg João Silva`) para eu confirmar."
                )
        except Exception as e:
            self.logger.error(f"❌ Erro em check_comprovante_print: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self._log_to_db("error", f"Erro ao analisar comprovante: {str(e)}")

    # ------------------------
    # Salvar pagamento com desambiguação
    # ------------------------
    def _salvar_pagamento(self, nome, valor, canal_id):
        try:
            db = self.db_session_factory()
            # procurar fila ativa neste canal
            fila = db.query(Fila).filter_by(canal_id=str(canal_id)).order_by(Fila.id.desc()).first()
            jogador_associado = None
            if fila:
                match = self._find_player_in_fila(fila, nome)
                if match == "AMBIGUO":
                    # pedir nome + sobrenome ao autor (não salva)
                    channel = self.get_channel(int(canal_id))
                    if channel:
                        asyncio.create_task(AntiDetectionUtils.natural_action(channel.send, "⚠️ Encontrei mais de um jogador com esse nome. Por favor envie o `pg Nome Sobrenome` para eu registrar corretamente."))
                    db.close()
                    return
                elif match is None:
                    # não encontrou — pede nome completo
                    channel = self.get_channel(int(canal_id))
                    if channel:
                        asyncio.create_task(AntiDetectionUtils.natural_action(channel.send, "⚠️ Não consegui identificar qual jogador é. Por favor envie `pg Nome Sobrenome` (ex.: `pg João Silva`)."))
                    db.close()
                    return
                else:
                    jogador_associado = match

            # normalizar valor
            if isinstance(valor, str):
                valor_s = valor.replace(',', '.').strip()
            else:
                valor_s = str(valor)
            try:
                valor_float = float(valor_s)
            except Exception:
                valor_float = 0.0

            pg = Pagamento(
                client_id=self.db_client_id,
                nome_pagador=jogador_associado or nome,
                valor=float(valor_float) if valor_float else 0.0,
                horario=datetime.utcnow().isoformat(),
                canal_id=canal_id
            )
            db.add(pg)
            # se teve fila e jogador, pode atualizar status se necessário
            if fila:
                # marcar registro de que pelo menos um pagamento existe
                fila.status = "PAGA" if fila.status in ("AGUARDANDO_PAGAMENTO", "FINALIZADA") else fila.status
            db.commit()
            db.close()
            self._log_to_db("success", f"Pagamento salvo: {pg.nome_pagador} R${pg.valor}")
        except Exception as e:
            self.logger.error(f"Erro salvar pag DB: {e}")
            traceback.print_exc()
