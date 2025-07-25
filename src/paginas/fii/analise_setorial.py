import streamlit as st
import pandas as pd

from .coletar_dados_status_invest import obter_dados_fii
from .analise_fundamentalista import analise_fundamentalista_avancada

def analise_setorial(df_tickers_setor: pd.DataFrame, pesos_ajustados: dict[str, float]):
    """Compara FIIs do mesmo segmento"""
    if df_tickers_setor.empty:
        return None
    
    dados_setor = []
    total = df_tickers_setor.shape[0]
    progresso = st.progress(0, text="Analisando ativos...")

    for i, ticker in enumerate(df_tickers_setor['ticker'].values, 1):    
        dados = obter_dados_fii(ticker)
        if dados:
            analise = analise_fundamentalista_avancada(ticker,dados, pesos_ajustados)
            if analise is not None:
                df_analise = analise.T  # ✅ Transforma colunas em colunas da linha
                df_analise['setor'] = dados.get('setor','Desconhecido')
                df_analise['Ticker'] = ticker
                dados_setor.append(df_analise)

        progresso.progress(i / total, text=f"Analisando {ticker} ({i}/{total})")


    progresso.empty()
    
    if not dados_setor:
        return None
    
    df_setor = pd.concat(dados_setor)
    df_setor.set_index('Ticker', inplace=True)

    # Calcular rankings
    for col in df_setor.columns:
        if col not in ['Número de Ativos', 'Patrimônio Líquido (R$ mi)', 'setor']:
            try:

                df_setor[f'Rank {col}'] = df_setor[col].rank(ascending=False if '%' in col or 'DY' in col else True)
            except:
                continue

    return df_setor