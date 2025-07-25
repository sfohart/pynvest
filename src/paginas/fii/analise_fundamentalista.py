
import streamlit as st
import pandas as pd
from src.utils import parse_currency, parse_percent


@st.cache_data(show_spinner=False)
def analise_fundamentalista_avancada(ticker: str, dados_fundamentalistas: dict[str,any], pesos_ajustados: dict[str, float]):
    if not dados_fundamentalistas:
        return None
    
    preco = parse_currency(dados_fundamentalistas.get('valor_atual', 0))
    p_vp = float(dados_fundamentalistas.get('pvp', 0) or 0)
    dy = parse_percent(dados_fundamentalistas.get('dividend_yield_12m', 0))
    vacancia = 0.0  # não disponível, definir default
    patrimonio = parse_currency(dados_fundamentalistas.get('patrimonio_total', 0))
    n_cotistas = int(dados_fundamentalistas.get('numero_cotistas', 0) or 0)  # usando cotistas como proxy
    liquidez = parse_currency(dados_fundamentalistas.get('liquidez_media_diaria', 0))
    tx_adm = 0.0  # não disponível, default 0
    ultimo_rendimento = 0.0  # não disponível, default 0
    dy_cagr_3a = float(dados_fundamentalistas.get('dy_cagr_3y', 0) or 0)
    crescimento_div = dy_cagr_3a
    volatilidade = 0.0  # não disponível, default 0
    
    score_qualidade = calcular_score_qualidade(
        {
            'dy': dy * 100,
            'dy_cagr_3a': crescimento_div,
            'p_vp': p_vp,
            'vacancia': vacancia * 100,
            'volatilidade': volatilidade,
            'liquidez': liquidez,
            'n_cotistas': n_cotistas
        }, 
        pesos = pesos_ajustados)
    
    analise = {
        'Preço Atual (R$)': round(preco, 2),
        'P/VP': round(p_vp, 2),
        'DY (%)': round(dy * 100, 2),
        'DY CAGR (3a) (%)': round(dy_cagr_3a, 2),
        'Crescimento Dividendos (%)': round(crescimento_div, 2),
        'Vacância (%)': round(vacancia * 100, 2),
        'Patrimônio Líquido (R$ mi)': round(patrimonio / 1e6, 2),
        'Número de Ativos': n_cotistas,
        'Volatilidade Anual (%)': round(volatilidade, 2),
        'Liquidez Diária (R$)': round(liquidez, 2),
        'Taxa de Administração (%)': round(tx_adm * 100, 2),
        'Último Rendimento (R$)': round(ultimo_rendimento, 2),
        'Score Qualidade': round(score_qualidade, 1)
    }
    
    return pd.DataFrame.from_dict(analise, orient='index', columns=['Valor'])


def calcular_score_qualidade(fatores, pesos=dict[str,float]):
 
    
    # Normalização dos valores
    dy_norm = min(fatores['dy'] / 10, 1) if fatores['dy'] > 0 else 0  # Máx 10%
    crescimento_div_norm = max(-1, min(fatores['dy_cagr_3a'] / 20, 1))  # Entre -20% e +20%
    p_vp_norm = max(0, 1 - abs(1 - fatores['p_vp']) / 0.5)  # Ideal próximo a 1
    vacancia_norm = max(0, 1 - fatores['vacancia'] / 30)  # Máx 30%
    volatilidade_norm = max(0, 1 - fatores['volatilidade'] / 50)  # Máx 50%
    liquidez_norm = min(fatores['liquidez'] / 5e6, 1) if fatores['liquidez'] > 0 else 0  # Máx R$5mi
        
    # Cálculo do score
    score = (dy_norm * pesos['dy'] +
             crescimento_div_norm * pesos['dy_cagr_3a'] +
             p_vp_norm * pesos['p_vp'] +
             vacancia_norm * pesos['vacancia'] +
             volatilidade_norm * pesos['volatilidade'] +
             liquidez_norm * pesos['liquidez'])
    
    return score * 10  # Score de 0 a 10