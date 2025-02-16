from flask import Flask
import yagmail
import smtplib
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv
from db import (
    get_notificacoes_pendentes, marcar_notificacao_enviada,
    get_agendamentos_proximas_24h, criar_notificacao_lembrete
)
from routes import init_app

load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave_secreta_do_app'

def get_yagmail_instance():
    try:
        email = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASSWORD')
        if not email or not password:
            print("Erro: Credenciais de e-mail não configuradas")
            return None
            
        print(f"Tentando conectar com o e-mail: {email}")
        print("Configurações SMTP:")
        print("- Host: smtp.gmail.com")
        print("- Porta: 587")
        print("- TLS: Ativado")
        print("- SSL: Desativado")
            
        return yagmail.SMTP(
            user=email,
            password=password,
            host='smtp.gmail.com',
            port=587,
            smtp_starttls=True,
            smtp_ssl=False
        )
    except smtplib.SMTPAuthenticationError as e:
        print(f"Erro de autenticação detalhado: {str(e)}")
        print("Por favor, verifique:")
        print("1. Se a verificação em duas etapas está ativada")
        print("2. Se a senha de app foi gerada corretamente")
        print("3. Se a senha foi copiada sem espaços extras")
        return None
    except Exception as e:
        print(f"Erro ao criar instância do yagmail: {e}")
        return None

def enviar_notificacoes():
    try:
        notificacoes = get_notificacoes_pendentes()
        if not notificacoes:
            print("Nenhuma notificação pendente")
            return
            
        yag = get_yagmail_instance()
        if not yag:
            print("Não foi possível inicializar o serviço de e-mail")
            return
            
        for notif in notificacoes:
            try:
                if not notif.get('email'):
                    print(f"E-mail não encontrado para notificação {notif.get('id')}")
                    continue
                    
                # Determina o assunto com base no conteúdo da mensagem
                assunto = 'Lembrete de Exame' if 'LEMBRETE' in notif['mensagem'] else 'Confirmação de Agendamento'
                
                conteudo = [
                    f'''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Sistema de Agendamento de Exames</h2>
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                            {notif['mensagem'].replace(chr(10), '<br>')}
                        </div>
                        <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
                            Esta é uma mensagem automática, por favor não responda.
                        </p>
                    </div>
                    '''
                ]
                
                yag.send(
                    to=notif['email'],
                    subject=assunto,
                    contents=conteudo
                )
                marcar_notificacao_enviada(notif['id'])
                print(f"E-mail enviado com sucesso para {notif['email']}")
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"Erro de autenticação SMTP: {e}")
                return  # Para imediatamente se houver erro de autenticação
            except smtplib.SMTPException as e:
                print(f"Erro SMTP ao enviar e-mail para {notif.get('email')}: {e}")
            except Exception as e:
                print(f"Erro ao enviar e-mail para {notif.get('email')}: {e}")
                
    except Exception as e:
        print(f"Erro geral no processo de envio de notificações: {e}")
    finally:
        if 'yag' in locals():
            try:
                yag.close()
            except:
                pass

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

# Inicializa o scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(enviar_notificacoes, 'interval', minutes=5)
scheduler.add_job(verificar_agendamentos_24h, 'interval', hours=1)
scheduler.start()

# Registra as blueprints
init_app(app)

if __name__ == '__main__':
    app.run(debug=True) 