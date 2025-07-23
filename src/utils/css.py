import streamlit as st

def carregar_css_global():
    css = """
    <style>
    /* Variáveis padrão - tema claro */
    :root {
        --bg-color: #f9f9f9;
        --text-color: #222222;
        --card-bg: #ffffff;
        --card-shadow: rgba(0,0,0,0.1);
        --color-1: #1E90FF;   /* azul */
        --color-2: #32CD32;   /* verde */
        --color-3: #FF4500;   /* vermelho/alarme */
    }

    /* Quando o tema do sistema/Streamlit for escuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: #0e1117;
            --text-color: #fafafa;
            --card-bg: #121212;
            --card-shadow: rgba(255,255,255,0.05);
            --color-1: #1E90FF;
            --color-2: #32CD32;
            --color-3: #FF4500;
        }
    }

    /* Aplica background e texto padrão da app */
    .app-body {
        background-color: var(--bg-color);
        color: var(--text-color);
        transition: background-color 0.3s ease, color 0.3s ease;
        //min-height: 100vh;
        //padding: 1rem 2rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)