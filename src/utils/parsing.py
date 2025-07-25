import re
import pandas as pd

def parse_from_string_to_numeric(valor_str):
    """
    Converte uma string brasileira (ex: '1.234,56') para float (1234.56).
    Funciona também com números sem milhar: '4,84' -> 4.84
    """
    if not isinstance(valor_str, str):
        valor_str = str(valor_str)

    valor_str = valor_str.strip().replace('\xa0', '').replace('R$', '').replace('%', '')
    
    # Remove todos os pontos que não sejam seguidos de 2 dígitos (provável decimal)
    if ',' in valor_str:
        # Se tiver vírgula, é decimal → remove todos os pontos
        valor_str = valor_str.replace('.', '')
        valor_str = valor_str.replace(',', '.') 
    else:
        # Se não tiver vírgula, pode estar no formato já correto
        valor_str = valor_str.replace(',', '')

    try:
        return float(valor_str)
    except ValueError:
        return 0.0
    
# Função auxiliar para converter valores percentuais
def parse_percent(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace('%', '').replace('.', '').replace(',', '.')
        try:
            return float(value) / 100
        except:
            return 0.0
    return float(value)

# Função auxiliar para converter valores monetários
def parse_currency(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
        try:
            return float(value)
        except:
            return 0.0
    return float(value)
