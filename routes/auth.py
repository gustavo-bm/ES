from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db_connection, criar_usuario, criar_paciente

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
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
                    return redirect(url_for('paciente.dashboard', user_id=user['id']))
                else:
                    return redirect(url_for('recepcionista.dashboard'))
            
            flash('Usuário ou senha incorretos')
            
        except Exception as e:
            print(f"Erro no login: {e}")
            flash('Erro ao realizar login')
            
        finally:
            cursor.close()
            conn.close()
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    return redirect(url_for('auth.login'))

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
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
                    return redirect(url_for('auth.login'))
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
                return redirect(url_for('auth.login'))
        
        flash('Erro ao realizar cadastro')
    
    return render_template('cadastro.html') 