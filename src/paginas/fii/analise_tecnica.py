import streamlit as st

import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots

from .coletar_dados_status_invest import obter_dados_fii


@st.cache_data(show_spinner=False)
def analise_tecnica(dados):
    """Adiciona indicadores técnicos à análise"""
    hist = dados['mercado']['hist_precos']
    
    # Médias móveis
    hist['MA20'] = hist['Close'].rolling(20).mean()
    hist['MA200'] = hist['Close'].rolling(200).mean()
    
    # RSI
    delta = hist['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    hist['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
    ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
    hist['MACD'] = ema12 - ema26
    hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    hist['Upper Band'] = hist['MA20'] + 2 * hist['Close'].rolling(20).std()
    hist['Lower Band'] = hist['MA20'] - 2 * hist['Close'].rolling(20).std()
    
    return hist

def exibir_analise_tecnica(carteira: list[str]):
    """Visualização interativa da análise técnica com Plotly e tema dinâmico.

    Organiza gráficos e explicações em abas, com links para referências.
    """

    opcoes = ["Selecione"] + sorted(carteira)
    ticker = st.selectbox("Selecione o FII para análise técnica:", opcoes, key="fii_tecnica")

    if not ticker or ticker == 'Selecione':
        return

    try:
        dados = obter_dados_fii(ticker)  # dicionário com ['mercado']['hist_precos']
        if (dados is not None) and ('mercado' in dados.keys()):
            hist = analise_tecnica(dados)  # DataFrame com indicadores técnicos
    except Exception as e:
        st.error(f"Erro ao obter análise técnica para {ticker}: {str(e)}")
        return

    if hist.empty:
        st.warning("Sem dados disponíveis para análise técnica.")
        return

    # Detectar tema para cores dinâmicas
    tema = None
    try:
        tema = st.runtime.scriptrunner.script_run_context.get_script_run_ctx().session_info.session.app_session._main_dg._theme
    except Exception:
        pass

    text_color = tema.get("textColor", "#000000") if tema else "#000000"
    grid_color = "#444" if (tema and tema.get("base") == "dark") else "#ccc"

    # Criar abas
    abas = st.tabs(["Preço e Bandas de Bollinger", "RSI e MACD"])

    # Aba 1: Preço, Médias e Bandas
    with abas[0]:
        fig1 = sp.make_subplots(rows=1, cols=1)

        fig1.add_trace(go.Scatter(
            x=hist.index, y=hist['Close'], name='Preço', line=dict(color='#1f77b4')))
        fig1.add_trace(go.Scatter(
            x=hist.index, y=hist['MA20'], name='Média 20 dias', line=dict(color='orange')))
        fig1.add_trace(go.Scatter(
            x=hist.index, y=hist['MA200'], name='Média 200 dias', line=dict(color='green')))
        fig1.add_trace(go.Scatter(
            x=hist.index, y=hist['Upper Band'], name='Banda Superior', line=dict(dash='dash', color='gray')))
        fig1.add_trace(go.Scatter(
            x=hist.index, y=hist['Lower Band'], name='Banda Inferior', line=dict(dash='dash', color='gray')))

        # Preenchimento entre bandas
        fig1.add_trace(go.Scatter(
            x=hist.index.tolist() + hist.index[::-1].tolist(),
            y=hist['Upper Band'].tolist() + hist['Lower Band'][::-1].tolist(),
            fill='toself', fillcolor='rgba(128,128,128,0.1)',
            line=dict(color='rgba(255,255,255,0)'), name='Bandas Bollinger'))

        fig1.update_layout(
            title=f"Preço e Bandas de Bollinger - {ticker}",
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color),
            showlegend=True,
            margin=dict(t=40, b=40),
        )
        fig1.update_xaxes(showgrid=True, gridcolor=grid_color)
        fig1.update_yaxes(showgrid=True, gridcolor=grid_color)

        st.plotly_chart(fig1, use_container_width=True)

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
        fig2 = sp.make_subplots(rows=1, cols=1)

        fig2.add_trace(go.Scatter(
            x=hist.index, y=hist['RSI'], name='RSI', line=dict(color='purple')))
        fig2.add_trace(go.Scatter(
            x=hist.index, y=hist['MACD'], name='MACD', line=dict(color='blue')))
        fig2.add_trace(go.Scatter(
            x=hist.index, y=hist['Signal'], name='Linha de Sinal', line=dict(color='orange')))

        # Linhas referência RSI
        fig2.add_shape(type="line", x0=hist.index[0], x1=hist.index[-1], y0=70, y1=70,
                       line=dict(dash='dash', color='red', width=1))
        fig2.add_shape(type="line", x0=hist.index[0], x1=hist.index[-1], y0=30, y1=30,
                       line=dict(dash='dash', color='green', width=1))

        fig2.update_layout(
            title=f"RSI e MACD - {ticker}",
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color),
            showlegend=True,
            margin=dict(t=40, b=40),
        )
        fig2.update_xaxes(showgrid=True, gridcolor=grid_color)
        fig2.update_yaxes(showgrid=True, gridcolor=grid_color)

        st.plotly_chart(fig2, use_container_width=True)

        st.markdown(f"""
            **RSI (Índice de Força Relativa):** indica condições de sobrecompra (acima de 70) ou sobrevenda (abaixo de 30).  
            Veja [Investopedia - RSI](https://www.investopedia.com/terms/r/rsi.asp) para mais detalhes.

            ---

            **MACD (Moving Average Convergence Divergence):** mostra momentum e cruzamentos de média móvel para indicar mudanças de tendência.  
            Veja [Investopedia - MACD](https://www.investopedia.com/terms/m/macd.asp) para mais informações.
            """)
