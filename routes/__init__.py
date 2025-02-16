from .auth import auth_bp
from .paciente import paciente_bp
from .recepcionista import recepcionista_bp
from .healthcheck import healthcheck_bp

def init_app(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(paciente_bp)
    app.register_blueprint(recepcionista_bp)
    app.register_blueprint(healthcheck_bp) 