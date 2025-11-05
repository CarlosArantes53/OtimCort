# app/database.py
import sqlite3
from typing import List
from .models import Item

# Nota: A conexão não é mais global. 
# É uma boa prática abrir e fechar conexões por transação.

def get_db_connection(db_path: str):
    """Conecta ao banco de dados"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def _row_to_item(row: sqlite3.Row) -> Item:
    """Converte uma linha do banco em um objeto Item"""
    return Item(
        item_code=row['ItemCode'],
        item_name=row['ItemName'],
        espessura=float(row['espessura']),
        desenvolvimento=float(row['desenvolvimento']),
        largura=float(row['largura']),
        estoque_atual=int(row['estoque_atual']),
        estoque_maximo=int(row['estoque_maximo']),
        demanda=int(row['demanda'])
    )

def get_all_items(db_path: str) -> List[Item]:
    """Busca todos os itens do banco"""
    conn = get_db_connection(db_path)
    rows = conn.execute('SELECT * FROM tbl_demanda').fetchall()
    conn.close()
    return [_row_to_item(row) for row in rows]

def get_items_by_dimensions(db_path: str, espessura: float, largura: float) -> List[Item]:
    """Busca itens com mesma espessura e largura"""
    conn = get_db_connection(db_path)
    rows = conn.execute(
        'SELECT * FROM tbl_demanda WHERE espessura = ? AND largura = ?',
        (espessura, largura)
    ).fetchall()
    conn.close()
    return [_row_to_item(row) for row in rows]

def get_item_by_code(db_path: str, item_code: str) -> Item | None:
    """Busca um item específico pelo código"""
    conn = get_db_connection(db_path)
    row = conn.execute('SELECT * FROM tbl_demanda WHERE ItemCode = ?', (item_code,)).fetchone()
    conn.close()
    
    if row:
        return _row_to_item(row)
    return None