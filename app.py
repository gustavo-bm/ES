from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from email_service import enviar_notificacoes, verificar_agendamentos_24h

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'chave_secreta_do_app'

    # Inicializa o scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(enviar_notificacoes, 'interval', minutes=5)
    scheduler.add_job(verificar_agendamentos_24h, 'interval', hours=1)
    scheduler.start()

    # Registra as blueprints
    from routes import init_app
    init_app(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 