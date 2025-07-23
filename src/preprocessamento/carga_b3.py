import pandas as pd
import os

import streamlit as st
import tempfile

def carregar_movimentacoes_streamlit(path_planilha: str, path_fusoes_desdobramentos: str):
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
            if isinstance(df_movimentacoes, pd.DataFrame) and not df_movimentacoes.empty:
                st.success("Arquivo carregado e processado com sucesso!")                
                df_movimentacoes.to_excel(path_planilha, header=True)
                return df_movimentacoes
            else:
                st.error("O arquivo foi carregado mas não pôde ser processado.")
                return None
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
            return None
    
    return None


def carregar_movimentacoes(path_planilha: str) -> pd.DataFrame:
    import warnings
    from openpyxl.styles.stylesheet import Stylesheet

    # Suprimir o aviso específico
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')

    df_movimentacoes = pd.read_excel(path_planilha)

    # Converte a coluna Data para datetime
    df_movimentacoes['Data'] = pd.to_datetime(
        df_movimentacoes['Data'], 
        format='%d/%m/%Y',  # Formato brasileiro
        errors='coerce'     # Converte datas inválidas para NaT
    )

    # Se existir a coluna 'Produto', divide em 'Ticker' e 'Descrição'
    if 'Produto' in df_movimentacoes.columns:
        df_movimentacoes[['Ticker', 'Descrição']] = df_movimentacoes['Produto'].str.split(' - ', n=1, expand=True)
        df_movimentacoes['Ticker'] = df_movimentacoes['Ticker'].str.strip()
        df_movimentacoes['Descrição'] = df_movimentacoes['Descrição'].str.strip()
        posicao_produto = df_movimentacoes.columns.get_loc('Produto')
        df_movimentacoes.drop('Produto', axis=1, inplace=True)
        df_movimentacoes.insert(posicao_produto, 'Descrição', df_movimentacoes.pop('Descrição'))
        df_movimentacoes.insert(posicao_produto, 'Ticker', df_movimentacoes.pop('Ticker'))

    # Padroniza 'Entrada/Saída' para capitalizar e tirar espaços
    df_movimentacoes['Entrada/Saída'] = df_movimentacoes['Entrada/Saída'].str.strip().str.capitalize()

    return df_movimentacoes


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

