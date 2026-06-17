import sys
import os
# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import discord
import asyncio
import logging
import re
# 🩹 Aplica a correção do bug do discord.py-self LOGO no início,
# antes de qualquer bot ser criado. Isso resolve de forma definitiva o erro
# "'NoneType' object is not iterable" que acontecia ao conectar no Discord.
from bot.utils.discord_patch import aplicar_patch_discord
aplicar_patch_discord()
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
        self.client_name = client_data.get("nome") or "SemNome"
        # Configurações do cliente
        # IMPORTANTE: se "config_json" vier None do banco de dados,
        # o .get("config_json", {}) ainda retorna None (pois a chave existe).
        # Por isso usamos "or {}" para garantir que SEMPRE seja um dicionário. 🛡️
        self.config = client_data.get("config_json") or {}
        if not isinstance(self.config, dict):
            # Se por algum motivo não for um dicionário, forçamos um dicionário vazio
            self.config = {}
        self.email = client_data.get("email")
        self.email_senha = client_data.get("senha_email")
        self.logger = logging.getLogger(f"Bot-{self.client_name}")
        self.db_session_factory = db_session_factory
        # Limite de taxa REDUZIDO para no máximo 5 ações de ENVIO por minuto.
        # Isso deixa o bot mais "humano" e evita ser detectado pelo Discord. 🐢
        self.rate_limiter = RateLimiter(actions_per_minute=5)
        # Configurações com valores padrão (nunca ficam None) ✅
        self.prefix = self.config.get("prefix") or "!"
        self.categoria_id = self.config.get("categoria_id") # Categoria onde as salas são criadas
        self.cargo_mediador_id = self.config.get("cargo_mediador_id")
        # Valores padrão extras para evitar erros de "NoneType" 🛡️
        self.palavras_chave_canal = self.config.get("palavras_chave_canal") or ["fila", "filas", "partidas", "pagar"]
        self.valor_fila_padrao = self.config.get("valor_fila_padrao") or 5.50
        self.nome_recebedor_pix = self.config.get("nome_recebedor_pix") or ""
        # 🐞 LOGS DE DEPURAÇÃO: mostram o valor de cada configuração ao iniciar
        # Isso ajuda a descobrir QUAL variável está vindo vazia (None)
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

    async def start(self, token: str):
        # Função responsável por LIGAR o bot e conectar ao Discord 🔌
        # Aqui validamos tudo ANTES de chamar o Discord, para evitar o erro
        # "'NoneType' object is not iterable".
        # 1️⃣ Validação do TOKEN (a causa mais comum de erros ao iniciar) 🔑
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
        # 2️⃣ Tentativa de conexão com RETENTATIVAS (retry) 🔁
        # O erro "'NoneType' object is not iterable" muitas vezes acontece porque
        # a biblioteca discord.py-self busca informações em sites externos
        # (build number / propriedades do navegador) e essa busca pode FALHAR
        # de forma temporária por causa da internet. Por isso tentamos algumas vezes.
        max_tentativas = 3
        for tentativa in range(1, max_tentativas + 1):
            try:
                print(f"🔄 [DEBUG] Tentativa {tentativa} de {max_tentativas} de conexão...")
                await super().start(token)
                # Se chegou aqui sem erro, deu tudo certo ✅
                return
            except TypeError as e:
                # Erro típico de "NoneType is not iterable" (dado None vindo de site externo)
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
                # Qualquer outro erro (token inválido, sem internet, etc.)
                erro_final = f"❌ Erro ao iniciar o bot '{self.client_name}': {type(e).__name__}: {e}"
                self.logger.error(erro_final)
                self._log_to_db("error", erro_final)
                print(erro_final)
                traceback.print_exc()
                # Esses erros normalmente não se resolvem tentando de novo, então paramos
                return

    async def on_ready(self):
        self.logger.info(f"Bot {self.client_name} logado como {self.user}!")
        self._log_to_db("info", f"Bot {self.client_name} online como {self.user}")
        # 🟢 Log bem visível confirmando que o bot está pronto para receber mensagens
        print("=" * 50)
        print(f"🟢 BOT ONLINE: {self.user} (cliente: {self.client_name})")
        print(f"👀 Prefixo dos comandos: '{self.prefix}'")
        print(f"📡 Servidores conectados: {len(self.guilds)}")
        print("✅ Aguardando mensagens... (vou logar cada uma que chegar)")
        print("=" * 50)

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
        # 📨 ESTE EVENTO É CHAMADO PARA CADA MENSAGEM QUE O BOT VÊ.
        # OBS IMPORTANTE: como este é um "self-bot" (conta de usuário), ele recebe
        # TODAS as mensagens automaticamente. A biblioteca discord.py-self NÃO usa
        # "intents" (diferente de bots normais). Por isso o conteúdo das mensagens
        # (message.content) sempre vem preenchido, sem precisar configurar nada. ✅
        # Ignorar mensagens do próprio bot (senão ele responde a si mesmo) 🔁
        if message.author == self.user:
            return
        # 🐞 LOG DETALHADO: mostra cada mensagem recebida (ajuda muito a debugar!)
        try:
            canal_nome = getattr(message.channel, "name", "DM/privado")
            conteudo = (message.content or "")[:100] # mostra só os 100 primeiros caracteres
            print(f"📨 [MSG] Canal: #{canal_nome} | Autor: {message.author} | Texto: '{conteudo}' | Anexos: {len(message.attachments)}")
        except Exception as e:
            print(f"⚠️ [MSG] Erro ao logar mensagem recebida: {e}")
        # Processa a mensagem em segundo plano (não trava o bot) ⚙️
        asyncio.create_task(self.process_message(message))

    def _normalize_spaces(self, s: str) -> str:
        return re.sub(r'\s+', ' ', s).strip()

    def _detect_payment_mention(self, text: str):
        """
        Detecta se o texto contém alguma menção de pagamento em vários formatos.
        Retorna None se não detectar nada ou um dict com {'name': str, 'indicator': str}
        Exemplo de detecções:
          - "Joao PG"
          - "joão pago"
          - "[Maria] pg"
          - "Nome pgo" (typo comum)
        """
        if not text:
            return None
        t = text.strip()

        # Variantes aceitáveis para indicar pagamento (inclui typos comuns)
        indicators = [
            r'\bpg\b', r'\bp\.g\b', r'\bp g\b', r'\bpgo\b', r'\bpago\b',
            r'\bpagou\b', r'\bpaguei\b', r'\bpag\b', r'\bpg\.\b'
        ]
        indicator_pat = re.compile('|'.join(indicators), re.IGNORECASE)

        # Padrões que tentam capturar "NOME <INDICADOR>" ou "<INDICADOR> NOME"
        # 1) Nome seguido de indicador: "Joao PG", "João pago", "[Maria] pg"
        pat1 = re.compile(
            r'^(?P<name>[A-Za-zÀ-ÿ0-9 .,_\-\[\]\(\)]{2,60})\s*(?P<ind>' + '|'.join([p.strip(r'\b') for p in indicators]) + r')\b',
            re.IGNORECASE
        )
        # 2) Indicador seguido de nome: "pg João", "pago: Maria"
        pat2 = re.compile(
            r'^(?P<ind>' + '|'.join([p.strip(r'\b') for p in indicators]) + r')[:\s\-]*\s*(?P<name>[A-Za-zÀ-ÿ0-9 .,_\-\[\]\(\)]{2,60})',
            re.IGNORECASE
        )
        # 3) Nome entre colchetes seguido de indicador: "[Maria] pg"
        pat3 = re.compile(r'[\[\(]?\s*(?P<name>[A-Za-zÀ-ÿ0-9 .,_\-\']{2,60})\s*[\]\)]?.{0,3}(?P<ind>' + '|'.join([p.strip(r'\b') for p in indicators]) + r')\b', re.IGNORECASE)

        for pat in (pat1, pat2, pat3):
            m = pat.search(t)
            if m:
                name = m.groupdict().get('name') or ""
                ind = m.groupdict().get('ind') or ""
                name = name.strip(" []()")
                name = self._normalize_spaces(name)
                # descartamos matches que são muito curtos ou números isolados
                if len(name) < 2:
                    return None
                return {'name': name, 'indicator': ind.lower()}
        # 4) Se só existe um indicador isolado (ex: "pago") sem nome, não sugerimos comando automático
        if indicator_pat.search(t):
            return {'name': None, 'indicator': indicator_pat.search(t).group(0).lower()}
        return None

    async def _suggest_payment_format(self, message, detected):
        """
        Envia uma sugestão discreta e amigável para o usuário sobre o formato correto.
        A mensagem é apagada automaticamente após 'delay_seconds'.
        """
        # Construir sugestão
        if detected.get('name'):
            suggested_cmd = f"pg {detected['name']}"
            example = f"Ex.: `pg {detected['name']}`"
            text = (f"⚠️ Parece que você informou que pagou, mas não no formato que eu entendo.\n"
                    f"Para eu confirmar automaticamente, use: `{suggested_cmd}` — {example}\n"
                    f"Se quiser, responda esse comando ou digite `pg Nome`.")
        else:
            text = ("⚠️ Detectei uma menção a pagamento, mas não encontrei um nome claro.\n"
                    "Para eu confirmar automaticamente, envie: `pg Nome` (ex.: `pg João Silva`).")

        # Envia mensagem de forma discreta com natural_action (anti-detecção)
        try:
            sent = await AntiDetectionUtils.natural_action(message.reply, text)
        except Exception:
            # fallback direto caso natural_action falhe
            sent = await message.reply(text)

        # Apagar a sugestão após alguns segundos (deixar discreta). Ajuste se necessário.
        async def _del_then_delete(msg, delay_seconds=10):
            try:
                await asyncio.sleep(delay_seconds)
                await msg.delete()
            except Exception:
                pass

        # Criar task para apagar a mensagem
        try:
            asyncio.create_task(_del_then_delete(sent, delay_seconds=12))
        except Exception:
            pass

    async def process_message(self, message):
        try:
            # ❌ IMPORTANTE: NÃO chamamos rate_limiter aqui!
            # Antes, o bot aplicava limite de taxa em CADA mensagem RECEBIDA.
            # Em canais movimentados isso criava uma fila gigante de esperas
            # ("Rate limit atingido. Esperando Xs") e o bot ficava travado,
            # sem responder aos comandos. ⛔
            # Agora o limite de taxa só vale para as ações de ENVIO (responder),
            # que é o que realmente importa para não ser detectado. ✅
            conteudo = (message.content or "").strip()
            
            # Sugestão automática de formato 'pg' quando detectamos variações
            try:
                detected = self._detect_payment_mention(conteudo)
                # Só sugerimos se não for o comando 'pg ' já correto e se detectamos um nome ou indicador relevante
                if detected and not conteudo.lower().startswith("pg "):
                    # Evitar sugerir para mensagens muito longas (provavelmente não é um comprovante)
                    if len(conteudo) < 200:
                        await self._suggest_payment_format(message, detected)
                        # Não retornamos; permitimos que outras rotinas continuem (ex.: OCR se houver anexo)
            except Exception as e:
                self.logger.debug(f"Erro ao detectar menção de pagamento: {e}")

            # 💸 PRIORIDADE MÁXIMA: comando manual "pg Nome" (sem precisar de OCR!)
            # Se alguém escrever, por exemplo, "pg Juan" (com ou sem imagem anexada),
            # o bot busca o pagamento DIRETO no Gmail pelo nome, ignorando a imagem.
            # Isso é mais confiável do que ler o print, e funciona mesmo SEM o Tesseract. ✅
            if conteudo.lower().startswith("pg "):
                print(f"✅ [CMD] Comando 'pg' detectado de {message.author}: '{conteudo[:60]}'")
                self._log_to_db("info", f"Comando 'pg' recebido de {message.author}")
                await self.cmd_pg(message)
                return # Não processa OCR da imagem quando o comando 'pg' é usado.

            # 🔎 Detecção de comandos
            if conteudo.startswith(f"{self.prefix}criar_sala"):
                print(f"✅ [CMD] Comando 'criar_sala' detectado de {message.author}")
                self._log_to_db("info", f"Comando criar_sala recebido de {message.author}")
                await self.cmd_criar_sala(message)
            elif conteudo.startswith(f"{self.prefix}verificar_pix"):
                print(f"✅ [CMD] Comando 'verificar_pix' detectado de {message.author}")
                self._log_to_db("info", f"Comando verificar_pix recebido de {message.author}")
                await self.cmd_verificar_pix(message)

            # 🖼️ Verificar se é um comprovante em imagem (print de Pix)
            if message.attachments:
                print(f"🖼️ [IMG] Mensagem com {len(message.attachments)} anexo(s) — verificando se é comprovante...")
                await self.check_comprovante_print(message)
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {traceback.format_exc()}")
            print(f"❌ [ERRO] Falha ao processar mensagem: {e}")
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
        # Tenta extrair o último termo como valor, e os anteriores como nome
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
        print(f"🔍 [VERIFICAR_PIX] Iniciando busca no Gmail (em segundo plano)...")
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
        """Comando manual: "pg Nome do Jogador" (valor é opcional).
        👉 Exemplos de uso:
        - "pg Juan" -> busca no Gmail um Pix do "Juan" (qualquer valor)
        - "pg Juan Silva" -> busca por "Juan Silva"
        - "pg Juan 10,00" -> busca por "Juan" no valor de R$ 10,00
        O bot procura o pagamento DIRETO no Gmail, sem precisar ler nenhuma
        imagem (sem OCR/Tesseract). É a forma mais confiável de confirmar! ✅
        """
        print(f"🔍 [PG] Comando 'pg' recebido: '{message.content[:100]}'")
        if not self.email or not self.email_senha:
            print(f"⚠️ [PG] E-mail não configurado para este cliente. Abortando.")
            await AntiDetectionUtils.natural_action(
                message.reply,
                "⚠️ E-mail não configurado. Avise o administrador para configurar o Gmail."
            )
            return
        # Remove o prefixo "pg " (3 primeiros caracteres) e separa os termos.
        resto = message.content.strip()[3:].strip()
        argumentos = resto.split()
        if not argumentos:
            print(f"⚠️ [PG] Nenhum nome informado após 'pg'. Abortando.")
            await AntiDetectionUtils.natural_action(
                message.reply,
                "📝 Use assim: `pg Nome do Jogador`\nExemplo: `pg Juan`"
            )
            return
        # Tenta descobrir se o último termo é um VALOR (ex: 10, 10,00, 10.50).
        # Se for, o nome é tudo menos o último termo. Senão, valor fica vazio.
        valor = None
        ultimo = argumentos[-1].replace("R$", "").replace("r$", "").replace(",", ".").strip()
        if len(argumentos) >= 2:
            try:
                float(ultimo)
                valor = argumentos[-1] # mantém o formato original (ex: "10,00")
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
        print(f"🔍 [PG] Iniciando busca no Gmail (em segundo plano)...")
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

    async def check_comprovante_print(self, message):
        """Verifica se a imagem é um comprovante usando OCR.
        🔍 ESTE MÉTODO TEM LOGS DETALHADOS EM CADA ETAPA para descobrir
        exatamente onde o processamento trava ou para."""
        try:
            canal_nome = getattr(message.channel, "name", "DM/privado")
            print(f"🔍 [COMPROVANTE] Iniciando análise no canal: #{canal_nome}")
            # Etapa 1: Verificar se está numa sala "fila-*"
            if not canal_nome.startswith("fila-"):
                print(f"⏭️ [COMPROVANTE] Canal '#{canal_nome}' NÃO começa com 'fila-'. Ignorando imagem. "
                      f"(Comprovantes só são analisados em salas que começam com 'fila-'")
                return
            print(f"✅ [COMPROVANTE] Canal válido (começa com 'fila-').")
            # Etapa 2: Verificar a extensão da imagem
            image_url = message.attachments[0].url
            print(f"🔗 [COMPROVANTE] URL da imagem: {image_url[:120]}")
            if not image_url.lower().split('?')[0].endswith(('.png', '.jpg', '.jpeg', '.webp')):
                print(f"⏭️ [COMPROVANTE] O anexo NÃO é uma imagem suportada (.png/.jpg/.jpeg/.webp). Ignorando.")
                return
            print(f"✅ [COMPROVANTE] Anexo é uma imagem suportada.")
            # Etapa 2.5: Verificar se o Tesseract (OCR) está disponível neste servidor.
            # Em ambientes como a Square Cloud, muitas vezes NÃO dá para instalar o
            # programa 'tesseract'. Nesse caso, avisamos o usuário para usar "pg Nome". ✅
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
            # Etapa 3: Avisar que está analisando
            print(f"💬 [COMPROVANTE] Enviando mensagem 'Analisando comprovante...'")
            await AntiDetectionUtils.natural_action(
                message.reply,
                "Analisando comprovante..."
            )
            print(f"✅ [COMPROVANTE] Mensagem 'Analisando...' enviada.")
            # Etapa 4: Executar OCR (lê o texto da imagem)
            print(f"🔍 [COMPROVANTE] Iniciando OCR (leitura do texto da imagem)...")
            text = await OCRService.extract_text_from_image_url(image_url)
            print(f"✅ [COMPROVANTE] OCR concluído. Caracteres extraídos: {len(text) if text else 0}")
            if text:
                print(f"📄 [COMPROVANTE] Prévia do texto lido (200 primeiros chars): '{text[:200]}'")
            if not text:
                print(f"⚠️ [COMPROVANTE] OCR não retornou texto. Avisando o usuário.")
                await AntiDetectionUtils.natural_action(message.channel.send, "Não consegui ler o comprovante.")
                return
            # Etapa 5: Verificar palavras-chave de comprovante
            texto_min = text.lower()
            print(f"🔍 [COMPROVANTE] Procurando palavras-chave (comprovante/pix/transferência) no texto...")
            if "comprovante" in texto_min or "pix" in texto_min or "transferência" in texto_min or "transferencia" in texto_min:
                print(f"✅ [COMPROVANTE] Palavra-chave ENCONTRADA! Aprovando comprovante.")
                await AntiDetectionUtils.natural_action(
                    message.reply,
                    "✅ Comprovante reconhecido pelo sistema (OCR)!"
                )
                self._log_to_db("success", f"Comprovante reconhecido no canal {canal_nome}")
                print(f"💾 [COMPROVANTE] Salvando pagamento no banco de dados...")
                self._salvar_pagamento(message.author.name, "0", str(message.channel.id)) # Pode refinar para extrair valor depois
                print(f"✅ [COMPROVANTE] Pagamento salvo. Processo concluído com sucesso! 🎉")
            else:
                print(f"❌ [COMPROVANTE] Nenhuma palavra-chave de comprovante encontrada no texto lido.")
                await AntiDetectionUtils.natural_action(
                    message.channel.send,
                    "⚠️ Não reconheci este print como um comprovante de Pix."
                )
        except Exception as e:
            # Captura QUALQUER erro inesperado e mostra o traceback completo
            self.logger.error(f"❌ Erro em check_comprovante_print: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"❌ [COMPROVANTE] ERRO inesperado: {str(e)}")
            print(traceback.format_exc())
            self._log_to_db("error", f"Erro ao analisar comprovante: {str(e)}")

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
