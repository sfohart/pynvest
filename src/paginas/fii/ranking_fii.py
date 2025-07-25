import streamlit as st
import pandas as pd

from .coletar_dados_status_invest import obter_fiis_por_categoria_segmento
from .analise_setorial import analise_setorial

@st.cache_data(show_spinner=False)
def identificar_melhores_fiis_por_setor(segmento_id: int, segmento_nome: str, pesos_ajustados: dict[str, float], n=5):
    """Identifica os melhores FIIs de um setor"""
    tickers_setor = obter_fiis_por_categoria_segmento(segmento_id)
    
    if tickers_setor.empty:
        st.warning(f"Nenhum ticker encontrado para o setor '{segmento_nome}'.")
        return None
    
    df_setor = analise_setorial(tickers_setor, pesos_ajustados)
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
    df_setor = df_setor.sort_values('Score Total', ascending=False)
    melhores = df_setor.head(n)
    
    return melhores, df_setor


def exibir_melhores_fiis(df_melhores: pd.DataFrame, df_todos: pd.DataFrame, fiis_por_linha: int = 5):
    st.subheader("🏆 Melhores FIIs do Setor")

    # Aplica CSS global para os cards
    st.markdown("""
        <style>
            .fii-card {
                background-color: var(--secondary-background-color);
                border-radius: 12px;
                padding: 1rem 1.2rem;
                margin-bottom: 1rem;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                align-items: stretch;
                cursor: pointer;
                transition: all 0.2s ease-in-out;
                border: 1px solid transparent;
            }

            .fii-card:hover {
                transform: scale(1.02);
                border-color: var(--primary-color);
                background-color: var(--primary-background-color);
            }

            .fii-top {
                width: 100%;
                text-align: center;
                margin-bottom: 0.5rem;
            }

            .fii-top .ticker {
                font-size: 1.6rem;
                font-weight: 700;
                margin-bottom: 0.2rem;
            }

            .fii-top .company-name {
                font-size: 0.9rem;
                color: gray;
            }

            .fii-bottom {
                display: flex;
                justify-content: space-between;
                font-size: 0.9rem;
                gap: 0.5rem;
            }

            .fii-bottom > div {
                flex: 1;
                text-align: center;
                font-size: 0.8rem;
            }
        </style>
    """, unsafe_allow_html=True)

    tickers = df_melhores.index.tolist()
    selected_ticker = None

    fiis_por_linha = 5  # Pode mudar para 3 ou 4 conforme a tela
    medalhas = ['🥇', '🥈', '🥉']

    for i in range(0, len(tickers), fiis_por_linha):
        linha = tickers[i:i+fiis_por_linha]
        cols = st.columns(len(linha))

        for col, ticker in zip(cols, linha):
            dados = df_melhores.loc[ticker]
            score = round(dados["Score Total"], 2)
            preco = round(dados["Preço Atual (R$)"], 2)


            idx = tickers.index(ticker)
            ticker_medalha = medalhas[idx] if idx < 3 else ''


            html_card = f"""
                <div class="fii-card">
                    <div class="fii-top">
                        <div class="ticker">{ticker_medalha + ' ' if ticker_medalha else ''}{ticker}</div>
                        <div class="company-name">{dados['companyName']}</div>
                    </div>
                    <div class="fii-bottom">
                        <div><strong>R$ {dados['Preço Atual (R$)']:.2f}</strong><br><small>Preço</small></div>
                        <div><strong>{dados['P/VP']:.2f}</strong><br><small>P/VP</small></div>
                        <div><strong>{dados['DY (%)']:.2f}%</strong><br><small>DY</small></div>
                    </div>
                </div>
            """
            col.markdown(html_card, unsafe_allow_html=True)

    with st.expander('Mostrar dados de todos os FII do setor', expanded=False):
        st.dataframe(df_todos)

    
