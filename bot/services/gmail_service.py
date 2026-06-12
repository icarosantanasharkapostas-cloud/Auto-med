import re
import imap_tools
from imap_tools import MailBox, AND
import logging
from typing import Optional, Dict, Any

class GmailService:
    @staticmethod
    def check_payment_email(email_address: str, app_password: str, player_name: str, value: str = None) -> Optional[Dict[str, Any]]:
        """
        Verifica a caixa de entrada do Gmail buscando um comprovante de pagamento Pix correspondente
        ao nome do jogador (e, opcionalmente, ao valor) recebido hoje.

        💡 O parâmetro 'value' é OPCIONAL:
           - Se você informar o valor, o bot confere nome E valor.
           - Se você NÃO informar (None ou vazio), o bot procura só pelo NOME.
             Isso é usado pelo comando 'pg Nome', em que o usuário não precisa
             digitar o valor — muito mais simples! 🎉
        """
        logger = logging.getLogger(f"Gmail-{email_address}")
        valor_str = f"R$ {value}" if value else "(qualquer valor)"
        logger.info(f"Procurando pagamento de {player_name} no valor de {valor_str}")
        print(f"🔍 [GMAIL] Buscando no Gmail para: '{player_name}' | valor: {valor_str}")

        try:
            # Etapa 1: Conectar no Gmail via IMAP
            print(f"🔍 [GMAIL] Tentando conectar no Gmail ({email_address})...")
            with MailBox('imap.gmail.com').login(email_address, app_password, 'INBOX') as mailbox:
                print(f"✅ [GMAIL] Conectado com sucesso! Buscando e-mails de hoje...")

                # Etapa 2: Buscar emails recebidos hoje
                mensagens = list(mailbox.fetch(AND(date_gte=imap_tools.datetime.date.today())))
                print(f"✅ [GMAIL] Encontrou {len(mensagens)} e-mail(s) de hoje para analisar.")

                # Etapa 3: Analisar cada e-mail
                for i, msg in enumerate(mensagens, start=1):
                    print(f"🔍 [GMAIL] Processando e-mail {i}/{len(mensagens)} | Assunto: '{msg.subject[:60]}'")
                    text = msg.text or msg.html

                    if not text:
                        print(f"⏭️ [GMAIL] E-mail {i} sem conteúdo de texto. Pulando.")
                        continue

                    # Procurando aproximação do nome (Case Insensitive) e Valor.
                    # Normalmente bancos enviam "Você recebeu um Pix de NOME no valor de R$ 10,00"
                    nome_bate = player_name.lower() in text.lower()
                    # Se o valor não foi informado, consideramos como "bate" (busca só por nome).
                    if value:
                        valor_bate = value.replace(',', '.') in text or value in text
                    else:
                        valor_bate = True
                    print(f"🔍 [GMAIL] E-mail {i}: nome encontrado? {nome_bate} | valor encontrado? {valor_bate}")

                    if nome_bate and valor_bate:
                        logger.info("Comprovante encontrado no email.")
                        print(f"✅ [GMAIL] PAGAMENTO ENCONTRADO no e-mail {i}! 🎉")
                        return {
                            "nome": player_name,
                            "valor": value if value else "(não informado)",
                            "data": msg.date.strftime("%d/%m/%Y %H:%M:%S"),
                            "assunto": msg.subject
                        }

            logger.info("Nenhum pagamento correspondente encontrado no momento.")
            print(f"❌ [GMAIL] Nenhum pagamento de '{player_name}' ({valor_str}) encontrado nos e-mails de hoje.")
            return None

        except Exception as e:
            logger.error(f"Erro ao acessar email: {str(e)}")
            print(f"❌ [GMAIL] ERRO ao acessar o e-mail: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
