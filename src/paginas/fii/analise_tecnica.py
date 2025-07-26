import streamlit as st
import pandas as pd

import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots

from .coletar_dados_status_invest import obter_dados_fii

from analises import (
    calcular_media_movel,
    mostrar_analise_media_movel,
    calcular_rsi,
    mostrar_analise_rsi,
    calcular_bandas_bollinger,
    mostrar_analise_bandas_bollinger,
    calcular_macd,
    mostrar_analise_macd,
    criar_grafico_historico_precos
)


def exibir_analise_tecnica(
        carteira: list[str],
        media_movel: bool = True,
        rsi: bool = True,
        bandas_bollinger: bool = True,
        macd: bool = True):
    
    """
    Visualização interativa da análise técnica com Plotly e tema dinâmico.
    Organiza gráficos e explicações em abas, com links para referências.
    """

    opcoes = ["Selecione"] + sorted(carteira)
    ticker = st.selectbox("Selecione o FII para análise técnica:", opcoes, key="fii_tecnica")

    # 1. Seletor de período
    periodo = st.radio(
        "Período de Análise:",
        options=["1 mês", "3 meses", "6 meses", "1 ano", "Máximo"],
        index=2,  # 6M como padrão
        horizontal=True,
        help="Selecione o período histórico para análise"
    )

    if not ticker or ticker == 'Selecione':
        st.info('Nenhuma análise disponível para exibição')
        return    

    with st.spinner(f'Analisando os dados históricos do Ticker {ticker}'):
        try:
            dados = obter_dados_fii(ticker)  # dicionário com ['mercado']['hist_precos']
            if (dados is not None) and ('mercado' in dados.keys()) and ('hist_precos' in dados['mercado'].keys()):
                df_historico_precos = dados['mercado']['hist_precos']   
        except Exception as e:
            st.error(f"Erro ao obter análise técnica para {ticker}: {str(e)}")
            return

        if df_historico_precos.empty:
            st.warning("Sem dados disponíveis para análise técnica.")
            return
        
        # Mapeamento para o parâmetro do Yahoo Finance
        period_map = {
            "1 mês": 30,
            "3 meses": 90,
            "6 meses": 180,
            "1 ano": 365,
            "Máximo": None
        }

        dados_analise = df_historico_precos.copy()
                    
        # Aplicar o período selecionado (se não for o máximo)
        if periodo != "Máximo":
            dias = period_map[periodo]
            start_date = pd.Timestamp.now(tz="America/Sao_Paulo") - pd.Timedelta(days=dias)
            dados_analise = dados_analise[dados_analise.index >= start_date]
        
        if media_movel:
            dados_analise = calcular_media_movel(dados_analise)            

        if rsi:
            dados_analise = calcular_rsi(dados_analise)

        if bandas_bollinger:
            dados_analise = calcular_bandas_bollinger(dados_analise)

        if macd:
            dados_analise = calcular_macd(dados_analise)
            

        # Detectar tema para cores dinâmicas
        tema = None
        try:
            tema = st.runtime.scriptrunner.script_run_context.get_script_run_ctx().session_info.session.app_session._main_dg._theme
        except Exception:
            pass

        text_color = tema.get("textColor", "#000000") if tema else "#000000"
        grid_color = "#444" if (tema and tema.get("base") == "dark") else "#ccc"

        col_grafico, col_analises = st.columns(2)
        with col_grafico:
            criar_grafico_historico_precos(dados_analise, sma=media_movel, bollinger=bandas_bollinger)
        with col_analises:

            # Criar abas
            abas = st.tabs(["Preço e Bandas de Bollinger", "RSI e MACD"])

            # Aba 1: Preço, Médias e Bandas
            with abas[0]:
                col_media_movel, col_bandas_bollinger = st.columns(2)
                with col_media_movel:
                    mostrar_analise_media_movel(dados_analise)

                with col_bandas_bollinger:
                    mostrar_analise_bandas_bollinger(dados_analise)

                # st.markdown(f"""
                #     **Bandas de Bollinger:** indicam volatilidade e possíveis pontos de reversão.  
                #     --- 
                #     <a href="https://www.investopedia.com/terms/b/bollingerbands.asp" target="_blank" style="color:#1E90FF;">Veja mais</a> na Investopedia.
                
                # """)
                st.markdown(f"""
                    **Bandas de Bollinger:** indicam volatilidade e possíveis pontos de reversão. 
                    Veja [Investopedia - Bollinger Bands](https://www.investopedia.com/terms/b/bollingerbands.asp) para mais detalhes.
                    """)

            # Aba 2: RSI e MACD
            with abas[1]:
                col_rsi, col_macd = st.columns(2)
                with col_rsi:
                    mostrar_analise_rsi(dados_analise)

                with col_macd:
                    mostrar_analise_macd(dados_analise)

                st.markdown(f"""
                    **RSI (Índice de Força Relativa):** indica condições de sobrecompra (acima de 70) ou sobrevenda (abaixo de 30).  
                    Veja [Investopedia - RSI](https://www.investopedia.com/terms/r/rsi.asp) para mais detalhes.

                    ---

                    **MACD (Moving Average Convergence Divergence):** mostra momentum e cruzamentos de média móvel para indicar mudanças de tendência.  
                    Veja [Investopedia - MACD](https://www.investopedia.com/terms/m/macd.asp) para mais informações.
                    """)
