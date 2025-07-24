import re

def parse_from_string_to_numeric(valor_str):
    """
    Converte uma string no formato brasileiro (ex: '1.234,56') para float (1234.56).
    Remove espaços e caracteres especiais, corrige separadores de milhar e decimal.
    """
    if not isinstance(valor_str, str):
        valor_str = str(valor_str)

    valor_str = valor_str.strip().replace('\xa0', '')  # remove espaços não visíveis

    # Remove pontos que sejam separadores de milhar (antes de grupo de 3 dígitos)
    valor_str = re.sub(r'\.(?=\d{3}(?:\.|,|$))', '', valor_str)

    # Substitui vírgula decimal por ponto decimal
    valor_str = valor_str.replace(',', '.')

    try:
        return float(valor_str)
    except ValueError:
        return 0.0