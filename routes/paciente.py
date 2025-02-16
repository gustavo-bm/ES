from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from db import (
    get_paciente_by_user_id, get_agendamentos_paciente,
    get_notificacoes_paciente, agendar_exame as db_agendar_exame, cancelar_agendamento
)

paciente_bp = Blueprint('paciente', __name__, url_prefix='/paciente')

@paciente_bp.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('auth.login'))
    
    agendamentos = get_agendamentos_paciente(paciente['id'])
    notificacoes = get_notificacoes_paciente(paciente['id'])
    
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
        
        if db_agendar_exame(paciente['id'], tipo_exame, data_hora):
            flash('Exame agendado com sucesso!')
            return redirect(url_for('paciente.dashboard', user_id=user_id))
        else:
            flash('Erro ao agendar exame.')
    
    return render_template('paciente/agendar.html', user_id=user_id, now=datetime.now())

@paciente_bp.route('/cancelar/<int:user_id>/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento(user_id, agendamento_id):
    paciente = get_paciente_by_user_id(user_id)
    if not paciente:
        return redirect(url_for('auth.login'))
    
    if cancelar_agendamento(agendamento_id, paciente['id']):
        flash('Agendamento cancelado com sucesso!')
    else:
        flash('Erro ao cancelar agendamento.')
    
    return redirect(url_for('paciente.dashboard', user_id=user_id)) 