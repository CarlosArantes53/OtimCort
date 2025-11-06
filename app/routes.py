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
    
    # --- INÍCIO DA MODIFICAÇÃO ---

    # 1. Ordena os itens por prioridade (maior primeiro)
    # A propriedade .prioridade é definida em models.py (10 para alta, 1 para baixa)
    items_ordenados = sorted(items, key=lambda item: item.prioridade, reverse=True)
    
    # 2. Extrai espessuras únicas para o filtro
    espessuras_unicas = sorted(list(set(item.espessura for item in items)))

    # --- FIM DA MODIFICAÇÃO ---

    # Agrupa por dimensões para visualização (mantido se você usar em outro lugar)
    grupos = defaultdict(list)
    for item in items:
        chave = (item.espessura, item.largura)
        grupos[chave].append(item)
    
    return render_template(
        'index.html', 
        items=items_ordenados,  # Passa a lista ordenada
        espessuras=espessuras_unicas, # Passa a lista de espessuras
        largura_chapa=current_app.config['LARGURA_CHAPA_PADRAO'],
        grupos=grupos
    )

@bp.route('/api/config', methods=['GET', 'POST'])
def config():
    # ... (resto do arquivo sem modificação) ...
# ... (resto do arquivo sem modificação) ...
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
# app/routes.py

# ... (imports e outras rotas) ...

@bp.route('/otimizar/<item_code>')
def otimizar(item_code):
    """Otimiza corte para um item selecionado"""
    
    # Pega configurações padrão do app
    db_path = current_app.config['DATABASE_PATH']
    default_largura = current_app.config['LARGURA_CHAPA_PADRAO']

    # Pega valores da URL (query parameters)
    try:
        largura_bruta = float(request.args.get('largura', default_largura))
        refilo = float(request.args.get('refilo', 0))
    except ValueError:
        largura_bruta = default_largura
        refilo = 0

    # Calcula a largura utilizável
    largura_utilizavel = largura_bruta - refilo
    
    if largura_utilizavel <= 0:
        return abort(400, "Refilo não pode ser maior que a largura da chapa.")

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
    
    # --- INÍCIO DA NOVA LÓGICA ---

    # 1. Cria o otimizador com a largura utilizável
    otimizador = OtimizadorCorte1D(largura_utilizavel)
    
    # 2. Pede ao otimizador uma lista maior de padrões (ex: 100).
    #    Eles já vêm ordenados por desperdício e prioridade.
    todos_padroes = otimizador.gerar_padroes_otimizados(itens_grupo, top_n=100)
    
    # 3. Filtra a lista para manter apenas padrões que contêm o item selecionado
    padroes_filtrados = []
    codigo_selecionado = item_selecionado.item_code
    
    for padrao in todos_padroes:
        # Verifica se o item_code está na combinação do padrão
        item_encontrado = False
        for item, qty in padrao.combinacao:
            if item.item_code == codigo_selecionado:
                item_encontrado = True
                break  # Encontrou, pode parar de checar esta combinação
        
        if item_encontrado:
            padroes_filtrados.append(padrao)

    # 4. Pega os "Top 10" da lista já filtrada e ordenada
    top_padroes_finais = padroes_filtrados[:10]
    
    # --- FIM DA NOVA LÓGICA ---

    return render_template(
        'results.html',
        item_selecionado=item_selecionado,
        padroes=top_padroes_finais, # Passa a lista filtrada
        largura_chapa_bruta=largura_bruta,
        refilo=refilo,
        largura_chapa_utilizavel=largura_utilizavel,
        total_itens_grupo=len(itens_grupo)
    )