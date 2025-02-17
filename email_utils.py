import yagmail
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

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

def enviar_email(destinatario, assunto, mensagem):
    print(f"\nIniciando envio de e-mail para {destinatario}")
    print(f"Assunto: {assunto}")
    
    try:
        print("Obtendo instância do yagmail...")
        yag = get_yagmail_instance()
        if not yag:
            print("Não foi possível inicializar o serviço de e-mail - yagmail retornou None")
            return False
            
        print("Preparando conteúdo do e-mail...")
        conteudo = [
            f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Sistema de Agendamento de Exames</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    {mensagem.replace(chr(10), '<br>')}
                </div>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
                    Esta é uma mensagem automática, por favor não responda.
                </p>
            </div>
            '''
        ]
        
        print("Enviando e-mail via yagmail...")
        yag.send(
            to=destinatario,
            subject=assunto,
            contents=conteudo
        )
        print(f"E-mail enviado com sucesso para {destinatario}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Erro de autenticação SMTP: {e}")
        print("Verifique as credenciais no arquivo .env")
        return False
    except smtplib.SMTPException as e:
        print(f"Erro SMTP ao enviar e-mail: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao enviar e-mail: {e}")
        return False
    finally:
        if 'yag' in locals():
            try:
                print("Fechando conexão SMTP...")
                yag.close()
            except:
                pass 