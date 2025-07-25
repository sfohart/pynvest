import streamlit as st
import pandas as pd



import plotly.graph_objects as go

from .coletar_dados_status_invest import obter_dados_fii
from .analise_fundamentalista import analise_fundamentalista_avancada


from ..commons import (
    detectar_tema_streamlit, 
    obter_tema_streamlit,
    exibir_resumo_investimentos
)

# Detecta e aplica o tema
detectar_tema_streamlit()
tema = obter_tema_streamlit()

#@st.cache_data(show_spinner=False)
def modelo_decisao_fii(ticker: str, pesos_indicadores: dict[str,float]):
    """Modelo de decisão com fallback seguro"""
    dados = obter_dados_fii(ticker)
    if not dados:
        return None
    
    try:
        analise_fund = analise_fundamentalista_avancada(ticker, dados, pesos_indicadores)
        if analise_fund is None or analise_fund.empty:
            return None
            
        # Cálculo simplificado da pontuação se a análise completa falhar
        try:
            dy = analise_fund.loc['DY (%)', 'Valor']
            p_vp = analise_fund.loc['P/VP', 'Valor']
            score = analise_fund.loc['Score Qualidade', 'Valor']
            
            # Pontuação baseada em critérios simples
            pontuacao = (dy * pesos_indicadores['dy']) + \
                ((1/p_vp) * pesos_indicadores['p_vp'] if p_vp > 0 else 0) + \
                (score)
            pontuacao = min(100, max(0, pontuacao))  # Garante entre 0 e 100
            
            recomendacao = (
                'COMPRA FORTE' if pontuacao > 80 else
                'COMPRA' if pontuacao > 60 else
                'NEUTRO' if pontuacao > 40 else
                'VENDA' if pontuacao > 20 else
                'VENDA FORTE'
            )
            
            return {
                'Pontuação': f"{pontuacao:.1f}%",
                'Recomendação': recomendacao,
                'Análise Fundamentalista': analise_fund
            }
        except:
            # Fallback básico se o cálculo falhar
            return {
                'Pontuação': "0%",
                'Recomendação': "N/A",
                'Análise Fundamentalista': analise_fund
            }
    except Exception as e:
        print(f"Erro no modelo de decisão para {ticker}: {str(e)}")
        return None
    
def painel_monitoramento(carteira: list[str], pesos_indicadores: dict[str,float]):
    """Cria painel com barra de progresso"""
    dados = []
    total = len(carteira)
    progresso = st.progress(0, text="Analisando ativos...")

    for i, ticker in enumerate(carteira, 1):
        try:
            resultado = modelo_decisao_fii(ticker, pesos_indicadores)
            if resultado and not resultado['Análise Fundamentalista'].empty:
                row = {
                    'Ticker': ticker,
                    'Preço': resultado['Análise Fundamentalista'].loc['Preço Atual (R$)', 'Valor'],
                    'DY (%)': resultado['Análise Fundamentalista'].loc['DY (%)', 'Valor'],
                    'P/VP': resultado['Análise Fundamentalista'].loc['P/VP', 'Valor'],
                    'Score': resultado['Análise Fundamentalista'].loc['Score Qualidade', 'Valor'],
                    'Recomendação': resultado['Recomendação']
                }

                if 'Pontuação' in resultado:
                    row['Pontuação'] = float(resultado['Pontuação'].replace('%', ''))

                dados.append(row)
        except Exception as e:
            st.warning(f"Erro ao processar {ticker} durante a construção do painel de monitoramento de FIIs: {str(e)}")
        
        progresso.progress(i / total, text=f"Analisando {ticker} ({i}/{total})")

    progresso.empty()  # Remove barra ao final

    if not dados:
        st.error("Nenhum dado válido foi coletado")
        return pd.DataFrame()
    
    df_painel = pd.DataFrame(dados)
    
    if 'Pontuação' not in df_painel.columns:
        df_painel['Pontuação'] = 0
    
    if not df_painel.empty:
        df_painel = df_painel.sort_values('Pontuação', ascending=False)
    
    return df_painel

def exibir_painel_monitoramento(df_painel: pd.DataFrame):
    if df_painel.empty:
        st.warning("Nenhum dado disponível para plotar gráficos")
        return

    
    tema_escuro = tema == "dark"
    template_plotly = "plotly_dark" if tema_escuro else "plotly_white"

    # Cores para texto e anotações
    bg_color = 'rgba(0,0,0,0)'
    text_color = '#FFF' if tema_escuro else '#000'
    annotation_bgcolor = '#333' if tema_escuro else '#FFF'

    # Cores por recomendação
    cores_recomendacao = {
        'COMPRA FORTE': '#006400' if tema_escuro else 'darkgreen',
        'COMPRA': '#32CD32' if tema_escuro else 'limegreen',
        'NEUTRO': '#BDB76B' if tema_escuro else 'gold',
        'VENDA': '#FF6347' if tema_escuro else 'tomato',
        'VENDA FORTE': '#8B0000' if tema_escuro else 'darkred',
        'N/A': '#808080'
    }

    def cor_por_recomendacao(r):
        return cores_recomendacao.get(r, '#007bff')

    tabs = st.tabs([        
        "Dividend Yield (%)",
        "Preço sobre Valor Patrimonial (P/VP)",
        "Score de Qualidade",
        "Pontuação Total"
    ])


    # 1. DY
    with tabs[0]:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_painel['Ticker'],
            y=df_painel['DY (%)'],
            marker_color=[cor_por_recomendacao(r) for r in df_painel['Recomendação']],
            text=[f"{v:.1f}%" for v in df_painel['DY (%)']],
            textposition='outside'
        ))
        fig.add_hline(
            y=6, line_dash="dash", line_color="red",
            annotation_text="DY Mínimo Desejável",
            annotation_position="top left",
            annotation_font_color=text_color,
            annotation_bgcolor=annotation_bgcolor
        )
        fig.update_layout(
            template=template_plotly,
            title="Dividend Yield (%) por Recomendação",
            yaxis_title="DY (%)",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # 2. P/VP
    with tabs[1]:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_painel['Ticker'],
            y=df_painel['P/VP'],
            marker_color=[cor_por_recomendacao(r) for r in df_painel['Recomendação']],
            text=[f"{v:.2f}" for v in df_painel['P/VP']],
            textposition='outside'
        ))
        fig.add_hline(
            y=1, line_dash="dash", line_color="red",
            annotation_text="Paridade (P/VP = 1)",
            annotation_position="top left",
            annotation_font_color=text_color,
            annotation_bgcolor=annotation_bgcolor
        )
        fig.update_layout(
            template=template_plotly,
            title="Preço sobre Valor Patrimonial (P/VP)",
            yaxis_title="P/VP",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. Score
    with tabs[2]:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_painel['Ticker'],
            y=df_painel['Score'],
            marker_color=[cor_por_recomendacao(r) for r in df_painel['Recomendação']],
            text=[f"{v:.1f}" for v in df_painel['Score']],
            textposition='outside'
        ))
        fig.add_hline(
            y=7, line_dash="dash", line_color="green",
            annotation_text="Bom (≥7)",
            annotation_position="top left",
            annotation_font_color=text_color,
            annotation_bgcolor=annotation_bgcolor
        )
        fig.update_layout(
            template=template_plotly,
            title="Score de Qualidade (0-10)",
            yaxis_title="Score",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # 4. Pontuação
    with tabs[3]:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_painel['Ticker'],
            y=df_painel['Pontuação'],
            marker_color=[cor_por_recomendacao(r) for r in df_painel['Recomendação']],
            text=[f"{v:.1f}" for v in df_painel['Pontuação']],
            textposition='outside'
        ))
        fig.add_hline(y=80, line_dash="dash", line_color="darkgreen",
            annotation_text="Excelente (≥80)", annotation_position="top left",
            annotation_font_color=text_color, annotation_bgcolor=annotation_bgcolor)
        fig.add_hline(y=60, line_dash="dash", line_color="limegreen",
            annotation_text="Bom (≥60)", annotation_position="top left",
            annotation_font_color=text_color, annotation_bgcolor=annotation_bgcolor)
        fig.add_hline(y=40, line_dash="dash", line_color="gold",
            annotation_text="Neutro (≥40)", annotation_position="top left",
            annotation_font_color=text_color, annotation_bgcolor=annotation_bgcolor)
        fig.update_layout(
            template=template_plotly,
            title="Pontuação Total (0-100)",
            yaxis_title="Pontuação",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander('Dados utilizados', expanded=False):
        st.dataframe(df_painel)