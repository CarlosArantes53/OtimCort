# app/__init__.py
from flask import Flask
from config import Config

def create_app(config_class=Config):
    """Fábrica de Aplicação"""
    app = Flask(__name__)
    
    # Carrega a configuração a partir da classe
    app.config.from_object(config_class)

    # Armazena configurações globais no app.config
    # Substitui a variável global LARGURA_CHAPA_PADRAO
    app.config['LARGURA_CHAPA_PADRAO'] = config_class.LARGURA_CHAPA_PADRAO
    app.config['DATABASE_PATH'] = config_class.DATABASE_PATH
    
    # Registra as rotas (Blueprint)
    with app.app_context():
        from . import routes
        app.register_blueprint(routes.bp)

    return app