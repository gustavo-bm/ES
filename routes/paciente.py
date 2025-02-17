from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from db import (
    get_paciente_by_user_id, get_agendamentos_paciente,
    get_notificacoes_paciente, agendar_exame as db_agendar_exame, 
    cancelar_agendamento as db_cancelar_agendamento
)
from models import Paciente, Agendamento, Notificacao

paciente_bp = Blueprint('paciente', __name__, url_prefix='/paciente')

@paciente_bp.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('auth.login'))
    
    agendamentos = get_agendamentos_paciente(paciente.id)
    notificacoes = get_notificacoes_paciente(paciente.id)
    
    return render_template('paciente/dashboard.html', 
                         agendamentos=agendamentos,
                         notificacoes=notificacoes,
                         user_id=user_id)

@paciente_bp.route('/agendar/<int:user_id>', methods=['GET', 'POST'])
def agendar_exame(user_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if db_agendar_exame(paciente.id, tipo_exame, data_hora):
            flash('Exame agendado com sucesso!')
            return redirect(url_for('paciente.dashboard', user_id=user_id))
        else:
            flash('Erro ao agendar exame.')
    
    return render_template('paciente/agendar.html', user_id=user_id, now=datetime.now())

@paciente_bp.route('/cancelar/<int:user_id>/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento(user_id, agendamento_id):
    print(f"[DEBUG] Iniciando cancelamento - User ID: {user_id}, Agendamento ID: {agendamento_id}")
    
    # Verificar se o paciente existe
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        print("[DEBUG] Paciente não encontrado")
        flash('Paciente não encontrado.')
        return redirect(url_for('auth.login'))
    
    try:
        # Tentar cancelar o agendamento
        if db_cancelar_agendamento(agendamento_id, paciente.id):
            print("[DEBUG] Agendamento cancelado com sucesso")
            flash('Agendamento cancelado com sucesso!')
        else:
            print("[DEBUG] Erro ao cancelar agendamento")
            flash('Erro ao cancelar agendamento.')
            
        # Importante: Redirecionar apenas uma vez, no final da função
        return redirect(url_for('paciente.dashboard', user_id=user_id))
        
    except Exception as e:
        print(f"[DEBUG] Erro durante o cancelamento: {e}")
        flash('Erro ao processar o cancelamento.')
        return redirect(url_for('paciente.dashboard', user_id=user_id)) 