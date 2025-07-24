from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode
import yfinance as yf
import fundamentus as fd
import pandas as pd
import numpy as np

import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots


from datetime import datetime, timedelta
import streamlit as st
from utils import parse_from_string_to_numeric

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import os


dir_dados = 'dados'
path_segmentos_fii_status_invest = os.path.join(dir_dados, 'segmentos_fii_status_invest.csv') 
path_categorias_fii_status_invest = os.path.join(dir_dados, 'categorias_fii_status_invest.csv')

df_segmentos_fii = pd.read_csv(path_segmentos_fii_status_invest)
df_categorias_fii = pd.read_csv(path_categorias_fii_status_invest)


############################################################################################################
# Coletar dados do Yahoo Finance e do Fundamentus
############################################################################################################



@st.cache_data(show_spinner=False)
def coletar_dados_completos(ticker):
    ticker_yf = ticker + '.SA' if not ticker.endswith('.SA') else ticker
    dados_mercado = None
    dados_fundamentos = {}

    try:
        # Coleta dados de mercado via Yahoo
        fii_yf = yf.Ticker(ticker_yf)
        hist = fii_yf.history(period='3y')

        if hist.empty:
            raise ValueError(f"Não há dados históricos para {ticker_yf}")

        dados_mercado = {
            'hist_precos': hist,
            'dividendos': fii_yf.dividends,
            'ultimo_preco': hist['Close'].iloc[-1],
            'volume_medio': hist['Volume'].mean()
        }
    except Exception as e:
        print(f"Erro ao coletar dados de mercado para {ticker}: {str(e)}")

    try:
        # Coleta dados do Status Invest via scraping
        url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker.lower()}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        def extrair_valor_por_label(label):
            span = soup.find('h3', text=re.compile(label, re.IGNORECASE))
            if span:
                valor = span.find_next('strong')
                return valor.text.strip() if valor else ''
            return ''

        dados_fundamentos = {
            'P/VP': parse_from_string_to_numeric(extrair_valor_por_label('P/VP')),
            'Div. Yield': parse_from_string_to_numeric(extrair_valor_por_label('dividend yield')),
            'Vacância Média': parse_from_string_to_numeric(extrair_valor_por_label('vacância média')),
            'Patrimônio Líq': parse_from_string_to_numeric(extrair_valor_por_label('patrimônio líq')),
            'Número de ativos': parse_from_string_to_numeric(extrair_valor_por_label('número de ativos')),
            'Liquidez Diária': parse_from_string_to_numeric(extrair_valor_por_label('liquidez diária')),
            'Taxa de administração': parse_from_string_to_numeric(extrair_valor_por_label('taxa de administração')),
            'Último Rendimento': parse_from_string_to_numeric(extrair_valor_por_label('último rendimento'))
        }


        # Captura do setor via breadcrumb (está em uma das âncoras superiores)
        # Extrair setor com base no HTML identificado
        setor = "Desconhecido"
        span_setor = soup.find('span', text='Segmento')
        if span_setor:
            container = span_setor.find_parent('div', class_='info')
            if container:
                strong_valor = container.find('strong', class_='value')
                if strong_valor:
                    setor = strong_valor.text.strip()

    except Exception as e:
        print(f"Erro ao coletar dados do Status Invest para {ticker}: {str(e)}")

    if dados_mercado and dados_fundamentos:
        return {
            'mercado': dados_mercado,
            'fundamentos': dados_fundamentos,
            'setor': setor,
            'info': fii_yf.info if 'fii_yf' in locals() else {}
            
        }

    return None



############################################################################################################
# Análise Fundamentalista Avançada
############################################################################################################
@st.cache_data(show_spinner=False)
def analise_fundamentalista_avancada(dados):
    """Realiza análise fundamentalista completa adaptada para fundamentus 0.3.2"""
    if not dados:
        return None
    
    # Função auxiliar para converter valores percentuais
    def parse_percent(value):
        if pd.isna(value):
            return 0.0
        if isinstance(value, str):
            value = value.replace('%', '').replace('.', '').replace(',', '.')
            try:
                return float(value) / 100
            except:
                return 0.0
        return float(value)
    
    # Função auxiliar para converter valores monetários
    def parse_currency(value):
        if pd.isna(value):
            return 0.0
        if isinstance(value, str):
            value = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                return float(value)
            except:
                return 0.0
        return float(value)
    
    # Extrair dados fundamentais
    fundamentos = dados['fundamentos']
    
    # Converter valores importantes
    try:
        preco = dados['mercado']['ultimo_preco']
        p_vp = parse_currency(fundamentos.get('P/VP', 0))
        dy = parse_percent(fundamentos.get('Div. Yield', 0))
        vacancia = parse_percent(fundamentos.get('Vacância Média', 0))
        patrimonio = parse_currency(fundamentos.get('Patrimônio Líq', 0))
        n_ativos = int(fundamentos.get('Número de ativos', 0))
        liquidez = parse_currency(fundamentos.get('Liquidez Diária', 0))
        tx_adm = parse_percent(fundamentos.get('Taxa de administração', 0))
        ultimo_rendimento = parse_currency(fundamentos.get('Último Rendimento', 0))
    except Exception as e:
        print(f"Erro ao converter valores fundamentais: {str(e)}")
        return None

    # Análise de dividendos
    dividendos = dados['mercado']['dividendos']
    if len(dividendos) > 0:
        div_12m = dividendos.last('12M')
        media_div = div_12m.mean()
        dy_real = (media_div * 12) / preco * 100 if preco > 0 else 0
        if len(div_12m) > 1:
            crescimento_div = (div_12m[-1] - div_12m[0]) / div_12m[0] * 100 if div_12m[0] > 0 else 0
        else:
            crescimento_div = 0
    else:
        dy_real = 0
        crescimento_div = 0
    
    # Análise de preços
    hist = dados['mercado']['hist_precos']
    volatilidade = hist['Close'].pct_change().std() * np.sqrt(252) * 100  # anualizada
    max_52s = hist['Close'].max()
    min_52s = hist['Close'].min()
    perc_52s = (preco - min_52s) / (max_52s - min_52s) * 100 if (max_52s - min_52s) > 0 else 50
    
    # Calcular CAGR do DY (3 anos)
    dy_cagr_3a = calcular_cagr_dy(dados)
    
    # Calcular score de qualidade
    score_qualidade = calcular_score_qualidade({
        'dy': dy_real,
        'crescimento_div': crescimento_div,
        'p_vp': p_vp,
        'vacancia': vacancia * 100,  # em percentual
        'volatilidade': volatilidade,
        'liquidez': liquidez,
        'n_ativos': n_ativos
    })
    
    # Criar dicionário com todas as métricas
    analise = {
        'Preço Atual (R$)': round(preco, 2),
        'P/VP': round(p_vp, 2),
        'DY (Fundamentus) (%)': round(dy * 100, 2),
        'DY Realizado (%)': round(dy_real, 2),
        'Crescimento Dividendos (%)': round(crescimento_div, 2),
        'Vacância (%)': round(vacancia * 100, 2),
        'Patrimônio Líquido (R$ mi)': round(patrimonio / 1e6, 2),
        'Número de Ativos': n_ativos,
        'Volatilidade Anual (%)': round(volatilidade, 2),
        'Posição 52 Semanas (%)': round(perc_52s, 2),
        'Liquidez Diária (R$ mi)': round(liquidez / 1e6, 2),
        'Taxa de Administração (%)': round(tx_adm * 100, 2),
        'Último Rendimento (R$)': round(ultimo_rendimento, 2),
        'Dividend Yield CAGR (3a) (%)': round(dy_cagr_3a, 2),
        'Score Qualidade': round(score_qualidade, 1)
    }
    
    return pd.DataFrame.from_dict(analise, orient='index', columns=['Valor'])

def calcular_cagr_dy(dados):
    """Calcula o CAGR do Dividend Yield"""
    dividendos = dados['mercado']['dividendos']
    hist_precos = dados['mercado']['hist_precos']
    
    if len(dividendos) >= 36 and len(hist_precos) >= 36:
        try:
            # Dividendos dos primeiros 12 meses
            div_inicial = dividendos[:12].sum()
            preco_inicial = hist_precos['Close'].iloc[11]
            dy_inicial = (div_inicial / preco_inicial) * 100 if preco_inicial > 0 else 0
            
            # Dividendos dos últimos 12 meses
            div_final = dividendos[-12:].sum()
            preco_final = hist_precos['Close'].iloc[-1]
            dy_final = (div_final / preco_final) * 100 if preco_final > 0 else 0
            
            # Calcular CAGR
            if dy_inicial > 0 and dy_final > 0:
                return ((dy_final / dy_inicial) ** (1/3) - 1) * 100
        except:
            pass
    return 0.0

def calcular_score_qualidade(fatores):
    """Calcula um score de qualidade baseado em múltiplos fatores"""
    score = 0
    
    # Peso dos fatores
    pesos = {
        'dy': 0.25,          # Dividend Yield
        'crescimento_div': 0.2,  # Crescimento dos dividendos
        'p_vp': 0.15,        # Preço sobre Valor Patrimonial
        'vacancia': 0.15,    # Vacância média
        'volatilidade': 0.1, # Volatilidade
        'liquidez': 0.1,     # Liquidez diária
        'n_ativos': 0.05     # Número de ativos
    }
    
    # Normalização dos valores
    dy_norm = min(fatores['dy'] / 10, 1) if fatores['dy'] > 0 else 0  # Máx 10%
    crescimento_div_norm = max(-1, min(fatores['crescimento_div'] / 20, 1))  # Entre -20% e +20%
    p_vp_norm = max(0, 1 - abs(1 - fatores['p_vp']) / 0.5)  # Ideal próximo a 1
    vacancia_norm = max(0, 1 - fatores['vacancia'] / 30)  # Máx 30%
    volatilidade_norm = max(0, 1 - fatores['volatilidade'] / 50)  # Máx 50%
    liquidez_norm = min(fatores['liquidez'] / 5e6, 1) if fatores['liquidez'] > 0 else 0  # Máx R$5mi
    n_ativos_norm = min(fatores['n_ativos'] / 10, 1) if fatores['n_ativos'] > 0 else 0  # Mín 10 ativos
    
    # Cálculo do score
    score = (dy_norm * pesos['dy'] +
             crescimento_div_norm * pesos['crescimento_div'] +
             p_vp_norm * pesos['p_vp'] +
             vacancia_norm * pesos['vacancia'] +
             volatilidade_norm * pesos['volatilidade'] +
             liquidez_norm * pesos['liquidez'] +
             n_ativos_norm * pesos['n_ativos'])
    
    return score * 10  # Score de 0 a 10

############################################################################################################
# Análise Setorial
############################################################################################################

@st.cache_data(show_spinner=False)
def obter_setores():
    url = "https://statusinvest.com.br/fundos-imobiliarios"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    setores = []
    links = []

    secao = soup.find('section', id='sector-section')
    if secao:
        cards = secao.find_all('div', class_='card')
        for card in cards:
            a = card.find('a')
            if a and a.get('href'):
                link_setor = "https://statusinvest.com.br" + a['href']
                nome_setor = a.find('h3').text.strip()
                setores.append(nome_setor)
                links.append(link_setor)
    return pd.DataFrame({'Setor': setores, 'Link': links})


@st.cache_data(show_spinner=False)
def obter_ativos_por_categoria_segmento(segmento_id: int, categoria_id: int = 2) -> pd.DataFrame:
    url = "https://statusinvest.com.br/sector/getcompanies"
    params = {
        "categoryType": categoria_id,
        "segmentoId": segmento_id
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://statusinvest.com.br/fundos-imobiliarios",
        "Origin": "https://statusinvest.com.br",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Erro na requisição: {response.status_code}\nResposta: {response.text}")

    resposta_json = response.json()

    # Verifica se a chave 'success' é True e 'data' existe
    if not resposta_json.get("success", False) or "data" not in resposta_json:
        raise ValueError("Resposta da API inválida ou vazia")

    dados = resposta_json["data"]

    # Converte a lista de dicionários em DataFrame pandas
    df = pd.DataFrame(dados)

    return df




def analise_setorial(df_tickers_setor: pd.DataFrame):
    """Compara FIIs do mesmo segmento"""
    if df_tickers_setor.empty:
        return None
    
    dados_setor = []
    total = df_tickers_setor.shape[0]
    progresso = st.progress(0, text="Analisando ativos...")

    for i, ticker in enumerate(df_tickers_setor['ticker'].values, 1):    
        dados = coletar_dados_completos(ticker)
        if dados:
            analise = analise_fundamentalista_avancada(dados)
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
        if col not in ['Número de Ativos', 'Patrimônio Líquido (R$ mi)']:
            try:

                df_setor[f'Rank {col}'] = df_setor[col].rank(ascending=False if '%' in col or 'DY' in col else True)
            except:
                continue

    return df_setor


@st.cache_data(show_spinner=False)
def identificar_melhores_fiis_por_setor(segmento_id: int, segmento_nome: str, n=5):
    """Identifica os melhores FIIs de um setor"""
    tickers_setor = obter_ativos_por_categoria_segmento(segmento_id)
    
    if tickers_setor.empty:
        st.warning(f"Nenhum ticker encontrado para o setor '{segmento_nome}'.")
        return None
    
    df_setor = analise_setorial(tickers_setor)
    if df_setor is None:
        return None
    
    # Calcular score total baseado nos rankings
    rank_cols = [col for col in df_setor.columns if col.startswith('Rank')]
    df_setor['Score Total'] = df_setor[rank_cols].mean(axis=1)

    df_setor = df_setor.merge(
        tickers_setor.set_index("ticker"),
        left_index=True,
        right_index=True,
        how="left"
    )
    
    # Ordenar por score
    melhores = df_setor.sort_values('Score Total', ascending=False).head(n)
    
    return melhores


def exibir_melhores_fiis(df: pd.DataFrame):
    st.subheader("🏆 Melhores FIIs do Setor")

    colunas_principais = {
        "Ticker": "Ativo",
        "categoryName": "Categoria",
        "companyName": "Empresa",
        "sectorName": "Setor",
        "segmentName": "Segmento"
    }

    tabela_base = df.reset_index().rename(columns=colunas_principais)
    tabela_exibicao = tabela_base[list(colunas_principais.values())]

    gb = GridOptionsBuilder.from_dataframe(tabela_exibicao)
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    gb.configure_pagination(paginationAutoPageSize=True)
    

    # Desabilita ordenação em todas as colunas:
    grid_options = gb.build()
    for col_def in grid_options['columnDefs']:
        col_def['sortable'] = False

    

    grid_response = AgGrid(
        tabela_exibicao,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=300
    )

    selected = grid_response.get('selected_rows')
    
    if selected is not None and len(selected) > 0:
        if isinstance(selected, pd.DataFrame):
            ativo_selecionado = selected.iloc[0]['Ativo']
        else:
            ativo_selecionado = selected[0]['Ativo']

        st.markdown(f"### Detalhes do ativo: {ativo_selecionado}")

        dados_completos = df.loc[ativo_selecionado]

        info_basica = {
            "Empresa": dados_completos["companyName"],
            "Categoria": dados_completos["categoryName"],
            "Setor": dados_completos["sectorName"],
            "Subsetor": dados_completos.get("subSectorName", ""),
            "Segmento": dados_completos["segmentName"],
        }
        
        col_excluir = set(info_basica.keys()) | {"setor", "Ticker"}
        indicadores = dados_completos.drop(labels=col_excluir, errors="ignore")
        indicadores_df = pd.DataFrame(indicadores).reset_index()
        indicadores_df.columns = ["Indicador", "Valor"]
        st.markdown("**Indicadores Fundamentais**")
        st.dataframe(indicadores_df, use_container_width=True)


############################################################################################################
# Análise Técnica
############################################################################################################

@st.cache_data
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
        dados = coletar_dados_completos(ticker)  # dicionário com ['mercado']['hist_precos']
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

        st.markdown(f"""
        <div style="color:{text_color}; font-size:14px; margin-top:10px;">
            <b>Bandas de Bollinger:</b> indicam volatilidade e possíveis pontos de reversão.  
            <a href="https://www.investopedia.com/terms/b/bollingerbands.asp" target="_blank" style="color:#1E90FF;">Veja mais</a> na Investopedia.
        </div>
        """, unsafe_allow_html=True)

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



@st.cache_data(show_spinner=False)
def modelo_decisao_fii(ticker: str, peso_dy: float = 0.5, peso_p_vp: float = 0.3, peso_score: float = 0.2):
    """Modelo de decisão com fallback seguro"""
    dados = coletar_dados_completos(ticker)
    if not dados:
        return None
    
    try:
        analise_fund = analise_fundamentalista_avancada(dados)
        if analise_fund is None or analise_fund.empty:
            return None
            
        # Cálculo simplificado da pontuação se a análise completa falhar
        try:
            dy = analise_fund.loc['DY Realizado (%)', 'Valor']
            p_vp = analise_fund.loc['P/VP', 'Valor']
            score = analise_fund.loc['Score Qualidade', 'Valor']
            
            # Pontuação baseada em critérios simples
            pontuacao = (dy * peso_dy) + ((1/p_vp) * peso_p_vp if p_vp > 0 else 0) + (score * peso_score)
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

####################################################################################################################################
# Painel de Monitoramento da carteira
####################################################################################################################################
def painel_monitoramento(carteira):
    """Cria painel com barra de progresso"""
    dados = []
    total = len(carteira)
    progresso = st.progress(0, text="Analisando ativos...")

    for i, ticker in enumerate(carteira, 1):
        try:
            resultado = modelo_decisao_fii(ticker)
            if resultado and not resultado['Análise Fundamentalista'].empty:
                row = {
                    'Ticker': ticker,
                    'Preço': resultado['Análise Fundamentalista'].loc['Preço Atual (R$)', 'Valor'],
                    'DY (%)': resultado['Análise Fundamentalista'].loc['DY Realizado (%)', 'Valor'],
                    'P/VP': resultado['Análise Fundamentalista'].loc['P/VP', 'Valor'],
                    'Score': resultado['Análise Fundamentalista'].loc['Score Qualidade', 'Valor'],
                    'Recomendação': resultado['Recomendação']
                }

                if 'Pontuação' in resultado:
                    row['Pontuação'] = float(resultado['Pontuação'].replace('%', ''))

                dados.append(row)
        except Exception as e:
            st.warning(f"Erro ao processar {ticker}: {str(e)}")
        
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

    # Detecta tema atual do Streamlit
    tema_escuro = st.get_option("theme.base") == "dark"

    # Cores para o fundo e texto dos gráficos
    bg_color = 'rgba(0,0,0,0)'
    text_color = '#FFF' if tema_escuro else '#000'
    annotation_bgcolor = '#333' if tema_escuro else '#FFF'

    # Cores para recomendações
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

    # Dividend Yield
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
            title="Dividend Yield (%) por Recomendação",
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            font_color=text_color,
            yaxis_title="DY (%)",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # P/VP
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
            title="Preço sobre Valor Patrimonial (P/VP)",
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            font_color=text_color,
            yaxis_title="P/VP",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Score de Qualidade
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
            title="Score de Qualidade (0-10)",
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            font_color=text_color,
            yaxis_title="Score",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Pontuação Total
    with tabs[3]:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_painel['Ticker'],
            y=df_painel['Pontuação'],
            marker_color=[cor_por_recomendacao(r) for r in df_painel['Recomendação']],
            text=[f"{v:.1f}" for v in df_painel['Pontuação']],
            textposition='outside'
        ))
        fig.add_hline(
            y=80, line_dash="dash", line_color="darkgreen",
            annotation_text="Excelente (≥80)",
            annotation_position="top left",
            annotation_font_color=text_color,
            annotation_bgcolor=annotation_bgcolor
        )
        fig.add_hline(
            y=60, line_dash="dash", line_color="limegreen",
            annotation_text="Bom (≥60)",
            annotation_position="top left",
            annotation_font_color=text_color,
            annotation_bgcolor=annotation_bgcolor
        )
        fig.add_hline(
            y=40, line_dash="dash", line_color="gold",
            annotation_text="Neutro (≥40)",
            annotation_position="top left",
            annotation_font_color=text_color,
            annotation_bgcolor=annotation_bgcolor
        )
        fig.update_layout(
            title="Pontuação Total (0-100)",
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            font_color=text_color,
            yaxis_title="Pontuação",
            xaxis_title="Ticker",
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander('Dados utilizados', expanded=False):
        st.dataframe(df_painel)



####################################################################################################################################
# Página do streamlit
####################################################################################################################################

def pagina_fii(df_fii: pd.DataFrame):
    meus_fiis = df_fii['Ticker'].unique() if not df_fii.empty else []
    df_painel_monitoramento = painel_monitoramento(meus_fiis)
    
    # Gerar painel de monitoramento
    with st.expander('Painel de Monitoramento'):        
        exibir_painel_monitoramento(df_painel_monitoramento)

    with st.expander('Análise Setorial'):        
        setores = sorted(df_segmentos_fii['segmento_nome'])
        segmento_nome = st.selectbox("Escolha o ativo", setores)
        segmento_id = df_segmentos_fii.query(f"segmento_nome == '{segmento_nome}'")['segmento_id'].values[0]

        if (segmento_id is None) or (int(segmento_id) <= 0):
            st.info('Selecione um segmemnto')
            return       
        
        segmento_id = int(segmento_id)
        df_melhores_fii = identificar_melhores_fiis_por_setor(segmento_id,segmento_nome)
        if (df_melhores_fii is not None) and (not df_melhores_fii.empty):
            #st.dataframe(df_melhores_fii, height=200)
            exibir_melhores_fiis(df_melhores_fii)
        
    pass
