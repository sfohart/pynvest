# Caminho correto para o seu arquivo .env personalizado
import pathlib
from dotenv import load_dotenv
# Caminho correto para o seu arquivo .env personalizado
# Caminho absoluto para a raiz do projeto (pasta pai de app)
root_dir = pathlib.Path(__file__).parent.parent.resolve()

# Caminho completo do arquivo .env.desenvolvimento
env_path = root_dir / ".env.desenvolvimento"
load_dotenv(".env.desenvolvimento")

from preprocessamento import (
    carregar_movimentacoes, 
    carregar_movimentacoes_streamlit,
    carregar_fusoes_desdobramentos,
    filtrar_fii,
    filtrar_acoes
)

import streamlit as st
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder

import os
import tempfile
import pandas as pd




from paginas import pagina_acoes, pagina_fii

from paginas.commons import (
    obter_tema_streamlit,
    detectar_tema_streamlit
)

# Ajusta o locale para pt_BR - isso depende do seu sistema
import locale
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Se não funcionar, tenta pt_BR ou ignora
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except locale.Error:
        pass  # fallback se locale não estiver instalado





# carregar as planilhas antes de usar o site
if not st.session_state.get('upload_concluido', False):
    st.write("Dialog should appear")
    carregar_movimentacoes_streamlit(os.getenv('PATH_FUSOES_DESDOBRAMENTOS'))
    st.stop()

df_movimentacoes = st.session_state['dados-movimentacoes']
df_fusoes_desdobramentos = st.session_state['dados-fusoes']

print(' ------------------------- df_movimentacoes -------------------------')
df_movimentacoes.info()

print(' ------------------------- df_fusoes_desdobramentos -------------------------')
df_fusoes_desdobramentos.info()

# Configurações iniciais da página
st.set_page_config(
    page_title="Acompanhamento de Investimentos",
    layout="wide",
    initial_sidebar_state="expanded"
)


# definindo o tema do menu
# CSS dinâmico com suporte a tema escuro/claro
st.markdown("""
    <style>
        /* Tema Claro */
        @media (prefers-color-scheme: light) {
            .sidebar-container {
                background-color: #FFFFFF !important;
            }
            .sidebar-container .nav-link {
                color: black !important;
            }
            .sidebar-container .nav-link:hover {
                background-color: #D3D3D3 !important;
            }
            .sidebar-container .nav-link.active {
                background-color: #ADD8E6 !important;
            }
        }

        /* Tema Escuro */
        @media (prefers-color-scheme: dark) {
            .sidebar-container {
                background-color: #0E1117 !important;
            }
            .sidebar-container .nav-link {
                color: white !important;
            }
            .sidebar-container .nav-link:hover {
                background-color: #2E4053 !important;
            }
            .sidebar-container .nav-link.active {
                background-color: #2E4053 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)


# Título principal
st.title("📈 Acompanhamento de Investimentos")

# Sidebar com estilos adaptados (aplica classe personalizada)
with st.sidebar:
    menu = option_menu(
        menu_title="Menu Principal",
        options=["Inicio", "Ações", "Fundos Imobiliários", "Configurações"],
        icons=["house", "graph-up", "bi-building", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px", "class": "sidebar-container"},  # classe personalizada
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
            },
            "nav-link-selected": {
                "color": "inherit",  # herdado do tema
            },
        },
    )


# Conteúdo dinâmico conforme menu selecionado
if menu == "Inicio":
    st.header("🏠 Início")

# Conteúdo dinâmico com base no menu
elif menu == "Ações":
    st.header("📊 Ações")
    
    if df_movimentacoes is not None:
        df_acoes = filtrar_acoes(df_movimentacoes)
        
        print(f'Valor das Operacoes: {df_acoes['Valor da Operação'].sum():,.2f}')
        pagina_acoes(df_acoes)

    
elif menu == "Fundos Imobiliários":
    st.header("🏢 Fundos Imobiliários")
        
    if df_movimentacoes is not None:
        df_fii = filtrar_fii(df_movimentacoes)
        print(f'Valor das Operacoes: {df_fii['Valor da Operação'].sum():,.2f}')
        pagina_fii(df_fii)
        

elif menu == "Configurações":
    st.header("⚙️ Configurações")
    st.info("Opções futuras como atualização de preços e preferências de layout.")

# Rodapé opcional
st.markdown("---")
st.caption("Desenvolvido por Leandro | Versão inicial")
