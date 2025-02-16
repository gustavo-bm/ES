from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from db import (
    get_db_connection_with_database, init_db, criar_usuario, criar_paciente, criar_recepcionista,
    agendar_exame, cancelar_agendamento, get_agendamentos_paciente,
    get_paciente_by_user_id, get_notificacoes_paciente, get_notificacoes_pendentes,
    marcar_notificacao_enviada, get_agendamentos_proximas_24h, criar_notificacao_lembrete,
    get_todos_pacientes, editar_agendamento, get_agendamento, atualizar_status_exame,
    get_historico_resultados, get_agendamentos_recepcionista
)
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from functools import wraps
import traceback
import yagmail
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave_secreta_do_app'

# Configuração do yagmail
yag = yagmail.SMTP(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))

def enviar_notificacoes():
    notificacoes = get_notificacoes_pendentes()
    for notif in notificacoes:
        try:
            yag.send(
                to=notif['email'],
                subject='Agendamento de Exame',
                contents=notif['mensagem']
            )
            marcar_notificacao_enviada(notif['id'])
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")

def verificar_agendamentos_24h():
    agendamentos = get_agendamentos_proximas_24h()
    for agend in agendamentos:
        criar_notificacao_lembrete(agend)

# Inicializar o scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(enviar_notificacoes, 'interval', minutes=5)
scheduler.add_job(verificar_agendamentos_24h, 'interval', hours=1)
scheduler.start()

# Decorador para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection_with_database()
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
                session['user_id'] = user['id']
                session['nome'] = user['nome']
                session['tipo_usuario'] = user['tipo_usuario']
                return redirect(url_for('dashboard'))
            
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
    session.clear()
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nome = request.form['nome']
        email = request.form['email']
        tipo_usuario = request.form['tipo_usuario']
        
        # Criar usuário
        user_id = criar_usuario(username, password, nome, email, tipo_usuario)
        
        if user_id:
            if tipo_usuario == 'paciente':
                cpf = request.form['cpf']
                data_nascimento = request.form['data_nascimento']
                
                if criar_paciente(user_id, cpf, data_nascimento):
                    flash('Cadastro realizado com sucesso!')
                    return redirect(url_for('login'))
                else:
                    # Se falhar ao criar paciente, precisamos excluir o usuário
                    conn = get_db_connection_with_database()
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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection_with_database()
    cursor = conn.cursor(dictionary=True)
    
    user_id = session['user_id']
    tipo_usuario = session['tipo_usuario']
    
    if tipo_usuario == 'paciente':
        # Primeiro, buscar o ID do paciente
        cursor.execute('SELECT id FROM pacientes WHERE user_id = %s', (user_id,))
        paciente = cursor.fetchone()
        
        if paciente:
            # Buscar exames do paciente
            cursor.execute('''
                SELECT e.id, e.data_hora, e.tipo_exame, e.status
                FROM exames e
                INNER JOIN agendamentos a ON e.id = a.exame_id
                WHERE a.paciente_id = %s
                ORDER BY e.data_hora DESC
            ''', (paciente['id'],))
            exames = cursor.fetchall()
            
            # Buscar notificações do paciente
            cursor.execute('''
                SELECT id, mensagem, created_at, status_envio
                FROM notificacoes
                WHERE paciente_id = %s
                ORDER BY created_at DESC
            ''', (paciente['id'],))
            notificacoes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('paciente/dashboard.html', 
                                exames=exames, 
                                notificacoes=notificacoes)
        
    elif tipo_usuario == 'recepcionista':
        cursor.execute('''
            SELECT e.id, e.data_hora, e.tipo_exame, e.status,
                   u.nome as nome_paciente
            FROM exames e
            INNER JOIN agendamentos a ON e.id = a.exame_id
            INNER JOIN pacientes p ON a.paciente_id = p.id
            INNER JOIN users u ON p.user_id = u.id
            ORDER BY e.data_hora DESC
        ''')
        exames = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('recepcionista/dashboard.html', exames=exames)
    
    return redirect(url_for('login'))

@app.route('/paciente/dashboard')
def dashboard_paciente():
    if 'user_id' not in session or session['tipo_usuario'] != 'paciente':
        return redirect(url_for('login'))
    
    paciente = get_paciente_by_user_id(session['user_id'])
    if not paciente:
        return redirect(url_for('logout'))
    
    agendamentos = get_agendamentos_paciente(paciente['id'])
    notificacoes = get_notificacoes_paciente(paciente['id'])
    
    return render_template('paciente/dashboard.html', 
                         agendamentos=agendamentos,
                         notificacoes=notificacoes)

@app.route('/paciente/agendar', methods=['GET', 'POST'])
def agendar_exame_paciente():
    if 'user_id' not in session or session['tipo_usuario'] != 'paciente':
        return redirect(url_for('login'))
    
    paciente = get_paciente_by_user_id(session['user_id'])
    if not paciente:
        return redirect(url_for('logout'))
    
    if request.method == 'POST':
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if agendar_exame(paciente['id'], tipo_exame, data_hora):
            flash('Exame agendado com sucesso!')
            return redirect(url_for('dashboard_paciente'))
        else:
            flash('Erro ao agendar exame.')
    
    return render_template('paciente/agendar.html')

@app.route('/paciente/cancelar/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento_paciente(agendamento_id):
    if 'user_id' not in session or session['tipo_usuario'] != 'paciente':
        return redirect(url_for('login'))
    
    paciente = get_paciente_by_user_id(session['user_id'])
    if not paciente:
        return redirect(url_for('logout'))
    
    if cancelar_agendamento(agendamento_id, paciente['id']):
        flash('Agendamento cancelado com sucesso!')
    else:
        flash('Erro ao cancelar agendamento.')
    
    return redirect(url_for('dashboard_paciente'))

@app.route('/recepcionista/dashboard')
@login_required
def dashboard_recepcionista():
    if session['tipo_usuario'] != 'recepcionista':
        return redirect(url_for('login'))
    
    agendamentos = get_agendamentos_recepcionista()
    return render_template('recepcionista/dashboard.html', exames=agendamentos)

@app.route('/recepcionista/atualizar_status/<int:exame_id>', methods=['POST'])
@login_required
def atualizar_status_exame_route(exame_id):
    if session['tipo_usuario'] != 'recepcionista':
        return redirect(url_for('login'))
    
    novo_status = request.form.get('status')
    resultado = request.form.get('resultado')
    
    if atualizar_status_exame(exame_id, novo_status, resultado):
        flash('Status atualizado com sucesso!', 'success')
    else:
        flash('Erro ao atualizar status.', 'error')
    
    return redirect(url_for('dashboard_recepcionista'))

@app.route('/recepcionista/editar_agendamento/<int:agendamento_id>', methods=['GET', 'POST'])
@login_required
def editar_agendamento_route(agendamento_id):
    if session['tipo_usuario'] != 'recepcionista':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if editar_agendamento(agendamento_id, tipo_exame, data_hora):
            flash('Agendamento atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard_recepcionista'))
        else:
            flash('Erro ao atualizar agendamento.', 'error')
    
    agendamento = get_agendamento(agendamento_id)
    return render_template('recepcionista/editar_agendamento.html', agendamento=agendamento)

@app.route('/recepcionista/cancelar/<int:agendamento_id>', methods=['POST'])
@login_required
def cancelar_agendamento_recepcionista(agendamento_id):
    if session['tipo_usuario'] != 'recepcionista':
        return redirect(url_for('login'))
    
    agendamento = get_agendamento(agendamento_id)
    if agendamento and cancelar_agendamento(agendamento_id, agendamento['paciente_id']):
        flash('Agendamento cancelado com sucesso!', 'success')
    else:
        flash('Erro ao cancelar agendamento.', 'error')
    
    return redirect(url_for('dashboard_recepcionista'))

@app.route('/paciente/historico')
@login_required
def historico_paciente():
    if session['tipo_usuario'] != 'paciente':
        return redirect(url_for('login'))
    
    paciente = get_paciente_by_user_id(session['user_id'])
    if not paciente:
        return redirect(url_for('logout'))
    
    historico = get_historico_resultados(paciente['id'])
    return render_template('paciente/historico.html', historico=historico)

@app.route('/healthcheck')
def healthcheck():
    try:
        conn = get_db_connection_with_database()
        if conn:
            conn.close()
            return jsonify({"status": "healthy", "database": "connected"}), 200
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 500
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 