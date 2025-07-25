
import pandas as pd
import numpy as np

import yfinance as yf
import fundamentus as fd

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

import plotly.graph_objects as go


def grafico_patrimonio_donut(total_investido, lucro_prejuizo, key=None, height_donut: int = 400):
    # Cores baseadas no tema atual
    if hasattr(st, 'theme') and st.theme is not None:
        tema = st.theme
        bg_color = tema.backgroundColor
        text_color = tema.textColor
        
        # Cores para o gráfico adaptadas ao tema
        if tema.base == 'dark':
            azul = '#1f77b4'  # Azul mais visível no escuro
            verde = '#2ca02c'  # Verde mais visível no escuro
            vermelho = '#d62728'  # Vermelho mais visível no escuro
        else:
            azul = '#4285F4'  # Azul do Material Design
            verde = '#0F9D58'  # Verde do Material Design
            vermelho = '#DB4437'  # Vermelho do Material Design
    else:
        # Fallback para tema claro
        bg_color = '#ffffff'
        text_color = '#31333f'
        azul = '#4285F4'
        verde = '#0F9D58'
        vermelho = '#DB4437'

    # Configuração dos dados do gráfico
    if lucro_prejuizo >= 0:
        labels = ["Total Investido", "Lucro"]
        values = [total_investido, lucro_prejuizo]
        colors = [azul, verde]
    else:
        labels = ["Total Investido", "Prejuízo"]
        values = [total_investido, abs(lucro_prejuizo)]
        colors = [azul, vermelho]

    # Criação do gráfico
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='inside',
        sort=False,
        direction='clockwise',
        showlegend=False,  # Removido para economizar espaço
        insidetextorientation='radial',
        hoverinfo='label+value+percent'
    )])

    # Formatação do valor monetário
    valor_total = total_investido + lucro_prejuizo
    valor_formatado = f'R$ {valor_total:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")

    # Layout final
    fig.update_layout(
        title_text="Distribuição do Patrimônio",
        annotations=[dict(
            text=valor_formatado,
            x=0.5, 
            y=0.5, 
            font_size=20, 
            font_color=text_color, 
            showarrow=False
        )],
        margin=dict(t=int(height_donut/8), b=int(height_donut/8), l=int(height_donut/8), r=int(height_donut/8)),
        height=height_donut,
        paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
        plot_bgcolor='rgba(0,0,0,0)',   # Fundo transparente
        font=dict(color=text_color)      # Cor do texto adaptada
    )

    return st.plotly_chart(fig, use_container_width=True, key=key)


def calcular_resumo_investimentos(df: pd.DataFrame):
    df = df.copy()

    total_investido_geral = 0
    total_valor_mercado = 0

    resumo = []

    for ticker in df["Ticker"].unique():
        df_ticker = df[df["Ticker"] == ticker]

        compras = df_ticker[df_ticker["Entrada/Saída"] == "Credito"]
        vendas = df_ticker[df_ticker["Entrada/Saída"] == "Debito"]

        qtd_comprada = compras["Quantidade"].sum()
        qtd_vendida = vendas["Quantidade"].sum()
        qtd_liquida = qtd_comprada - qtd_vendida

        if qtd_liquida <= 0:
            continue

        total_comprado = compras["Valor da Operação"].sum()
        total_vendido = vendas["Valor da Operação"].sum()
        total_investido = total_comprado - total_vendido

        preco_medio = (
            (compras["Quantidade"] * compras["Preço unitário"]).sum() / qtd_comprada
            if qtd_comprada > 0 else 0
        )

        try:
            preco_atual = yf.Ticker(ticker + ".SA").history(period="1d")["Close"].iloc[-1]
        except Exception:
            preco_atual = 0

        valor_mercado = preco_atual * qtd_liquida
        lucro_prejuizo = valor_mercado - total_investido

        total_investido_geral += total_investido
        total_valor_mercado += valor_mercado

        resumo.append({
            "Ticker": ticker,
            "Quantidade Atual": qtd_liquida,
            "Preço Médio": round(preco_medio, 2),
            "Preço Atual": round(preco_atual, 2),
            "Total Investido": round(total_investido, 2),
            "Valor de Mercado": round(valor_mercado, 2),
            "Lucro/Prejuízo": round(lucro_prejuizo, 2),
        })

    df_consolidacao = pd.DataFrame(resumo)
    df_consolidacao = df_consolidacao.sort_values(by=['Ticker'], ascending=True) if not df_consolidacao.empty else df_consolidacao

    lucro_total = total_valor_mercado - total_investido_geral
    delta = lucro_total / total_investido_geral if total_investido_geral > 0 else 0

    return {
        "consolidacao": df_consolidacao,
        "total_investido_geral": total_investido_geral,
        "total_valor_mercado": total_valor_mercado,
        "lucro_total": lucro_total,
        "delta": delta
    }



def criar_grafico_historico_precos(dados):
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

def exibir_resumo_investimentos(dict_consolidado: dict[str,any]):
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

    abas_resumo = st.tabs(["Minha Carteira", "Status por Ativo", "Histórico de Preços"])

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

    with abas_resumo[2]:
        tickers = ["Selecione"] + sorted(df_resumo_formatted["Ticker"].unique().tolist())
        ticker = st.selectbox("Escolha o ativo", tickers)


        if ticker != "Selecione":
            with st.spinner(f'Baixando histórico de preços do ticker {ticker}'):
                ticker_yf = ticker + ".SA"
                dados = yf.download(ticker_yf, period="6mo", interval="1d", group_by="ticker", threads=False)

                # Garantir que os dados estão em colunas simples
                if isinstance(dados.columns, pd.MultiIndex):
                    # Extrai a coluna corretamente se MultiIndex
                    dados.columns = dados.columns.get_level_values(1)

                # Tentativa alternativa sem o .SA, se vazio
                if dados.empty:
                    dados = yf.download(ticker, period="6mo", interval="1d", group_by="ticker", threads=False)
                    if isinstance(dados.columns, pd.MultiIndex):
                        dados.columns = dados.columns.get_level_values(1)

                if dados.empty or "Close" not in dados.columns:
                    st.warning(f"Nenhum dado encontrado para {ticker_yf} ou {ticker}.")
                    return
                
                dados.index = pd.to_datetime(dados.index)
                dados = dados[~dados.index.duplicated(keep='first')]  

                # Reindexar para dias úteis contínuos (evita gaps estranhos)
                idx = pd.date_range(start=dados.index.min(), end=dados.index.max(), freq='B')
                dados = dados.reindex(idx)

                dados = dados.dropna(subset=['Open', 'High', 'Low', 'Close'])
                fig_historico_precos = criar_grafico_historico_precos(dados)
                st.plotly_chart(fig_historico_precos, use_container_width=True, key='fig_historico_precos')
        else:
            st.session_state['fig_historico_precos'] = None