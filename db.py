import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_connection():
    try:
        # Primeiro conecta sem especificar o banco de dados
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def init_db():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Criar o banco de dados se não existir
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME', 'medical_appointments')}")
            cursor.execute(f"USE {os.getenv('DB_NAME', 'medical_appointments')}")
            
            # Criar tabela de usuários se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    tipo_usuario ENUM('paciente', 'recepcionista') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar tabela de pacientes se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pacientes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    cpf VARCHAR(11) UNIQUE NOT NULL,
                    data_nascimento DATE NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Criar tabela de exames se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exames (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo_exame VARCHAR(100) NOT NULL,
                    data_hora DATETIME NOT NULL,
                    resultado TEXT,
                    status ENUM('agendado', 'confirmado', 'realizado', 'cancelado') DEFAULT 'agendado',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar tabela de agendamentos se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agendamentos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    paciente_id INT NOT NULL,
                    exame_id INT NOT NULL,
                    data_hora DATETIME NOT NULL,
                    status ENUM('agendado', 'confirmado', 'realizado', 'cancelado') DEFAULT 'agendado',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
                    FOREIGN KEY (exame_id) REFERENCES exames(id) ON DELETE CASCADE
                )
            ''')
            
            # Criar tabela de histórico de resultados se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historico_resultados (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    paciente_id INT NOT NULL,
                    exame_id INT NOT NULL,
                    resultado TEXT NOT NULL,
                    data_resultado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
                    FOREIGN KEY (exame_id) REFERENCES exames(id) ON DELETE CASCADE
                )
            ''')
            
            # Criar tabela de notificações se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notificacoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    paciente_id INT NOT NULL,
                    mensagem TEXT NOT NULL,
                    email_destino VARCHAR(255) NOT NULL,
                    status_envio ENUM('pendente', 'enviado', 'erro') DEFAULT 'pendente',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
                )
            ''')
            
            # Criar tabela de recepcionistas se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recepcionistas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            connection.commit()
            print("Banco de dados verificado e atualizado com sucesso!")
        except Error as e:
            print(f"Erro ao inicializar o banco de dados: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def get_db_connection_with_database():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'medical_appointments')
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

# Funções para Usuários
def criar_usuario(username, password, nome, email, tipo_usuario):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, nome, email, tipo_usuario)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username, password, nome, email, tipo_usuario))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Erro ao criar usuário: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

# Funções para Pacientes
def criar_paciente(user_id, cpf, data_nascimento):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pacientes (user_id, cpf, data_nascimento)
                VALUES (%s, %s, %s)
            ''', (user_id, cpf, data_nascimento))
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao criar paciente: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_paciente_by_user_id(user_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT p.*, u.nome 
                FROM pacientes p 
                JOIN users u ON p.user_id = u.id 
                WHERE p.user_id = %s
            ''', (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Erro ao buscar paciente: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

# Funções para Agendamentos
def verificar_disponibilidade(data_hora):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Verifica se já existe agendamento no mesmo horário
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM agendamentos a
                WHERE a.data_hora = %s
                AND a.status = 'agendado'
            ''', (data_hora,))
            result = cursor.fetchone()
            return result['total'] == 0
        except Error as e:
            print(f"Erro ao verificar disponibilidade: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def agendar_exame(paciente_id, tipo_exame, data_hora):
    # Primeiro verifica se o horário está disponível
    if not verificar_disponibilidade(data_hora):
        return False
        
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar email do paciente
            cursor.execute('''
                SELECT u.email 
                FROM users u 
                INNER JOIN pacientes p ON u.id = p.user_id 
                WHERE p.id = %s
            ''', (paciente_id,))
            result = cursor.fetchone()
            email_paciente = result[0] if result else None
            
            if not email_paciente:
                return False
            
            # Criar o exame
            cursor.execute('''
                INSERT INTO exames (tipo_exame, data_hora, status)
                VALUES (%s, %s, 'agendado')
            ''', (tipo_exame, data_hora))
            exame_id = cursor.lastrowid
            
            # Criar o agendamento
            cursor.execute('''
                INSERT INTO agendamentos (paciente_id, exame_id, data_hora, status)
                VALUES (%s, %s, %s, 'agendado')
            ''', (paciente_id, exame_id, data_hora))
            
            # Criar notificação de confirmação
            mensagem = f'Seu exame de {tipo_exame} foi agendado para {data_hora.strftime("%d/%m/%Y às %H:%M")}'
            cursor.execute('''
                INSERT INTO notificacoes (paciente_id, mensagem, email_destino, status_envio)
                VALUES (%s, %s, %s, 'pendente')
            ''', (paciente_id, mensagem, email_paciente))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao agendar exame: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_agendamentos_paciente(paciente_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT a.*, e.tipo_exame
                FROM agendamentos a
                INNER JOIN exames e ON a.exame_id = e.id
                WHERE a.paciente_id = %s AND a.status != 'cancelado'
                ORDER BY a.data_hora
            ''', (paciente_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar agendamentos: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def cancelar_agendamento(agendamento_id, paciente_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar informações do agendamento
            cursor.execute('''
                SELECT e.tipo_exame, a.data_hora
                FROM agendamentos a
                INNER JOIN exames e ON a.exame_id = e.id
                WHERE a.id = %s
            ''', (agendamento_id,))
            exame_info = cursor.fetchone()
            
            # Atualizar status do agendamento
            cursor.execute('''
                UPDATE agendamentos SET status = 'cancelado'
                WHERE id = %s
            ''', (agendamento_id,))
            
            # Atualizar status do exame
            cursor.execute('''
                UPDATE exames e
                INNER JOIN agendamentos a ON e.id = a.exame_id
                SET e.status = 'cancelado'
                WHERE a.id = %s
            ''', (agendamento_id,))
            
            # Criar notificação de cancelamento
            if exame_info:
                cursor.execute('''
                    INSERT INTO notificacoes (paciente_id, mensagem, status_envio)
                    VALUES (%s, %s, 'enviado')
                ''', (paciente_id, f'Seu exame de {exame_info[0]} agendado para {exame_info[1].strftime("%d/%m/%Y às %H:%M")} foi cancelado'))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao cancelar agendamento: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

# Funções para Recepcionista
def criar_recepcionista(user_id, nome):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recepcionistas (user_id, nome)
                VALUES (%s, %s)
            ''', (user_id, nome))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Erro ao criar recepcionista: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def get_notificacoes_paciente(paciente_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM notificacoes
                WHERE paciente_id = %s
                ORDER BY created_at DESC
            ''', (paciente_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar notificações: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def get_todos_pacientes():
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT p.id, u.nome, p.cpf
                FROM pacientes p
                JOIN users u ON p.user_id = u.id
                ORDER BY u.nome
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar pacientes: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def editar_agendamento(agendamento_id, tipo_exame, data_hora):
    if not verificar_disponibilidade(data_hora):
        return False
        
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Atualizar o exame
            cursor.execute('''
                UPDATE exames e
                INNER JOIN agendamentos a ON e.id = a.exame_id
                SET e.tipo_exame = %s, e.data_hora = %s
                WHERE a.id = %s
            ''', (tipo_exame, data_hora, agendamento_id))
            
            # Atualizar o agendamento
            cursor.execute('''
                UPDATE agendamentos
                SET data_hora = %s
                WHERE id = %s
            ''', (data_hora, agendamento_id))
            
            # Criar notificação de alteração
            cursor.execute('''
                INSERT INTO notificacoes (paciente_id, mensagem, status_envio)
                VALUES ((SELECT paciente_id FROM agendamentos WHERE id = %s),
                        %s, 'pendente')
            ''', (agendamento_id, f'Seu exame de {tipo_exame} foi remarcado para {data_hora.strftime("%d/%m/%Y às %H:%M")}'))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao editar agendamento: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_agendamento(agendamento_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT a.*, e.tipo_exame, u.nome as nome_paciente
                FROM agendamentos a
                INNER JOIN exames e ON a.exame_id = e.id
                INNER JOIN pacientes p ON a.paciente_id = p.id
                INNER JOIN users u ON p.user_id = u.id
                WHERE a.id = %s
            ''', (agendamento_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Erro ao buscar agendamento: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

# Funções para Notificações
def get_notificacoes_pendentes():
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT n.*, u.email, e.tipo_exame, e.data_hora
                FROM notificacoes n
                INNER JOIN pacientes p ON n.paciente_id = p.id
                INNER JOIN users u ON p.user_id = u.id
                INNER JOIN agendamentos a ON n.paciente_id = a.paciente_id
                INNER JOIN exames e ON a.exame_id = e.id
                WHERE n.status_envio = 'pendente'
                AND e.data_hora > NOW()
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar notificações pendentes: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def marcar_notificacao_enviada(notificacao_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE notificacoes
                SET status_envio = 'enviado'
                WHERE id = %s
            ''', (notificacao_id,))
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao atualizar notificação: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_agendamentos_proximas_24h():
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT a.*, e.tipo_exame, u.email, u.nome as nome_paciente
                FROM agendamentos a
                INNER JOIN exames e ON a.exame_id = e.id
                INNER JOIN pacientes p ON a.paciente_id = p.id
                INNER JOIN users u ON p.user_id = u.id
                WHERE a.status = 'agendado'
                AND e.data_hora BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 24 HOUR)
                AND NOT EXISTS (
                    SELECT 1 FROM notificacoes n
                    WHERE n.paciente_id = a.paciente_id
                    AND n.mensagem LIKE '%lembrete%'
                    AND n.created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                )
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar agendamentos próximos: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def criar_notificacao_lembrete(agendamento):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            mensagem = f'LEMBRETE: Seu exame de {agendamento["tipo_exame"]} está agendado para amanhã às {agendamento["data_hora"].strftime("%H:%M")}'
            cursor.execute('''
                INSERT INTO notificacoes (paciente_id, mensagem, email_destino, status_envio)
                VALUES (%s, %s, %s, 'pendente')
            ''', (agendamento['paciente_id'], mensagem, agendamento['email']))
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao criar notificação de lembrete: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def atualizar_status_exame(exame_id, novo_status, resultado=None):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Atualizar status do exame
            if resultado:
                cursor.execute('''
                    UPDATE exames 
                    SET status = %s, resultado = %s
                    WHERE id = %s
                ''', (novo_status, resultado, exame_id))
            else:
                cursor.execute('''
                    UPDATE exames 
                    SET status = %s
                    WHERE id = %s
                ''', (novo_status, exame_id))
            
            # Atualizar status do agendamento
            cursor.execute('''
                UPDATE agendamentos 
                SET status = %s
                WHERE exame_id = %s
            ''', (novo_status, exame_id))
            
            # Se o exame foi realizado, adicionar ao histórico
            if novo_status == 'realizado' and resultado:
                cursor.execute('''
                    INSERT INTO historico_resultados (paciente_id, exame_id, resultado)
                    SELECT a.paciente_id, a.exame_id, %s
                    FROM agendamentos a
                    WHERE a.exame_id = %s
                ''', (resultado, exame_id))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao atualizar status do exame: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_historico_resultados(paciente_id):
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT hr.*, e.tipo_exame, e.data_hora
                FROM historico_resultados hr
                INNER JOIN exames e ON hr.exame_id = e.id
                WHERE hr.paciente_id = %s
                ORDER BY hr.data_resultado DESC
            ''', (paciente_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar histórico de resultados: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def get_agendamentos_recepcionista():
    conn = get_db_connection_with_database()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT a.*, e.tipo_exame, e.resultado, e.status,
                       p.id as paciente_id, u.nome as nome_paciente
                FROM agendamentos a
                INNER JOIN exames e ON a.exame_id = e.id
                INNER JOIN pacientes p ON a.paciente_id = p.id
                INNER JOIN users u ON p.user_id = u.id
                ORDER BY a.data_hora DESC
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar agendamentos: {e}")
            return []
        finally:
            cursor.close()
            conn.close() 