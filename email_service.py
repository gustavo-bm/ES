from db import (
    get_notificacoes_pendentes, marcar_notificacao_enviada,
    get_agendamentos_proximas_24h, criar_notificacao_lembrete
)
from email_utils import enviar_email

def enviar_notificacoes():
    try:
        notificacoes = get_notificacoes_pendentes()
        if not notificacoes:
            print("Nenhuma notificação pendente")
            return
            
        for notif in notificacoes:
            try:
                if not notif.get('email'):
                    print(f"E-mail não encontrado para notificação {notif.get('id')}")
                    continue
                    
                # Determina o assunto com base no conteúdo da mensagem
                assunto = 'Lembrete de Exame' if 'LEMBRETE' in notif['mensagem'] else 'Confirmação de Agendamento'
                
                if enviar_email(notif['email'], assunto, notif['mensagem']):
                    marcar_notificacao_enviada(notif['id'])
                
            except Exception as e:
                print(f"Erro ao processar notificação para {notif.get('email')}: {e}")
                
    except Exception as e:
        print(f"Erro geral no processo de envio de notificações: {e}")

def verificar_agendamentos_24h():
    try:
        agendamentos = get_agendamentos_proximas_24h()
        if not agendamentos:
            return
            
        for agend in agendamentos:
            try:
                if not agend.get('email'):
                    print(f"E-mail não encontrado para agendamento {agend.get('id')}")
                    continue
                    
                criar_notificacao_lembrete(agend)
                print(f"Lembrete criado com sucesso para {agend['email']}")
                
            except Exception as e:
                print(f"Erro ao criar lembrete para {agend.get('email')}: {e}")
                
    except Exception as e:
        print(f"Erro geral no processo de verificação de agendamentos: {e}") 