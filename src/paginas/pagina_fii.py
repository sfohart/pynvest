import pandas as pd
import streamlit as st
import os



from .fii.analise_fundamentalista import analise_fundamentalista_avancada
from .fii.analise_setorial import analise_setorial
from .fii.monitoramento_fii import painel_monitoramento, exibir_painel_monitoramento
from .fii.ranking_fii import identificar_melhores_fiis_por_setor, exibir_melhores_fiis
from .fii.resumo_investimentos import exibir_resumo_investimentos_fii



df_segmentos_fii = pd.read_csv(os.getenv('PATH_SEGMENTOS_FII_STATUS_INVEST'))
df_categorias_fii = pd.read_csv(os.getenv('PATH_CATEGORIAS_FII_STATUS_INVEST'))

from .commons import detectar_tema_streamlit, obter_tema_streamlit
from .commons import calcular_resumo_investimentos


####################################################################################################################################
# Página do streamlit
####################################################################################################################################
def sliders_pesos_dinamicos(pesos_iniciais):
    if 'pesos_atualizados' not in st.session_state:
        pesos = pesos_iniciais.copy()
        st.session_state['pesos_atualizados'] = pesos.copy()
    else:
        pesos = st.session_state['pesos_atualizados']

    nomes = list(pesos.keys())
    labels_dict = {
        'dy':'Dividend Yield (%)',
        'dy_cagr_3a': 'DY CAGR 3a',
        'p_vp':'P/VP',
        'vacancia':'Vacância',
        'volatilidade':'Volatilidade',
        'liquidez':'Liquidez',
        'preco_cota': 'Preço do FII'
    }

    def slider_alterado(changed_key):
        # Qual slider mudou? changed_key é do tipo 'slider_dy', etc.
        slider_nome = changed_key.replace('slider_', '')

        # Pega o valor que o usuário escolheu para esse slider
        valor_fixo = st.session_state[changed_key]

        # Pega os valores atuais de todos os sliders
        valores = [st.session_state[f'slider_{nome}'] for nome in nomes]

        # Calcula a soma dos sliders menos o slider que foi alterado
        soma_outros = sum(valores) - valor_fixo

        # Quer que a soma total seja 1, logo os outros devem somar 1 - valor_fixo
        resto = 1.0 - valor_fixo

        if soma_outros == 0:
            # Se os outros sliders são todos zero, distribui igual
            for nome in nomes:
                if nome != slider_nome:
                    st.session_state[f'slider_{nome}'] = resto / (len(nomes) - 1)
        else:
            # Ajusta proporcionalmente os outros sliders para que somem 'resto'
            for nome in nomes:
                if nome != slider_nome:
                    valor_atual = st.session_state[f'slider_{nome}']
                    novo_valor = valor_atual / soma_outros * resto
                    st.session_state[f'slider_{nome}'] = round(novo_valor, 4)  # para evitar muitos decimais

        # Atualiza pesos_atualizados
        st.session_state['pesos_atualizados'] = {nome: st.session_state[f'slider_{nome}'] for nome in nomes}

        # Reseta o selectbox para atualizar (opcional)
        st.session_state['selectbox_segmento_nome'] = '-- Selecione --'

    with st.container():
        st.markdown('#### Pesos dos Indicadores')
        st.info("O valor dos pesos será normalizado, de forma que o somatório deles seja sempre 1.0:")

        sliders_por_linha = 7
        linhas = (len(nomes) + sliders_por_linha - 1) // sliders_por_linha

        valores = [st.session_state.pesos_atualizados[n] for n in nomes]

        for linha in range(linhas):
            inicio = linha * sliders_por_linha
            fim = inicio + sliders_por_linha
            nomes_linha = nomes[inicio:fim]

            cols = st.columns(len(nomes_linha))
            for col, nome in zip(cols, nomes_linha):
                with col:
                    key = f'slider_{nome}'
                    if key not in st.session_state:
                        st.session_state[key] = pesos.get(nome, 0.0)

                    st.slider(
                        label=labels_dict[nome],
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                        key=key,
                        on_change=slider_alterado,
                        args=(key,)
                    )


    return st.session_state['pesos_atualizados']




def pagina_fii(df_fii: pd.DataFrame):
    meus_fiis = df_fii['Ticker'].unique() if not df_fii.empty else []

    # Uso exemplo com pesos padrão:
    pesos_padrao = {
        'dy': 0.3,               # Forte peso
        'dy_cagr_3a': 0.2,       # Crescimento real importa
        'p_vp': 0.15,            # Valuation
        'vacancia': 0.15,        # Qualidade operacional
        'liquidez': 0.1,         # Importante para entrar/sair
        'volatilidade': 0.05,    # Menos importante
        #'preco_cota': 0.05       # Marginal, se quiser manter
    }

    pesos_ajustados = sliders_pesos_dinamicos(pesos_padrao)
    segmento_nome = None

    dados_consolidados = calcular_resumo_investimentos(df_fii)

    with st.expander('Minha Carteira'):
        exibir_resumo_investimentos_fii(dados_consolidados)
    
    # Gerar painel de monitoramento
    with st.expander('Painel de Monitoramento'):        
        df_painel_monitoramento = painel_monitoramento(meus_fiis, pesos_ajustados)
        exibir_painel_monitoramento(df_painel_monitoramento)

    with st.expander('Análise Setorial'):        
        setores = sorted(df_segmentos_fii['segmento_nome'])
        segmento_nome = st.selectbox("Escolha o ativo", setores, key="selectbox_segmento_nome")
        segmento_id = df_segmentos_fii.query(f"segmento_nome == '{segmento_nome}'")['segmento_id'].values[0]

        if (segmento_id is None) or (int(segmento_id) <= 0):
            st.info('Selecione um segmemnto')
            df_melhores_fii = None
            df_setor = None
            return       
        
        segmento_id = int(segmento_id)
        df_melhores_fii, df_setor = identificar_melhores_fiis_por_setor(segmento_id, segmento_nome, pesos_ajustados)
        if (df_melhores_fii is not None) and (not df_melhores_fii.empty):
            #st.dataframe(df_melhores_fii, height=200)
            exibir_melhores_fiis(df_melhores_fii, df_setor)
        
    