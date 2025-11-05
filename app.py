# app.py
from flask import Flask, render_template, request, jsonify
import sqlite3
from dataclasses import dataclass
from typing import List, Tuple
import itertools
from collections import defaultdict

app = Flask(__name__)

# Configuração
LARGURA_CHAPA_PADRAO = 6000  # mm - pode ser alterado

@dataclass
class Item:
    item_code: str
    item_name: str
    espessura: float
    desenvolvimento: float
    largura: float
    estoque_atual: int
    estoque_maximo: int
    demanda: int
    
    @property
    def prioridade(self):
        """Calcula prioridade baseada na necessidade"""
        if self.demanda > self.estoque_atual:
            return 10  # Alta prioridade - necessário
        else:
            return 1   # Baixa prioridade - apenas estoque
    
    @property
    def quantidade_necessaria(self):
        """Quantidade que precisa ser produzida"""
        falta = max(0, self.demanda - self.estoque_atual)
        pode_estocar = max(0, self.estoque_maximo - self.estoque_atual - falta)
        return falta, pode_estocar

@dataclass
class PadraoCorte:
    combinacao: List[Tuple[Item, int]]  # (Item, quantidade)
    desperdicio: float
    utilizacao_percentual: float
    score_prioridade: int
    largura_chapa: float
    
    def __repr__(self):
        return f"Padrão(desp={self.desperdicio}mm, util={self.utilizacao_percentual:.1f}%, prior={self.score_prioridade})"


class OtimizadorCorte1D:
    """Otimizador de corte 1D usando múltiplas estratégias"""
    
    def __init__(self, largura_chapa: float):
        self.largura_chapa = largura_chapa
        self.margem_corte = 5  # mm - margem de segurança entre cortes
        
    def gerar_padroes_otimizados(self, itens: List[Item], top_n: int = 10) -> List[PadraoCorte]:
        """Gera os top N padrões de corte otimizados"""
        
        # Gera múltiplos padrões usando diferentes estratégias
        todos_padroes = []
        
        # Estratégia 1: First-Fit Decreasing - Maior primeiro
        todos_padroes.extend(self._gerar_padroes_ffd(itens, max_padroes=50))
        
        # Estratégia 2: Prioridade Alta primeiro
        todos_padroes.extend(self._gerar_padroes_prioridade(itens, max_padroes=50))
        
        # Estratégia 3: Best-Fit - Menor desperdício
        todos_padroes.extend(self._gerar_padroes_best_fit(itens, max_padroes=50))
        
        # Estratégia 4: Combinações específicas
        todos_padroes.extend(self._gerar_combinacoes_especificas(itens, max_padroes=100))
        
        # Remove duplicatas e ordena
        padroes_unicos = self._remover_duplicatas(todos_padroes)
        padroes_ordenados = self._ordenar_padroes(padroes_unicos)
        
        return padroes_ordenados[:top_n]
    
    def _gerar_padroes_ffd(self, itens: List[Item], max_padroes: int) -> List[PadraoCorte]:
        """First-Fit Decreasing: ordena por tamanho e tenta encaixar"""
        padroes = []
        itens_ordenados = sorted(itens, key=lambda x: x.desenvolvimento, reverse=True)
        
        for _ in range(min(max_padroes, 20)):
            padrao = self._construir_padrao_greedy(itens_ordenados)
            if padrao:
                padroes.append(padrao)
        
        return padroes
    
    def _gerar_padroes_prioridade(self, itens: List[Item], max_padroes: int) -> List[PadraoCorte]:
        """Prioriza itens com maior necessidade"""
        padroes = []
        
        # Ordena por prioridade e depois por tamanho
        itens_ordenados = sorted(itens, key=lambda x: (-x.prioridade, -x.desenvolvimento))
        
        for _ in range(min(max_padroes, 20)):
            padrao = self._construir_padrao_greedy(itens_ordenados)
            if padrao:
                padroes.append(padrao)
        
        return padroes
    
    def _gerar_padroes_best_fit(self, itens: List[Item], max_padroes: int) -> List[PadraoCorte]:
        """Best-Fit: tenta minimizar desperdício em cada passo"""
        padroes = []
        
        for _ in range(min(max_padroes, 20)):
            padrao = self._construir_padrao_best_fit(itens)
            if padrao:
                padroes.append(padrao)
        
        return padroes
    
    def _gerar_combinacoes_especificas(self, itens: List[Item], max_padroes: int) -> List[PadraoCorte]:
        """Gera combinações específicas explorando espaço de soluções"""
        padroes = []
        
        # Limita número de itens para evitar explosão combinatória
        n_itens = min(len(itens), 8)
        itens_principais = itens[:n_itens]
        
        # Tenta diferentes quantidades de cada item
        for item in itens_principais:
            max_qty = int(self.largura_chapa / (item.desenvolvimento + self.margem_corte))
            
            # Padrão com apenas este item
            for qty in range(1, min(max_qty + 1, 20)):
                padrao = self._criar_padrao_simples(item, qty)
                if padrao:
                    padroes.append(padrao)
            
            # Combinações com outros itens
            for outro_item in itens_principais:
                if outro_item.item_code != item.item_code:
                    padroes.extend(self._gerar_combinacoes_dois_itens(item, outro_item))
        
        # Combinações de 3 itens
        if len(itens_principais) >= 3:
            for combo in itertools.combinations(itens_principais, 3):
                padroes.extend(self._gerar_combinacao_tres_itens(list(combo)))
        
        return padroes[:max_padroes]
    
    def _construir_padrao_greedy(self, itens: List[Item]) -> PadraoCorte:
        """Constrói padrão usando abordagem greedy"""
        espaco_restante = self.largura_chapa
        combinacao = []
        score_prioridade = 0
        
        for item in itens:
            # Tenta adicionar o máximo deste item
            tamanho_com_margem = item.desenvolvimento + self.margem_corte
            qty_possivel = int(espaco_restante / tamanho_com_margem)
            
            if qty_possivel > 0:
                # Limita pela necessidade do item
                falta, pode_estocar = item.quantidade_necessaria
                qty_desejada = min(qty_possivel, falta + pode_estocar, 50)
                
                if qty_desejada > 0:
                    combinacao.append((item, qty_desejada))
                    espaco_usado = qty_desejada * tamanho_com_margem
                    espaco_restante -= espaco_usado
                    score_prioridade += item.prioridade * qty_desejada
        
        if not combinacao:
            return None
        
        desperdicio = espaco_restante
        utilizacao = ((self.largura_chapa - desperdicio) / self.largura_chapa) * 100
        
        return PadraoCorte(
            combinacao=combinacao,
            desperdicio=desperdicio,
            utilizacao_percentual=utilizacao,
            score_prioridade=score_prioridade,
            largura_chapa=self.largura_chapa
        )
    
    def _construir_padrao_best_fit(self, itens: List[Item]) -> PadraoCorte:
        """Constrói padrão tentando minimizar desperdício em cada passo"""
        espaco_restante = self.largura_chapa
        combinacao = []
        score_prioridade = 0
        
        itens_disponiveis = itens.copy()
        
        while itens_disponiveis and espaco_restante > 0:
            melhor_item = None
            melhor_qty = 0
            menor_desperdicio = float('inf')
            
            # Para cada item, encontra a quantidade que minimiza desperdício
            for item in itens_disponiveis:
                tamanho_com_margem = item.desenvolvimento + self.margem_corte
                max_qty = int(espaco_restante / tamanho_com_margem)
                
                if max_qty > 0:
                    falta, pode_estocar = item.quantidade_necessaria
                    qty_limite = min(max_qty, falta + pode_estocar, 30)
                    
                    for qty in range(1, qty_limite + 1):
                        espaco_usado = qty * tamanho_com_margem
                        desperdicio_temp = espaco_restante - espaco_usado
                        
                        if desperdicio_temp < menor_desperdicio and desperdicio_temp >= 0:
                            menor_desperdicio = desperdicio_temp
                            melhor_item = item
                            melhor_qty = qty
            
            if melhor_item is None:
                break
            
            combinacao.append((melhor_item, melhor_qty))
            espaco_restante -= melhor_qty * (melhor_item.desenvolvimento + self.margem_corte)
            score_prioridade += melhor_item.prioridade * melhor_qty
            itens_disponiveis.remove(melhor_item)
        
        if not combinacao:
            return None
        
        desperdicio = espaco_restante
        utilizacao = ((self.largura_chapa - desperdicio) / self.largura_chapa) * 100
        
        return PadraoCorte(
            combinacao=combinacao,
            desperdicio=desperdicio,
            utilizacao_percentual=utilizacao,
            score_prioridade=score_prioridade,
            largura_chapa=self.largura_chapa
        )
    
    def _criar_padrao_simples(self, item: Item, quantidade: int) -> PadraoCorte:
        """Cria padrão com apenas um tipo de item"""
        tamanho_total = quantidade * (item.desenvolvimento + self.margem_corte)
        
        if tamanho_total > self.largura_chapa:
            return None
        
        desperdicio = self.largura_chapa - tamanho_total
        utilizacao = (tamanho_total / self.largura_chapa) * 100
        score_prioridade = item.prioridade * quantidade
        
        return PadraoCorte(
            combinacao=[(item, quantidade)],
            desperdicio=desperdicio,
            utilizacao_percentual=utilizacao,
            score_prioridade=score_prioridade,
            largura_chapa=self.largura_chapa
        )
    
    def _gerar_combinacoes_dois_itens(self, item1: Item, item2: Item) -> List[PadraoCorte]:
        """Gera combinações de dois itens diferentes"""
        padroes = []
        
        for qty1 in range(1, 15):
            espaco_usado1 = qty1 * (item1.desenvolvimento + self.margem_corte)
            if espaco_usado1 >= self.largura_chapa:
                break
            
            espaco_restante = self.largura_chapa - espaco_usado1
            max_qty2 = int(espaco_restante / (item2.desenvolvimento + self.margem_corte))
            
            for qty2 in range(1, min(max_qty2 + 1, 15)):
                espaco_usado2 = qty2 * (item2.desenvolvimento + self.margem_corte)
                desperdicio = espaco_restante - espaco_usado2
                
                if desperdicio >= 0:
                    utilizacao = ((espaco_usado1 + espaco_usado2) / self.largura_chapa) * 100
                    score_prioridade = (item1.prioridade * qty1) + (item2.prioridade * qty2)
                    
                    padroes.append(PadraoCorte(
                        combinacao=[(item1, qty1), (item2, qty2)],
                        desperdicio=desperdicio,
                        utilizacao_percentual=utilizacao,
                        score_prioridade=score_prioridade,
                        largura_chapa=self.largura_chapa
                    ))
        
        return padroes
    
    def _gerar_combinacao_tres_itens(self, itens: List[Item]) -> List[PadraoCorte]:
        """Gera combinações de três itens"""
        padroes = []
        
        if len(itens) < 3:
            return padroes
        
        item1, item2, item3 = itens[0], itens[1], itens[2]
        
        for qty1 in range(1, 8):
            espaco1 = qty1 * (item1.desenvolvimento + self.margem_corte)
            if espaco1 >= self.largura_chapa:
                break
            
            for qty2 in range(1, 8):
                espaco2 = espaco1 + qty2 * (item2.desenvolvimento + self.margem_corte)
                if espaco2 >= self.largura_chapa:
                    break
                
                espaco_restante = self.largura_chapa - espaco2
                max_qty3 = int(espaco_restante / (item3.desenvolvimento + self.margem_corte))
                
                for qty3 in range(1, min(max_qty3 + 1, 8)):
                    espaco3 = qty3 * (item3.desenvolvimento + self.margem_corte)
                    desperdicio = espaco_restante - espaco3
                    
                    if desperdicio >= 0:
                        utilizacao = ((espaco2 + espaco3) / self.largura_chapa) * 100
                        score_prioridade = (item1.prioridade * qty1 + 
                                          item2.prioridade * qty2 + 
                                          item3.prioridade * qty3)
                        
                        padroes.append(PadraoCorte(
                            combinacao=[(item1, qty1), (item2, qty2), (item3, qty3)],
                            desperdicio=desperdicio,
                            utilizacao_percentual=utilizacao,
                            score_prioridade=score_prioridade,
                            largura_chapa=self.largura_chapa
                        ))
        
        return padroes
    
    def _remover_duplicatas(self, padroes: List[PadraoCorte]) -> List[PadraoCorte]:
        """Remove padrões duplicados"""
        padroes_unicos = []
        assinaturas_vistas = set()
        
        for padrao in padroes:
            # Cria assinatura única do padrão
            assinatura = tuple(sorted([
                (item.item_code, qty) for item, qty in padrao.combinacao
            ]))
            
            if assinatura not in assinaturas_vistas:
                assinaturas_vistas.add(assinatura)
                padroes_unicos.append(padrao)
        
        return padroes_unicos
    
    def _ordenar_padroes(self, padroes: List[PadraoCorte]) -> List[PadraoCorte]:
        """Ordena padrões por desperdício (crescente) e prioridade (decrescente)"""
        return sorted(padroes, key=lambda p: (p.desperdicio, -p.score_prioridade))


def get_db_connection():
    """Conecta ao banco de dados"""
    conn = sqlite3.connect("C://Users//carlos.eduardo//Desktop//Automation-Power-BI-schedular//database//processo.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_all_items() -> List[Item]:
    """Busca todos os itens do banco"""
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM tbl_demanda').fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append(Item(
            item_code=row['ItemCode'],
            item_name=row['ItemName'],
            espessura=float(row['espessura']),
            desenvolvimento=float(row['desenvolvimento']),
            largura=float(row['largura']),
            estoque_atual=int(row['estoque_atual']),
            estoque_maximo=int(row['estoque_maximo']),
            demanda=int(row['demanda'])
        ))
    
    return items


def get_items_by_dimensions(espessura: float, largura: float) -> List[Item]:
    """Busca itens com mesma espessura e largura"""
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM tbl_demanda WHERE espessura = ? AND largura = ?',
        (espessura, largura)
    ).fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append(Item(
            item_code=row['ItemCode'],
            item_name=row['ItemName'],
            espessura=float(row['espessura']),
            desenvolvimento=float(row['desenvolvimento']),
            largura=float(row['largura']),
            estoque_atual=int(row['estoque_atual']),
            estoque_maximo=int(row['estoque_maximo']),
            demanda=int(row['demanda'])
        ))
    
    return items


@app.route('/')
def index():
    """Página inicial com lista de itens"""
    items = get_all_items()
    
    # Agrupa por dimensões para visualização
    grupos = defaultdict(list)
    for item in items:
        chave = (item.espessura, item.largura)
        grupos[chave].append(item)
    
    return render_template('index.html', 
                         items=items, 
                         largura_chapa=LARGURA_CHAPA_PADRAO,
                         grupos=grupos)


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Endpoint para configurar largura da chapa"""
    global LARGURA_CHAPA_PADRAO
    
    if request.method == 'POST':
        data = request.get_json()
        nova_largura = data.get('largura_chapa')
        if nova_largura and nova_largura > 0:
            LARGURA_CHAPA_PADRAO = nova_largura
            return jsonify({'success': True, 'largura_chapa': LARGURA_CHAPA_PADRAO})
        return jsonify({'success': False, 'error': 'Largura inválida'}), 400
    
    return jsonify({'largura_chapa': LARGURA_CHAPA_PADRAO})


@app.route('/otimizar/<item_code>')
def otimizar(item_code):
    """Otimiza corte para um item selecionado"""
    # Busca o item selecionado
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM tbl_demanda WHERE ItemCode = ?', (item_code,)).fetchone()
    conn.close()
    
    if not row:
        return "Item não encontrado", 404
    
    item_selecionado = Item(
        item_code=row['ItemCode'],
        item_name=row['ItemName'],
        espessura=float(row['espessura']),
        desenvolvimento=float(row['desenvolvimento']),
        largura=float(row['largura']),
        estoque_atual=int(row['estoque_atual']),
        estoque_maximo=int(row['estoque_maximo']),
        demanda=int(row['demanda'])
    )
    
    # Busca todos os itens com mesma espessura e largura
    itens_grupo = get_items_by_dimensions(item_selecionado.espessura, item_selecionado.largura)
    
    # Executa otimização
    otimizador = OtimizadorCorte1D(LARGURA_CHAPA_PADRAO)
    top_padroes = otimizador.gerar_padroes_otimizados(itens_grupo, top_n=10)
    
    return render_template('results.html',
                         item_selecionado=item_selecionado,
                         padroes=top_padroes,
                         largura_chapa=LARGURA_CHAPA_PADRAO,
                         total_itens_grupo=len(itens_grupo))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
