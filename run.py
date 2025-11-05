# run.py
from app import create_app
from config import Config

# Cria a aplicação usando a fábrica
app = create_app(Config)

if __name__ == '__main__':
    # Usa as configurações de DEBUG e PORTA carregadas do .env
    app.run(
        debug=app.config['DEBUG'], 
        port=app.config['PORT'], 
        host='0.0.0.0' # Permite acesso na rede
    )