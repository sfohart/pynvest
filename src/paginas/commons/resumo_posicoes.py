
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


