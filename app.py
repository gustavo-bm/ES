from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from db import (
    get_db_connection, criar_usuario, criar_paciente, criar_recepcionista,
    agendar_exame, cancelar_agendamento, get_agendamentos_paciente,
    get_paciente_by_user_id, get_notificacoes_paciente, get_notificacoes_pendentes,
    marcar_notificacao_enviada, get_agendamentos_proximas_24h, criar_notificacao_lembrete,
    get_todos_pacientes, editar_agendamento, get_agendamento, atualizar_status_exame,
    get_agendamentos_recepcionista
)
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from functools import wraps
import traceback
import yagmail
import smtplib
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv

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
            
        return yagmail.SMTP(email, password)
    except Exception as e:
        print(f"Erro ao criar instância do yagmail: {e}")
        return None

def enviar_notificacoes():
    try:
        notificacoes = get_notificacoes_pendentes()
        if not notificacoes:
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
                    
                yag.send(
                    to=notif['email'],
                    subject='Agendamento de Exame',
                    contents=notif['mensagem']
                )
                marcar_notificacao_enviada(notif['id'])
                print(f"E-mail enviado com sucesso para {notif['email']}")
                
            except smtplib.SMTPException as e:
                print(f"Erro SMTP ao enviar e-mail para {notif.get('email')}: {e}")
            except Exception as e:
                print(f"Erro ao enviar e-mail para {notif.get('email')}: {e}")
                
    except Exception as e:
        print(f"Erro geral no processo de envio de notificações: {e}")
    finally:
        if 'yag' in locals():
            yag.close()

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

scheduler = BackgroundScheduler()
scheduler.add_job(enviar_notificacoes, 'interval', minutes=5)
scheduler.add_job(verificar_agendamentos_24h, 'interval', hours=1)
scheduler.start()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if not conn:
            flash('Erro de conexão com o banco de dados')
            return render_template('login.html')
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT id, nome, tipo_usuario 
                FROM users 
                WHERE username = %s AND password = %s
            ''', (username, password))
            user = cursor.fetchone()
            
            if user:
                if user['tipo_usuario'] == 'paciente':
                    return redirect(url_for('dashboard_paciente', user_id=user['id']))
                else:
                    return redirect(url_for('dashboard_recepcionista'))
            
            flash('Usuário ou senha incorretos')
            
        except Exception as e:
            print(f"Erro no login: {e}")
            flash('Erro ao realizar login')
            
        finally:
            cursor.close()
            conn.close()
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nome = request.form['nome']
        email = request.form['email']
        tipo_usuario = request.form['tipo_usuario']
        
        user_id = criar_usuario(username, password, nome, email, tipo_usuario)
        
        if user_id:
            if tipo_usuario == 'paciente':
                cpf = request.form['cpf']
                data_nascimento = request.form['data_nascimento']
                
                if criar_paciente(user_id, cpf, data_nascimento):
                    flash('Cadastro realizado com sucesso!')
                    return redirect(url_for('login'))
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
                        conn.commit()
                        cursor.close()
                        conn.close()
            else:
                flash('Cadastro realizado com sucesso!')
                return redirect(url_for('login'))
        
        flash('Erro ao realizar cadastro')
    
    return render_template('cadastro.html')

@app.route('/paciente/dashboard/<int:user_id>')
def dashboard_paciente(user_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('login'))
    
    agendamentos = get_agendamentos_paciente(paciente['id'])
    notificacoes = get_notificacoes_paciente(paciente['id'])
    
    return render_template('paciente/dashboard.html', 
                         agendamentos=agendamentos,
                         notificacoes=notificacoes,
                         user_id=user_id)

@app.route('/paciente/agendar/<int:user_id>', methods=['GET', 'POST'])
def agendar_exame_paciente(user_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if agendar_exame(paciente['id'], tipo_exame, data_hora):
            flash('Exame agendado com sucesso!')
            return redirect(url_for('dashboard_paciente', user_id=user_id))
        else:
            flash('Erro ao agendar exame.')
    
    return render_template('paciente/agendar.html', user_id=user_id, now=datetime.now())

@app.route('/paciente/cancelar/<int:user_id>/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento_paciente(user_id, agendamento_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('login'))
    
    if cancelar_agendamento(agendamento_id, paciente['id']):
        flash('Agendamento cancelado com sucesso!')
    else:
        flash('Erro ao cancelar agendamento.')
    
    return redirect(url_for('dashboard_paciente', user_id=user_id))

@app.route('/recepcionista/dashboard')
def dashboard_recepcionista():
    agendamentos = get_agendamentos_recepcionista()
    return render_template('recepcionista/dashboard.html', exames=agendamentos)

@app.route('/recepcionista/agendar', methods=['GET', 'POST'])
def agendar_exame_recepcionista():
    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if agendar_exame(paciente_id, tipo_exame, data_hora):
            flash('Exame agendado com sucesso!', 'success')
            return redirect(url_for('dashboard_recepcionista'))
        else:
            flash('Erro ao agendar exame.', 'error')
    
    pacientes = get_todos_pacientes()
    return render_template('recepcionista/agendar.html', pacientes=pacientes, now=datetime.now())

@app.route('/recepcionista/atualizar_status/<int:exame_id>', methods=['POST'])
def atualizar_status_exame_route(exame_id):
    novo_status = request.form.get('status')
    
    if atualizar_status_exame(exame_id, novo_status):
        flash('Status atualizado com sucesso!', 'success')
    else:
        flash('Erro ao atualizar status.', 'error')
    
    return redirect(url_for('dashboard_recepcionista'))

@app.route('/recepcionista/editar_agendamento/<int:agendamento_id>', methods=['GET', 'POST'])
def editar_agendamento_route(agendamento_id):
    if request.method == 'POST':
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if editar_agendamento(agendamento_id, tipo_exame, data_hora):
            flash('Agendamento atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard_recepcionista'))
        else:
            flash('Erro ao atualizar agendamento.', 'error')
    
    agendamento = get_agendamento(agendamento_id)
    return render_template('recepcionista/editar_agendamento.html', agendamento=agendamento, now=datetime.now())

@app.route('/recepcionista/cancelar/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento_recepcionista(agendamento_id):
    agendamento = get_agendamento(agendamento_id)
    if agendamento and cancelar_agendamento(agendamento_id, agendamento['paciente_id']):
        flash('Agendamento cancelado com sucesso!', 'success')
    else:
        flash('Erro ao cancelar agendamento.', 'error')
    
    return redirect(url_for('dashboard_recepcionista'))

@app.route('/healthcheck')
def healthcheck():
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({"status": "healthy", "database": "connected"}), 200
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 500
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 