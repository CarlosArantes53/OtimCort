# app/models.py
from dataclasses import dataclass
from typing import List, Tuple

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