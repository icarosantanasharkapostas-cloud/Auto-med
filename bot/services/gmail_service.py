import re
import imap_tools
from imap_tools import MailBox, AND
import logging
from typing import Optional, Dict, Any

class GmailService:
    @staticmethod
    def check_payment_email(email_address: str, app_password: str, player_name: str, value: str) -> Optional[Dict[str, Any]]:
        """
        Verifica a caixa de entrada do Gmail buscando um comprovante de pagamento Pix correspondente
        ao nome do jogador e valor no último minuto/poucas horas.
        """
        logger = logging.getLogger(f"Gmail-{email_address}")
        logger.info(f"Procurando pagamento de {player_name} no valor de R$ {value}")
        
        try:
            # Substituir por 'imap.gmail.com' para contas google
            with MailBox('imap.gmail.com').login(email_address, app_password, 'INBOX') as mailbox:
                # Buscar emails recebidos hoje com assunto PIX
                for msg in mailbox.fetch(AND(date_gte=imap_tools.datetime.date.today())):
                    text = msg.text or msg.html
                    
                    if not text:
                        continue
                        
                    # Aqui usamos um Regex genérico, adapte para o formato do seu banco
                    # Procurando aproximação do nome (pode ser Case Insensitive) e Valor
                    # Normalmente bancos enviam "Você recebeu um Pix de NOME no valor de R$ 10,00"
                    
                    if player_name.lower() in text.lower() and value.replace(',', '.') in text:
                        logger.info("Comprovante encontrado no email.")
                        return {
                            "nome": player_name,
                            "valor": value,
                            "data": msg.date.strftime("%d/%m/%Y %H:%M:%S"),
                            "assunto": msg.subject
                        }
            
            logger.info("Nenhum pagamento correspondente encontrado no momento.")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao acessar email: {str(e)}")
            return None
