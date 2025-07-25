import streamlit as st
import yfinance as yf

import plotly.graph_objects as go

import pandas as pd

from ..commons import calcular_resumo_investimentos, grafico_patrimonio_donut
from .analise_tecnica import analise_tecnica, exibir_analise_tecnica


def grafico_historico_precos_fii(dados):
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dados.index,
        open=dados['Open'],
        high=dados['High'],
        low=dados['Low'],
        close=dados['Close'],
        name='Preço',
        increasing_line_color='#2ecc71',
        decreasing_line_color='#e74c3c'
    ))
    
    # Adicionar indicadores
    if 'SMA_curta' in dados.columns:
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['SMA_curta'],
            name='SMA 20',
            line=dict(color='#f39c12', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['SMA_longa'],
            name='SMA 50', 
            line=dict(color='#3498db', width=2)
        ))
    
    if 'Banda_Superior' in dados.columns:
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['Banda_Superior'],
            name='B. Superior',
            line=dict(color='#e74c3c', width=1, dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['Banda_Inferior'],
            name='B. Inferior',
            line=dict(color='#2ecc71', width=1, dash='dot')
        ))
    
    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=40, l=40, r=40, b=40),
        hovermode="x unified"
    )
    
    return fig


def exibir_resumo_investimentos_fii(dict_consolidado: dict[str,any]):
    df_resumo = dict_consolidado['consolidacao']    
    total_investido_geral = dict_consolidado["total_investido_geral"]
    lucro_total = dict_consolidado["lucro_total"]
    delta = dict_consolidado["delta"]

    # Formatar colunas numéricas para string em pt-BR com 2 casas decimais
    df_resumo_formatted = df_resumo.copy()
    cols_moeda = ["Preço Médio", "Preço Atual", "Total Investido", "Valor de Mercado", "Lucro/Prejuízo"]

    if not df_resumo_formatted.empty:
        for col in cols_moeda:
            df_resumo_formatted[col] = df_resumo_formatted[col].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

    abas_resumo = st.tabs([
        "Minha Carteira", 
        "Status por Ativo", 
        #"Histórico de Preços"
        ])

    with abas_resumo[0]:
        st.subheader("Minha Carteira")
        st.warning("""
                    ##### Atenção:
                
                Os valores obtidos como *Preço Atual* e *Valor de Mercado* são extraídos com base no valor
                mais recente do ativo disponível no *Yahoo Finance*.
                """)

        col1, col2 = st.columns(2)
        col1.metric("Total Investido", f"R$ {total_investido_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Lucro/Prejuízo Total", f"R$ {lucro_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{delta:.2%}")

        grafico_patrimonio_donut(total_investido_geral, lucro_total, 'patrimonio_geral')
    
    with abas_resumo[1]:
        with st.expander('#### Investimentos', expanded=False):
            st.dataframe(df_resumo_formatted, use_container_width=True)    

        for _, row in df_resumo.iterrows():
            with st.container(border=True):
                col_donut, col_info = st.columns([1, 2])
                with col_donut:
                    grafico_patrimonio_donut(
                        row['Total Investido'], 
                        row['Lucro/Prejuízo'], 
                        key=f"donut_{row['Ticker']}",
                        height_donut=300
                    )

                with col_info:
                    st.markdown(f"### {row['Ticker']}")            
                    col_qtde, col_medio, col_atual, col_lucro = st.columns(4)
                    col_qtde.metric("Quantidade", f"{row['Quantidade Atual']:,.0f}")
                    col_medio.metric("Preço Médio", f"R$ {row['Preço Médio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    col_atual.metric("Preço Atual", f"R$ {row['Preço Atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))                
                    col_lucro.metric("Lucro/Prejuízo", 
                            f"R$ {row['Lucro/Prejuízo']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                            f"{row['Lucro/Prejuízo']/row['Total Investido']:.2%}" if row['Total Investido'] > 0 else "0%")

    # with abas_resumo[2]:
    #     tickers = ["Selecione"] + sorted(df_resumo_formatted["Ticker"].unique().tolist())
    #     ticker = st.selectbox("Escolha o ativo", tickers)


    #     if ticker != "Selecione":
    #         with st.spinner(f'Baixando histórico de preços do ticker {ticker}'):
    #             ticker_yf = ticker + ".SA"
    #             dados = yf.download(ticker_yf, period="6mo", interval="1d", group_by="ticker", threads=False)

    #             # Garantir que os dados estão em colunas simples
    #             if isinstance(dados.columns, pd.MultiIndex):
    #                 # Extrai a coluna corretamente se MultiIndex
    #                 dados.columns = dados.columns.get_level_values(1)

    #             # Tentativa alternativa sem o .SA, se vazio
    #             if dados.empty:
    #                 dados = yf.download(ticker, period="6mo", interval="1d", group_by="ticker", threads=False)
    #                 if isinstance(dados.columns, pd.MultiIndex):
    #                     dados.columns = dados.columns.get_level_values(1)

    #             if dados.empty or "Close" not in dados.columns:
    #                 st.warning(f"Nenhum dado encontrado para {ticker_yf} ou {ticker}.")
    #                 return
                
    #             dados.index = pd.to_datetime(dados.index)
    #             dados = dados[~dados.index.duplicated(keep='first')]  

    #             # Reindexar para dias úteis contínuos (evita gaps estranhos)
    #             idx = pd.date_range(start=dados.index.min(), end=dados.index.max(), freq='B')
    #             dados = dados.reindex(idx)

    #             dados = dados.dropna(subset=['Open', 'High', 'Low', 'Close'])
    #             fig_historico_precos = grafico_historico_precos_fii(dados)
    #             st.plotly_chart(fig_historico_precos, use_container_width=True, key='fig_historico_precos')
    #     else:
    #         st.session_state['fig_historico_precos'] = None