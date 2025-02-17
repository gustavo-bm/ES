import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime
from email_utils import enviar_email
from models import Paciente, Recepcionista, Agendamento, Notificacao, Exame

load_dotenv()

def get_db_connection():
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

def criar_usuario(username, password, nome, email, tipo_usuario):
    conn = get_db_connection()
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

def criar_paciente(user_id, cpf, data_nascimento):
    conn = get_db_connection()
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
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT p.*, u.nome, u.username, u.email 
                FROM pacientes p 
                JOIN users u ON p.user_id = u.id 
                WHERE p.user_id = %s
            ''', (user_id,))
            result = cursor.fetchone()
            if result:
                return Paciente(
                    id=result['id'],
                    username=result['username'],
                    nome=result['nome'],
                    email=result['email'],
                    cpf=result['cpf'],
                    data_nascimento=result['data_nascimento'],
                    user_id=result['user_id']
                )
            return None
        except Error as e:
            print(f"Erro ao buscar paciente: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def verificar_disponibilidade(data_hora):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
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
    print(f"Iniciando agendamento de exame para paciente {paciente_id}")
    if not verificar_disponibilidade(data_hora):
        print("Horário indisponível para agendamento")
        return False
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Registrando exame
            print("Registrando exame...")
            cursor.execute('''
                INSERT INTO exames (tipo_exame, data_hora, status)
                VALUES (%s, %s, 'agendado')
            ''', (tipo_exame, data_hora))
            exame_id = cursor.lastrowid
            
            # Registrando agendamento
            print("Registrando agendamento...")
            cursor.execute('''
                INSERT INTO agendamentos (paciente_id, exame_id, data_hora, status)
                VALUES (%s, %s, %s, 'agendado')
            ''', (paciente_id, exame_id, data_hora))
            agendamento_id = cursor.lastrowid
            
            # Criando objetos do modelo
            paciente = get_paciente_by_user_id(paciente_id)
            if not paciente:
                print(f"Paciente {paciente_id} não encontrado")
                return False
                
            agendamento = Agendamento(
                id=agendamento_id,
                paciente=paciente,
                tipo_exame=tipo_exame,
                data_hora=data_hora
            )
            
            # Criando e anexando observador
            notificacao = Notificacao()
            agendamento.attach(notificacao)
            
            # Notificando sobre o novo agendamento
            agendamento.notify()
            
            conn.commit()
            print("Agendamento concluído com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao agendar exame: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_agendamentos_paciente(paciente_id):
    conn = get_db_connection()
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
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar informações do agendamento
            cursor.execute('''
                SELECT a.*, e.tipo_exame, e.data_hora, p.user_id
                FROM agendamentos a
                INNER JOIN exames e ON a.exame_id = e.id
                INNER JOIN pacientes p ON a.paciente_id = p.id
                WHERE a.id = %s AND a.paciente_id = %s
            ''', (agendamento_id, paciente_id))
            agend_info = cursor.fetchone()
            
            if not agend_info:
                print("Agendamento não encontrado")
                return False
            
            # Buscar paciente
            paciente = get_paciente_by_user_id(agend_info['user_id'])
            if not paciente:
                print("Paciente não encontrado")
                return False
            
            # Criar objeto de agendamento
            agendamento = Agendamento(
                id=agendamento_id,
                paciente=paciente,
                tipo_exame=agend_info['tipo_exame'],
                data_hora=agend_info['data_hora'],
                status='agendado'
            )
            
            # Anexar observador
            notificacao = Notificacao()
            agendamento.attach(notificacao)
            
            # Atualizar status no banco
            cursor.execute('''
                UPDATE agendamentos SET status = 'cancelado'
                WHERE id = %s
            ''', (agendamento_id,))
            
            cursor.execute('''
                UPDATE exames e
                INNER JOIN agendamentos a ON e.id = a.exame_id
                SET e.status = 'cancelado'
                WHERE a.id = %s
            ''', (agendamento_id,))
            
            # Cancelar agendamento e notificar
            agendamento.cancelar()
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao cancelar agendamento: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def criar_recepcionista(user_id, nome):
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
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
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Primeiro, buscar informações do paciente
            cursor.execute('''
                SELECT p.id as paciente_id, u.email, u.nome
                FROM agendamentos a
                JOIN pacientes p ON a.paciente_id = p.id
                JOIN users u ON p.user_id = u.id
                WHERE a.id = %s
            ''', (agendamento_id,))
            
            paciente_info = cursor.fetchone()
            if not paciente_info:
                print("Paciente não encontrado")
                return False
            
            # Atualizar exame
            cursor.execute('''
                UPDATE exames e
                INNER JOIN agendamentos a ON e.id = a.exame_id
                SET e.tipo_exame = %s, e.data_hora = %s
                WHERE a.id = %s
            ''', (tipo_exame, data_hora, agendamento_id))
            
            # Atualizar agendamento
            cursor.execute('''
                UPDATE agendamentos
                SET data_hora = %s
                WHERE id = %s
            ''', (data_hora, agendamento_id))
            
            # Criar notificação
            mensagem = f'Seu exame de {tipo_exame} foi remarcado para {data_hora.strftime("%d/%m/%Y às %H:%M")}'
            cursor.execute('''
                INSERT INTO notificacoes (paciente_id, mensagem, email_destino, status_envio)
                VALUES (%s, %s, %s, 'pendente')
            ''', (paciente_info['paciente_id'], mensagem, paciente_info['email']))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao editar agendamento: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_agendamento(agendamento_id):
    conn = get_db_connection()
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

def get_notificacoes_pendentes():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT DISTINCT n.*, u.email, e.tipo_exame, e.data_hora, u.nome as nome_paciente
                FROM notificacoes n
                INNER JOIN pacientes p ON n.paciente_id = p.id
                INNER JOIN users u ON p.user_id = u.id
                LEFT JOIN agendamentos a ON n.paciente_id = a.paciente_id
                LEFT JOIN exames e ON a.exame_id = e.id
                WHERE n.status_envio = 'pendente'
                AND (e.data_hora > NOW() OR e.data_hora IS NULL)
                ORDER BY n.created_at DESC
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar notificações pendentes: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def marcar_notificacao_enviada(notificacao_id):
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            mensagem = f'''Olá {agendamento['nome_paciente']},

LEMBRETE: Seu exame de {agendamento["tipo_exame"]} está agendado para amanhã às {agendamento["data_hora"].strftime("%H:%M")}.

Local: Clínica de Exames
Endereço: Rua dos Exames, 123
Data: {agendamento["data_hora"].strftime("%d/%m/%Y")}
Horário: {agendamento["data_hora"].strftime("%H:%M")}

Lembretes importantes:
- Chegue com 15 minutos de antecedência
- Traga um documento com foto
- Em caso de necessidade de cancelamento, avise com antecedência

Atenciosamente,
Equipe da Clínica'''

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

def atualizar_status_exame(exame_id, novo_status):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE exames 
                SET status = %s
                WHERE id = %s
            ''', (novo_status, exame_id))
            
            cursor.execute('''
                UPDATE agendamentos 
                SET status = %s
                WHERE exame_id = %s
            ''', (novo_status, exame_id))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao atualizar status do exame: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def get_agendamentos_recepcionista():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT a.*, e.tipo_exame, e.status,
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