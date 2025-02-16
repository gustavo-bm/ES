from flask import Blueprint, jsonify
from db import get_db_connection
from app import enviar_notificacoes

healthcheck_bp = Blueprint('healthcheck', __name__)

@healthcheck_bp.route('/healthcheck')
def healthcheck():
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({"status": "healthy", "database": "connected"}), 200
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 500
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@healthcheck_bp.route('/force-email')
def force_email():
    try:
        enviar_notificacoes()
        return jsonify({"status": "success", "message": "Tentativa de envio de e-mails realizada"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 