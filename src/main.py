from preprocessamento import (
    carregar_movimentacoes, 
    carregar_movimentacoes_streamlit,
    carregar_fusoes_desdobramentos
)

import streamlit as st
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder

import os
import tempfile


from paginas import (
    pagina_resumo_geral
)

from utils import carregar_css_global

carregar_css_global()

# Ajusta o locale para pt_BR - isso depende do seu sistema
import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    # Se não funcionar, tenta pt_BR ou ignora
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR')
    except locale.Error:
        pass  # fallback se locale não estiver instalado

# definindo caminho dos arquivos
dir_dados = 'dados'
path_planilha_b3 = os.path.join(dir_dados, 'movimentacao-b3.xlsx') 
path_fusoes_desdobramentos = os.path.join(dir_dados, 'fusoes_desdobramentos.csv') 



# Configurações iniciais da página
st.set_page_config(
    page_title="Acompanhamento de Investimentos",
    layout="wide",
    initial_sidebar_state="expanded"
)


df_fusoes_desdobramentos = carregar_fusoes_desdobramentos(path_fusoes_desdobramentos)


# Título principal
st.title("📈 Acompanhamento de Investimentos")

# Menu lateral estilizado
with st.sidebar:
    menu = option_menu(
        menu_title="Menu Principal",
        options=["Resumo Geral", "Análises", "Configurações"],
        icons=["graph-up", "clipboard-chart", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#0E1117"},
            "icon": {"color": "orange", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#2E4053",
            },
            "nav-link-selected": {"background-color": "#2E4053"},
        }
    )

# Conteúdo dinâmico com base no menu
if menu == "Resumo Geral":
    st.header("📊 Resumo Geral")
    st.info("Aqui você verá o total investido, posição atual e lucro/prejuízo.")

    df_movimentacoes = carregar_movimentacoes_streamlit(path_planilha_b3, path_fusoes_desdobramentos)
    if df_movimentacoes is not None:
        df_movimentacoes.info()
        pagina_resumo_geral(df_movimentacoes)

    
elif menu == "Importar Operações":
    st.header("📈 Análises")
    st.info("Aqui você poderá analisar os ativos.")
    
    df_movimentacoes = carregar_movimentacoes(path_planilha_b3)
    if df_movimentacoes is None:
        df_movimentacoes = carregar_movimentacoes_streamlit(path_planilha_b3, path_fusoes_desdobramentos)

    pagina_resumo_geral(df_movimentacoes, df_fusoes_desdobramentos)

elif menu == "Configurações":
    st.header("⚙️ Configurações")
    st.info("Opções futuras como atualização de preços e preferências de layout.")

# Rodapé opcional
st.markdown("---")
st.caption("Desenvolvido por Leandro | Versão inicial")