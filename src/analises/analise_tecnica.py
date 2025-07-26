from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np

import streamlit as st
import plotly.graph_objects as go

def calcular_media_movel(dados: pd.DataFrame, periodo_curto: int = 20, periodo_longo: int = 50):
    # Calcular médias móveis
    dados['SMA_curta'] = dados['Close'].rolling(window=periodo_curto).mean()
    dados['SMA_longa'] = dados['Close'].rolling(window=periodo_longo).mean()

    return dados

@st.cache_data(show_spinner=False)
def analisar_media_movel(dados: pd.DataFrame, periodo_curto: int = 20, periodo_longo: int = 50):
    # Calcular médias móveis
    colunas_necessarias = ['SMA_curta', 'SMA_longa']
    if not all(col in dados.columns for col in colunas_necessarias):
        dados = calcular_media_movel(dados, periodo_curto, periodo_longo)

    # Gerar sinal
    ultimo_sinal = "Neutro"
    if dados['SMA_curta'].iloc[-1] > dados['SMA_longa'].iloc[-1]:
        if dados['SMA_curta'].iloc[-2] <= dados['SMA_longa'].iloc[-2]:
            ultimo_sinal = "Compra (cruzamento para cima)"
    elif dados['SMA_curta'].iloc[-1] < dados['SMA_longa'].iloc[-1]:
        if dados['SMA_curta'].iloc[-2] >= dados['SMA_longa'].iloc[-2]:
            ultimo_sinal = "Venda (cruzamento para baixo)"
    
    return ultimo_sinal, dados[['Close', 'SMA_curta', 'SMA_longa']].tail(10)

def calcular_rsi(dados: pd.DataFrame, periodo:int=14, limiar_compra:int=30, limiar_venda:int=70):
    delta = dados['Close'].diff()
    ganho = delta.where(delta > 0, 0)
    perda = -delta.where(delta < 0, 0)
    
    avg_ganho = ganho.rolling(window=periodo).mean()
    avg_perda = perda.rolling(window=periodo).mean()
    
    rs = avg_ganho / avg_perda
    dados['RSI'] = 100 - (100 / (1 + rs))

    return dados

@st.cache_data(show_spinner=False)
def analisar_rsi(dados: pd.DataFrame, periodo:int=14, limiar_compra:int=30, limiar_venda:int=70):
    
    colunas_necessarias = ['RSI']
    if not all(col in dados.columns for col in colunas_necessarias):
        dados = calcular_rsi(dados, periodo, limiar_compra, limiar_venda)
    
    ultimo_sinal = "Neutro"
    if dados['RSI'].iloc[-1] < limiar_compra:
        ultimo_sinal = "Compra (RSI baixo)"
    elif dados['RSI'].iloc[-1] > limiar_venda:
        ultimo_sinal = "Venda (RSI alto)"
    
    return ultimo_sinal, dados[['Close', 'RSI']].tail(10)

def calcular_bandas_bollinger(dados: pd.DataFrame, periodo:int=20, desvios:int=2):
    dados['SMA'] = dados['Close'].rolling(window=periodo).mean()
    dados['STD'] = dados['Close'].rolling(window=periodo).std()
    
    dados['Banda_Superior'] = dados['SMA'] + (dados['STD'] * desvios)
    dados['Banda_Inferior'] = dados['SMA'] - (dados['STD'] * desvios)

    return dados

@st.cache_data(show_spinner=False)
def analisar_bandas_bollinger(dados: pd.DataFrame, periodo:int=20, desvios:int=2):

    colunas_necessarias = ['SMA','STD','Banda_Superior','Banda_Inferior']
    if not all(col in dados.columns for col in colunas_necessarias):
        dados = calcular_bandas_bollinger(dados, periodo, desvios)
    
    ultimo_sinal = "Neutro"
    if dados['Close'].iloc[-1] < dados['Banda_Inferior'].iloc[-1]:
        ultimo_sinal = "Compra (preço abaixo da banda inferior)"
    elif dados['Close'].iloc[-1] > dados['Banda_Superior'].iloc[-1]:
        ultimo_sinal = "Venda (preço acima da banda superior)"
    
    return ultimo_sinal, dados[['Close', 'SMA', 'Banda_Superior', 'Banda_Inferior']].tail(10)

def calcular_macd(dados: pd.DataFrame, periodo_rapido:int=12, periodo_lento:int=26, periodo_sinal:int=9):
    dados['EMA_rapida'] = dados['Close'].ewm(span=periodo_rapido, adjust=False).mean()
    dados['EMA_lenta'] = dados['Close'].ewm(span=periodo_lento, adjust=False).mean()
    dados['MACD'] = dados['EMA_rapida'] - dados['EMA_lenta']
    dados['Sinal_MACD'] = dados['MACD'].ewm(span=periodo_sinal, adjust=False).mean()

    return dados

@st.cache_data(show_spinner=False)
def analisar_macd(dados: pd.DataFrame, periodo_rapido:int=12, periodo_lento:int=26, periodo_sinal:int=9):
    colunas_necessarias = ['EMA_rapida','EMA_lenta','MACD','Sinal_MACD']
    if not all(col in dados.columns for col in colunas_necessarias):
        dados = calcular_macd(dados, periodo_rapido, periodo_lento, periodo_sinal)
    
    ultimo_sinal = "Neutro"
    if dados['MACD'].iloc[-1] > dados['Sinal'].iloc[-1] and dados['MACD'].iloc[-2] <= dados['Sinal'].iloc[-2]:
        ultimo_sinal = "Compra (MACD cruzou para cima)"
    elif dados['MACD'].iloc[-1] < dados['Sinal'].iloc[-1] and dados['MACD'].iloc[-2] >= dados['Sinal'].iloc[-2]:
        ultimo_sinal = "Venda (MACD cruzou para baixo)"
    
    return ultimo_sinal, dados[['Close', 'MACD', 'Sinal']].tail(10)


def criar_grafico_historico_precos(dados, sma: bool = True, bollinger: bool = True, key_grafico: str = 'grafico_historico_precos'):
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dados.index, open=dados['Open'], high=dados['High'],
        low=dados['Low'], close=dados['Close'], name='Preço'
    ))
    
    # Adicionar todos os indicadores principais
    if sma and ('SMA_curta' in dados.columns):
        fig.add_trace(go.Scatter(x=dados.index, y=dados['SMA_curta'], name='SMA 20', line=dict(color='orange', width=1.5)))
        fig.add_trace(go.Scatter(x=dados.index, y=dados['SMA_longa'], name='SMA 50', line=dict(color='blue', width=1.5)))
    
    if bollinger and ('Banda_Superior' in dados.columns):
        fig.add_trace(go.Scatter(x=dados.index, y=dados['Banda_Superior'], name='Bollinger Superior', line=dict(color='red', width=1, dash='dot')))
        fig.add_trace(go.Scatter(x=dados.index, y=dados['Banda_Inferior'], name='Bollinger Inferior', line=dict(color='green', width=1, dash='dot')))
    
    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, l=40, r=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True, key=key_grafico)

# Função para formatar o delta corretamente para o Streamlit
def formatar_delta(sinal):
    if "Compra" in sinal:
        return f"↑ {sinal}", "compra", "normal"  # Texto, delta, delta_color
    elif "Venda" in sinal:
        return f"↓ {sinal}", "venda", "inverse"  # Texto, delta, delta_color
    else:
        return sinal, "aguarde", "off"  # Texto, delta vazio, delta_color off

def mostrar_analise_media_movel(dados: pd.DataFrame):
    # 2. Calcular todos os indicadores
    try:
        sinal_sma, dados_sma = analisar_media_movel(dados)
    except Exception as e:
        st.error(f"Erro ao realizar a análise da média móvel: {str(e)}")
        return

    # Médias Móveis
    with st.expander("📈 Médias Móveis (SMA)", expanded=True):
        st.markdown("""
        **Sobre Médias Móveis:**  
        As Médias Móveis suavizam os dados de preço para identificar tendências.  
        - **SMA 20:** Média de 20 períodos (curto prazo)  
        - **SMA 50:** Média de 50 períodos (médio prazo)  
        **Sinal de compra:** Quando a SMA curta cruza acima da SMA longa  
        **Sinal de venda:** Quando a SMA curta cruza abaixo da SMA longa
        """)
        texto_sma, delta_sma, cor_sma = formatar_delta(sinal_sma)
        st.metric("Sinal", texto_sma, delta=delta_sma, delta_color=cor_sma)
        with st.expander('Dados', expanded=False):
            fig_sma = go.Figure()
            fig_sma.add_trace(go.Scatter(x=dados_sma.index, y=dados_sma['Close'], name='Preço', line=dict(color='gray', width=1)))
            fig_sma.add_trace(go.Scatter(x=dados_sma.index, y=dados_sma['SMA_curta'], name='SMA 20', line=dict(color='orange', width=2)))
            fig_sma.add_trace(go.Scatter(x=dados_sma.index, y=dados_sma['SMA_longa'], name='SMA 50', line=dict(color='blue', width=2)))
            st.plotly_chart(fig_sma, use_container_width=True)

def mostrar_analise_rsi(dados: pd.DataFrame):
    try:
        sinal_rsi, dados_rsi = analisar_rsi(dados)
    except Exception as e:
        st.error(f"Erro ao realizar análise RSI: {str(e)}")
        return
    
    with st.expander("📊 Índice de Força Relativa (RSI)", expanded=True):
        st.markdown("""
        **Sobre o RSI:**  
        O RSI mede a velocidade e mudança dos movimentos de preço (0-100).  
        - **Acima de 70:** Ativo pode estar sobrecomprado (sinal de venda)  
        - **Abaixo de 30:** Ativo pode estar sobrevendido (sinal de compra)  
        Ideal para identificar condições extremas do mercado.
        """)
        texto_rsi, delta_rsi, cor_rsi = formatar_delta(sinal_rsi)
        st.metric("Sinal", texto_rsi, delta=delta_rsi, delta_color=cor_rsi)
        with st.expander('Dados', expanded=False):
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=dados_rsi.index, y=dados_rsi['RSI'], name='RSI', line=dict(color='purple', width=2)))
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobre-vendido")
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobre-comprado")
            st.plotly_chart(fig_rsi, use_container_width=True)

def mostrar_analise_bandas_bollinger(dados: pd.DataFrame):
    try:
        sinal_bb, dados_bb = analisar_bandas_bollinger(dados)
    except Exception as e:
        st.error(f"Erro ao realizar análise das bandas de Bollinger: {str(e)}")
        return
    
    # Bandas de Bollinger
    with st.expander("📉 Bandas de Bollinger", expanded=True):
        st.markdown("""
        **Sobre Bandas de Bollinger:**  
        Mostram a volatilidade e níveis de preço relativos.  
        - **Banda Superior:** SMA + 2 desvios padrão  
        - **Banda Inferior:** SMA - 2 desvios padrão  
        **Sinal de compra:** Quando o preço toca a banda inferior  
        **Sinal de venda:** Quando o preço toca a banda superior  
        Contração das bandas indica baixa volatilidade.
        """)
        texto_bb, delta_bb, cor_bb = formatar_delta(sinal_bb)
        st.metric("Sinal", texto_bb, delta=delta_bb, delta_color=cor_bb)
        with st.expander('Dados', expanded=False):
            fig_bb = go.Figure()
            fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['Close'], name='Preço', line=dict(color='gray', width=1)))
            fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['Banda_Superior'], name='Banda Superior', line=dict(color='red', width=1)))
            fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['SMA'], name='Média', line=dict(color='blue', width=1)))
            fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['Banda_Inferior'], name='Banda Inferior', line=dict(color='green', width=1)))

@st.cache_data(show_spinner=False)
def mostrar_analise_macd(dados: pd.DataFrame):
    try:
        sinal_macd, dados_macd = analisar_macd(dados)
    except Exception as e:
        st.error(f"Erro ao realizar análise MACD: {str(e)}")
        return
    
    # MACD
    with st.expander("📈 MACD (Convergência/Divergência de Médias Móveis)", expanded=True):
        st.markdown("""
        **Sobre o MACD:**  
        Mostra a relação entre duas médias móveis do preço.  
        - **MACD:** Diferença entre EMA 12 e EMA 26  
        - **Linha Sinal:** EMA 9 do MACD  
        **Sinal de compra:** Quando o MACD cruza acima da linha de sinal  
        **Sinal de venda:** Quando o MACD cruza abaixo da linha de sinal  
        O histograma mostra a diferença entre as linhas.
        """)
        texto_macd, delta_macd, cor_macd = formatar_delta(sinal_macd)
        st.metric("Sinal", texto_macd, delta=delta_macd, delta_color=cor_macd)
        with st.expander('Dados', expanded=False):
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=dados_macd.index, y=dados_macd['MACD'], name='MACD', line=dict(color='blue', width=2)))
            fig_macd.add_trace(go.Scatter(x=dados_macd.index, y=dados_macd['Sinal'], name='Linha Sinal', line=dict(color='orange', width=2)))
            fig_macd.add_bar(
                x=dados_macd.index, 
                y=dados_macd['MACD']-dados_macd['Sinal'], 
                name='Histograma', 
                marker_color=np.where((dados_macd['MACD']-dados_macd['Sinal']) > 0, 'green', 'red')
            )
            st.plotly_chart(fig_macd, use_container_width=True)

# def mostrar_analise_tecnica(
#         df: pd.DataFrame, 
#         media_movel: bool = True,
#         rsi: bool = True,
#         bandas_bollinger: bool = True,
#         macd: bool = True):
    
#     st.title("Análise Técnica para Decisão de Compra/Venda")
    
#     # 1. Seletor de período
#     periodo = st.radio(
#         "Período de Análise:",
#         options=["1 mês", "3 meses", "6 meses", "1 ano", "Máximo"],
#         index=2,  # 6M como padrão
#         horizontal=True,
#         help="Selecione o período histórico para análise"
#     )
    
#     # Mapeamento para o parâmetro do Yahoo Finance
#     period_map = {
#         "1 mês": 30,
#         "3 meses": 90,
#         "6 meses": 180,
#         "1 ano": 365,
#         "Máximo": None
#     }

#     dados = df.copy()
                
#     # Aplicar o período selecionado (se não for o máximo)
#     if periodo != "Máximo":
#         dias = period_map[periodo]
#         start_date = pd.Timestamp.now() - pd.Timedelta(days=dias)
#         dados = dados[dados.index >= start_date]
    
    
#     # 3. Gráfico principal combinado
#     with st.expander("📊 Visão Integrada - Gráfico Principal", expanded=True):
#         st.markdown(f"**Período selecionado:** {periodo}")
#         fig_principal = criar_grafico_principal(dados, sma=media_movel, bollinger=bandas_bollinger)
#         st.plotly_chart(fig_principal, use_container_width=True)
    
#     # 4. Análises individuais em 2 colunas
#     dict_analises: dict[str,bool] = {
#         'Médias Móveis (SMA)': media_movel,
#         'RSI': rsi,
#         'Bandas Bollinger': bandas_bollinger,
#         'MACD': macd
#     }

#     # Filtra apenas as análises ativas (True)
#     abas_ativas = [nome for nome, ativo in dict_analises.items() if ativo]

#     # Cria as abas no Streamlit apenas para os ativos
#     if abas_ativas:
#         tabs = st.tabs(abas_ativas)

#         # Itera sobre as abas e exibe o conteúdo correspondente
#         for tab, nome in zip(tabs, abas_ativas):
#             with tab:
#                 st.write(f"Análise selecionada: **{nome}**")
#                 # Aqui você pode colocar funções específicas, ex:
#                 if nome == 'Médias Móveis (SMA)':
#                     mostrar_analise_media_movel(dados)
#                 elif nome == 'RSI':
#                     mostrar_analise_rsi(dados)
#                 elif nome == 'Bandas Bollinger':
#                     mostrar_analise_bandas_bollinger(dados)
#                 elif nome == 'MACD':
#                     mostrar_analise_macd(dados)
#     else:
#         st.info("Nenhuma análise selecionada.")
    
#     # Nota importante
#     st.info("""
#     **📌 Nota Importante:**  
#     - Os indicadores técnicos são recalculados automaticamente quando você altera o período de análise.  
#     - Períodos mais longos mostram tendências gerais, enquanto períodos curtos revelam oportunidades de curto prazo.  
#     - Recomenda-se usar múltiplos indicadores para confirmar os sinais antes de tomar decisões de investimento.
#     """)