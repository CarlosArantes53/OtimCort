# app/routes.py
from flask import (
    Blueprint, render_template, request, jsonify, current_app, abort
)
from collections import defaultdict
from . import database
from .optimizer import OtimizadorCorte1D

# Cria um Blueprint. Todas as rotas serão registradas nele.
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Página inicial com lista de itens"""
    db_path = current_app.config['DATABASE_PATH']
    items = database.get_all_items(db_path)
    
    # Agrupa por dimensões para visualização
    grupos = defaultdict(list)
    for item in items:
        chave = (item.espessura, item.largura)
        grupos[chave].append(item)
    
    return render_template(
        'index.html', 
        items=items, 
        largura_chapa=current_app.config['LARGURA_CHAPA_PADRAO'],
        grupos=grupos
    )

@bp.route('/api/config', methods=['GET', 'POST'])
def config():
    """Endpoint para configurar largura da chapa"""
    
    # ATENÇÃO: Modificar a configuração em tempo de execução (POST)
    # é perigoso em produção, pois afeta TODOS os usuários.
    # Esta rota agora afeta o app.config.
    
    if request.method == 'POST':
        data = request.get_json()
        nova_largura = data.get('largura_chapa')
        
        if nova_largura and float(nova_largura) > 0:
            current_app.config['LARGURA_CHAPA_PADRAO'] = float(nova_largura)
            return jsonify({
                'success': True, 
                'largura_chapa': current_app.config['LARGURA_CHAPA_PADRAO']
            })
        return jsonify({'success': False, 'error': 'Largura inválida'}), 400
    
    # GET
    return jsonify({'largura_chapa': current_app.config['LARGURA_CHAPA_PADRAO']})

@bp.route('/otimizar/<item_code>')
def otimizar(item_code):
    """Otimiza corte para um item selecionado"""
    
    # Pega configurações atuais do app
    db_path = current_app.config['DATABASE_PATH']
    largura_chapa = current_app.config['LARGURA_CHAPA_PADRAO']
    margem_corte = current_app.config['MARGEM_CORTE']

    # Busca o item selecionado
    item_selecionado = database.get_item_by_code(db_path, item_code)
    
    if not item_selecionado:
        return abort(404, "Item não encontrado")
    
    # Busca todos os itens com mesma espessura e largura
    itens_grupo = database.get_items_by_dimensions(
        db_path, 
        item_selecionado.espessura, 
        item_selecionado.largura
    )
    
    # Executa otimização
    # Passamos as configurações para o otimizador
    otimizador = OtimizadorCorte1D(largura_chapa, margem_corte)
    top_padroes = otimizador.gerar_padroes_otimizados(itens_grupo, top_n=10)
    
    return render_template(
        'results.html',
        item_selecionado=item_selecionado,
        padroes=top_padroes,
        largura_chapa=largura_chapa,
        total_itens_grupo=len(itens_grupo)
    )