from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from db import (
    get_agendamentos_recepcionista, get_todos_pacientes,
    agendar_exame, atualizar_status_exame, editar_agendamento,
    get_agendamento, cancelar_agendamento
)

recepcionista_bp = Blueprint('recepcionista', __name__, url_prefix='/recepcionista')

@recepcionista_bp.route('/dashboard')
def dashboard():
    agendamentos = get_agendamentos_recepcionista()
    return render_template('recepcionista/dashboard.html', exames=agendamentos)

@recepcionista_bp.route('/agendar', methods=['GET', 'POST'])
def agendar_exame():
    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if agendar_exame(paciente_id, tipo_exame, data_hora):
            flash('Exame agendado com sucesso!', 'success')
            return redirect(url_for('recepcionista.dashboard'))
        else:
            flash('Erro ao agendar exame.', 'error')
    
    pacientes = get_todos_pacientes()
    return render_template('recepcionista/agendar.html', pacientes=pacientes, now=datetime.now())

@recepcionista_bp.route('/atualizar_status/<int:exame_id>', methods=['POST'])
def atualizar_status(exame_id):
    novo_status = request.form.get('status')
    
    if atualizar_status_exame(exame_id, novo_status):
        flash('Status atualizado com sucesso!', 'success')
    else:
        flash('Erro ao atualizar status.', 'error')
    
    return redirect(url_for('recepcionista.dashboard'))

@recepcionista_bp.route('/editar_agendamento/<int:agendamento_id>', methods=['GET', 'POST'])
def editar_agendamento(agendamento_id):
    if request.method == 'POST':
        tipo_exame = request.form['tipo_exame']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        
        if editar_agendamento(agendamento_id, tipo_exame, data_hora):
            flash('Agendamento atualizado com sucesso!', 'success')
            return redirect(url_for('recepcionista.dashboard'))
        else:
            flash('Erro ao atualizar agendamento.', 'error')
    
    agendamento = get_agendamento(agendamento_id)
    return render_template('recepcionista/editar_agendamento.html', agendamento=agendamento, now=datetime.now())

@recepcionista_bp.route('/cancelar/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento(agendamento_id):
    agendamento = get_agendamento(agendamento_id)
    if agendamento and cancelar_agendamento(agendamento_id, agendamento['paciente_id']):
        flash('Agendamento cancelado com sucesso!', 'success')
    else:
        flash('Erro ao cancelar agendamento.', 'error')
    
    return redirect(url_for('recepcionista.dashboard')) 