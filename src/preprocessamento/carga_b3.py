import pandas as pd
import os
import re

import streamlit as st
import tempfile

from utils import parse_from_string_to_numeric

####################################################################################################################################
# Funções auxiliares
####################################################################################################################################

    
def classificar_ativo_b3(row):
    ticker = str(row['Ticker']).upper()
    descricao = str(row['Descrição']).upper()

    # Fundos Imobiliários (FII) - mais variações comuns na descrição
    if ticker.endswith('11') and any(
        x in descricao for x in ['FII', 'FDO INV IMOB', 'FUNDO DE INVESTIMENTO IMOB', 'IMOBILIÁRIO']):
        return 'FII'

    # ETFs
    if ticker.endswith('11') and any(x in descricao for x in ['ETF', 'ÍNDICE']):
        return 'ETF'

    # BDRs
    if ticker.endswith(('34', '35', '32', '39')) or 'BDR' in descricao:
        return 'BDR'

    # Ações ON/PN
    if ticker.endswith('3'):
        return 'Ação ON'
    if ticker.endswith('4'):
        return 'Ação PN'

    # Units
    if ticker.endswith('11') and any(x in descricao for x in ['UNIT', 'UNITS']):
        return 'Unit'

    # Opções
    if len(ticker) >= 5 and ticker[-1].isdigit() and ticker[-2].isalpha():
        return 'Opção'

    # Renda Fixa Pública
    if any(p in descricao for p in ['TESOURO', 'LTN', 'NTN', 'LFT']):
        return 'Tesouro Direto'

    # Renda Fixa Privada
    if any(p in descricao for p in ['DEBENTURE', 'CRI', 'CRA', 'CDB']):
        return 'Renda Fixa Privada'

    # Fallback
    return 'Outro'

def identificar_tipo(row) -> str:
    ticker = str(row['Ticker']).upper()
    descricao = str(row['Descrição']).upper()
    produto = str(row['Produto']).upper()

    if ticker.endswith('11'):
        return 'FII'
    elif ticker.endswith(('3', '4', '5', '6')):
        return 'Ações'
    elif 'CDB' in produto:
        return 'CDB'
    else:
        return 'Outros'
    
####################################################################################################################################
# Funções principais
####################################################################################################################################

@st.dialog('Faça o Upload do Extrato da B3')
def carregar_movimentacoes_streamlit(path_fusoes_desdobramentos: str):
    """
    Componente Streamlit para upload de arquivo que retorna o DataFrame processado
    ou None se nenhum arquivo for carregado.
    """
    st.markdown("### 📤 Upload do Arquivo de Movimentações")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo Excel com suas movimentações",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        key="movimentacoes_upload"
    )
    
    if uploaded_file is not None:
        try:
            # Cria um arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            
            # Usa sua função existente para processar
            df_movimentacoes = carregar_movimentacoes(tmp_path)
            df_fusoes_desdobramentos = carregar_fusoes_desdobramentos(path_fusoes_desdobramentos)

            df_movimentacoes = ajustar_movimentacoes_por_eventos(df_mov=df_movimentacoes, df_eventos=df_fusoes_desdobramentos)
            
            # Remove o arquivo temporário
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            # Verifica se o processamento foi bem sucedido
            if isinstance(df_movimentacoes, pd.DataFrame) and not df_movimentacoes.empty \
                and isinstance(df_fusoes_desdobramentos, pd.DataFrame) and not df_fusoes_desdobramentos.empty:
                st.success("Arquivo carregado e processado com sucesso!")                                
                st.session_state['dados-movimentacoes'] = df_movimentacoes
                st.session_state['dados-fusoes'] = df_fusoes_desdobramentos
                st.session_state['upload_concluido'] = True
                st.rerun()
                
            else:
                st.error("O arquivo foi carregado mas não pôde ser processado.")                
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")



def carregar_movimentacoes(path_planilha: str) -> pd.DataFrame:
    import warnings
    from openpyxl.styles.stylesheet import Stylesheet

    # Suprimir o aviso específico
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')

    df = pd.read_excel(path_planilha, dtype=str)

    # Converte a coluna Data para datetime
    df['Data'] = pd.to_datetime(
        df['Data'], 
        format='%d/%m/%Y',  # Formato brasileiro
        errors='coerce'     # Converte datas inválidas para NaT
    )


    
    # Se existir a coluna 'Produto', divide em 'Ticker' e 'Descrição'
    if 'Produto' in df.columns:
        df[['Ticker', 'Descrição']] = df['Produto'].str.split(' - ', n=1, expand=True)
        df['Ticker'] = df['Ticker'].str.strip()
        df['Descrição'] = df['Descrição'].str.strip()
        posicao_produto = df.columns.get_loc('Produto')
        #df.drop('Produto', axis=1, inplace=True)
        df.insert(posicao_produto + 1, 'Ticker', df.pop('Ticker'))
        df.insert(posicao_produto + 2, 'Descrição', df.pop('Descrição'))

    colunas_necessarias = ['Ticker', 'Descrição']
    if all(col in df.columns for col in colunas_necessarias):
        df['Tipo de Ativo'] = df.apply(classificar_ativo_b3, axis=1)

    # Padroniza 'Entrada/Saída' para capitalizar e tirar espaços
    df['Entrada/Saída'] = df['Entrada/Saída'].str.strip().str.capitalize()

    # Define quais tipos são considerados compra ou venda
    tipos_compra_venda = [
        'Compra',
        'Venda',
        'Transferência - Liquidação',
        # esses dois aqui abaixo não aparecem, quando filtramos por "Compra/Venda"
        # ao puxar um extrato de movimentações na B3
        # 'Leilão de Fração',
        # 'Resgate',
    ]

    df['Compra/Venda'] = df['Movimentação'].isin(tipos_compra_venda)

    colunas_monetarias = ['Valor da Operação', 'Preço unitário','Quantidade']
    if all(col in df.columns for col in colunas_monetarias):
        for col in colunas_monetarias:
            df[col] = df[col].apply(parse_from_string_to_numeric)
            
    
    # classificando por Tipo de Investimento
    df['Tipo de Investimento'] = df.apply(identificar_tipo, axis=1)
    # df['Tipo de Investimento'] = df['Produto'].apply(identificar_tipo)

    return df



def carregar_fusoes_desdobramentos(path_csv: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv)

    df['data_vigencia'] = pd.to_datetime(
        df['data_vigencia'], 
        format='%Y-%m-%d',  # Formato brasileiro
        errors='coerce'     # Converte datas inválidas para NaT
    )

    return df


def ajustar_movimentacoes_por_eventos(df_mov: pd.DataFrame, df_eventos: pd.DataFrame) -> pd.DataFrame:
    df_mov = df_mov.copy()
    df_eventos = df_eventos.copy()

    df_eventos['data_vigencia'] = pd.to_datetime(df_eventos['data_vigencia'], errors='coerce')

    def parse_fator(fator_str):
        try:
            a, b = map(float, fator_str.split(':'))
            return b / a
        except:
            return 1.0

    df_eventos['fator_float'] = df_eventos['fator_conversao'].apply(parse_fator)

    # Aplicar todos os eventos
    for _, evento in df_eventos.iterrows():
        antigo = evento['ativo_antigo']
        novo = evento['ativo_novo']
        data = evento['data_vigencia']
        fator = evento['fator_float']

        # Identifica movimentações com o ativo antigo após a data do evento
        mask = (df_mov['Ticker'] == antigo)

        # Aplica transformação: altera ticker e ajusta quantidade
        df_mov.loc[mask, 'Ticker'] = novo
        df_mov.loc[mask, 'Quantidade'] = df_mov.loc[mask, 'Quantidade'] * fator

    # Opcional: agrupar por ticker, data e tipo de movimentação, somando quantidades e valores
    df_mov.reset_index(drop=True, inplace=True)
    return df_mov




def filtrar_fii(df: pd.DataFrame) -> pd.DataFrame:

    colunas_necessarias = ['Tipo de Investimento','Tipo de Ativo']
    if not all(col in df.columns for col in colunas_necessarias):
        return df

    filtro = (df['Tipo de Ativo'] == 'FII') & (df['Tipo de Investimento'] == 'FII') & (df['Compra/Venda'])
    df_filtrado = df[filtro]
    return df_filtrado

def filtrar_acoes(df: pd.DataFrame) -> pd.DataFrame:

    colunas_necessarias = ['Tipo de Investimento','Tipo de Ativo']
    if not all(col in df.columns for col in colunas_necessarias):
        return df

    filtro = (df['Tipo de Investimento'] == 'Ações') & (df['Compra/Venda'])
    df_filtrado = df[filtro]
    return df_filtrado