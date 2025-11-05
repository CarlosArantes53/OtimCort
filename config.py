import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT'))

    DATABASE_PATH = os.environ.get('DATABASE_PATH')
    if not DATABASE_PATH:
        raise ValueError("A variável de ambiente DATABASE_PATH não foi definida.")

    LARGURA_CHAPA_PADRAO = float(os.environ.get('LARGURA_CHAPA_PADRAO', 1220.0))
    MARGEM_CORTE = float(os.environ.get('MARGEM_CORTE', 5.0))