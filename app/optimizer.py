# app/optimizer.py
import itertools
from typing import List
from .models import Item, PadraoCorte

class OtimizadorCorte1D:
    """Otimizador de corte 1D usando múltiplas estratégias"""
    
    def __init__(self, largura_chapa: float):
        self.largura_chapa = largura_chapa
        
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
            max_qty = int(self.largura_chapa / (item.desenvolvimento))
            
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
            qty_possivel = int(espaco_restante / item.desenvolvimento)
            
            if qty_possivel > 0:
                # Limita pela necessidade do item
                falta, pode_estocar = item.quantidade_necessaria
                qty_desejada = min(qty_possivel, falta + pode_estocar, 50)
                
                if qty_desejada > 0:
                    combinacao.append((item, qty_desejada))
                    espaco_usado = qty_desejada * item.desenvolvimento
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
                max_qty = int(espaco_restante / item.desenvolvimento)
                
                if max_qty > 0:
                    falta, pode_estocar = item.quantidade_necessaria
                    qty_limite = min(max_qty, falta + pode_estocar, 30)
                    
                    for qty in range(1, qty_limite + 1):
                        espaco_usado = qty * item.desenvolvimento
                        desperdicio_temp = espaco_restante - espaco_usado
                        
                        if desperdicio_temp < menor_desperdicio and desperdicio_temp >= 0:
                            menor_desperdicio = desperdicio_temp
                            melhor_item = item
                            melhor_qty = qty
            
            if melhor_item is None:
                break
            
            combinacao.append((melhor_item, melhor_qty))
            espaco_restante -= melhor_qty * melhor_item.desenvolvimento
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
        tamanho_total = quantidade * item.desenvolvimento
        
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
            espaco_usado1 = qty1 * item1.desenvolvimento
            if espaco_usado1 >= self.largura_chapa:
                break
            
            espaco_restante = self.largura_chapa - espaco_usado1
            max_qty2 = int(espaco_restante / item2.desenvolvimento)
            
            for qty2 in range(1, min(max_qty2 + 1, 15)):
                espaco_usado2 = qty2 * item2.desenvolvimento
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
            espaco1 = qty1 * item1.desenvolvimento
            if espaco1 >= self.largura_chapa:
                break
            
            for qty2 in range(1, 8):
                espaco2 = espaco1 + qty2 * item2.desenvolvimento
                if espaco2 >= self.largura_chapa:
                    break
                
                espaco_restante = self.largura_chapa - espaco2
                max_qty3 = int(espaco_restante / item3.desenvolvimento)
                
                for qty3 in range(1, min(max_qty3 + 1, 8)):
                    espaco3 = qty3 * item3.desenvolvimento
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
