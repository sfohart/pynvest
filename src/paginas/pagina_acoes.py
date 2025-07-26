import pandas as pd
import numpy as np
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# from cotacoes import fechamento_oficial_yahoo
import yfinance as yf
import plotly.graph_objects as go

# from analises import (
#     mostrar_analise_tecnica
# )

def _preparar_dados(df):
    """Prepara o DataFrame para exibição no AgGrid"""
    df = df.copy()
    
    # Converter coluna de Data
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    
    # Criar coluna formatada para exibição
    df['Data_Formatada'] = df['Data'].dt.strftime('%d/%m/%Y')
    
    # Converter colunas numéricas
    numeric_cols = ['Quantidade', 'Preço unitário', 'Valor da Operação']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def _configurar_grid(df):
    """Configura as opções do AgGrid"""
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurações padrão
    gb.configure_default_column(
        filterable=True,
        sortable=True,
        resizable=True,
        editable=False,
        wrapText=True,
        autoHeight=True
    )
    
    # Configuração especial para datas
    gb.configure_column(
        'Data_Formatada',
        headerName='Data',
        sortable=True,
        filter='agDateColumnFilter',
        valueFormatter="function(params) {return params.value;}"
    )
    
    # Configuração para colunas numéricas
    numeric_cols = ['Quantidade', 'Preço unitário', 'Valor da Operação']
    for col in numeric_cols:
        gb.configure_column(
            col,
            type=["numericColumn", "numberColumnFilter"],
            valueFormatter=JsCode("""
                function(params) {
                    if (typeof params.value === 'number') {
                        return params.value.toLocaleString('pt-BR');
                    }
                    return params.value;
                }
            """)
        )
    
    # Configurações adicionais
    gb.configure_pagination(enabled=True, paginationPageSize=10)
    gb.configure_selection(selection_mode='multiple', use_checkbox=True)
    gb.configure_side_bar()
    
    return gb.build()

def _mostrar_movimentacoes(df_movimentacoes, habilitar_selecao=False):
    """Exibe o DataFrame no AgGrid com tratamento robusto de erros"""
    try:
        # Verificação inicial do DataFrame
        if not isinstance(df_movimentacoes, pd.DataFrame) or df_movimentacoes.empty:
            st.warning("Nenhum dado disponível para exibição.")
            return {'data': pd.DataFrame(), 'selected_rows': pd.DataFrame()}

        # Preparar cópia segura dos dados
        df_exibicao = df_movimentacoes.copy()
        
        # Converter coluna de Data
        if 'Data' in df_exibicao.columns:
            df_exibicao['Data'] = pd.to_datetime(
                df_exibicao['Data'], 
                format='%d/%m/%Y', 
                errors='coerce'
            )
            df_exibicao['Data_Formatada'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
        
        # Configurar grid
        gb = GridOptionsBuilder.from_dataframe(
            df_exibicao.drop(columns=['Data'], errors='ignore')
            .rename(columns={'Data_Formatada': 'Data'})
        )
        
        # Configurações básicas
        gb.configure_default_column(
            filterable=True,
            sortable=True,
            resizable=True,
            editable=False
        )
        
        # Configurar seleção apenas se habilitado
        if habilitar_selecao:
            gb.configure_selection(
                selection_mode='multiple',
                use_checkbox=True
            )
        
        # Exibir grid e capturar resposta
        grid_response = AgGrid(
            df_exibicao.drop(columns=['Data'], errors='ignore')
            .rename(columns={'Data_Formatada': 'Data'}),
            gridOptions=gb.build(),
            height=500,
            width='100%',
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode='FILTERED',
            try_to_convert_back_to_original_types=False
        )
        
        # Criar novo dicionário de retorno (não modificar o grid_response diretamente)
        resultado = {
            'data': grid_response['data'],
            'selected_rows': grid_response.get('selected_rows', pd.DataFrame())
        }
        
        return resultado
        
    except Exception as e:
        st.error(f"Erro ao exibir dados: {str(e)}")
        # Retornar estrutura vazia em caso de erro
        return {'data': df_movimentacoes, 'selected_rows': pd.DataFrame()}
        


def grafico_patrimonio_donut(total_investido, lucro_prejuizo, key=None, height_donut: int = 400):
    # Cores baseadas no tema atual
    if hasattr(st, 'theme') and st.theme is not None:
        tema = st.theme
        bg_color = tema.backgroundColor
        text_color = tema.textColor
        
        # Cores para o gráfico adaptadas ao tema
        if tema.base == 'dark':
            azul = '#1f77b4'  # Azul mais visível no escuro
            verde = '#2ca02c'  # Verde mais visível no escuro
            vermelho = '#d62728'  # Vermelho mais visível no escuro
        else:
            azul = '#4285F4'  # Azul do Material Design
            verde = '#0F9D58'  # Verde do Material Design
            vermelho = '#DB4437'  # Vermelho do Material Design
    else:
        # Fallback para tema claro
        bg_color = '#ffffff'
        text_color = '#31333f'
        azul = '#4285F4'
        verde = '#0F9D58'
        vermelho = '#DB4437'

    # Configuração dos dados do gráfico
    if lucro_prejuizo >= 0:
        labels = ["Total Investido", "Lucro"]
        values = [total_investido, lucro_prejuizo]
        colors = [azul, verde]
    else:
        labels = ["Total Investido", "Prejuízo"]
        values = [total_investido, abs(lucro_prejuizo)]
        colors = [azul, vermelho]

    # Criação do gráfico
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='inside',
        sort=False,
        direction='clockwise',
        showlegend=False,  # Removido para economizar espaço
        insidetextorientation='radial',
        hoverinfo='label+value+percent'
    )])

    # Formatação do valor monetário
    valor_total = total_investido + lucro_prejuizo
    valor_formatado = f'R$ {valor_total:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")

    # Layout final
    fig.update_layout(
        title_text="Distribuição do Patrimônio",
        annotations=[dict(
            text=valor_formatado,
            x=0.5, 
            y=0.5, 
            font_size=20, 
            font_color=text_color, 
            showarrow=False
        )],
        margin=dict(t=int(height_donut/8), b=int(height_donut/8), l=int(height_donut/8), r=int(height_donut/8)),
        height=height_donut,
        paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
        plot_bgcolor='rgba(0,0,0,0)',   # Fundo transparente
        font=dict(color=text_color)      # Cor do texto adaptada
    )

    return st.plotly_chart(fig, use_container_width=True, key=key)


def mostrar_resumo_investimentos(df: pd.DataFrame):
    df = df.copy()

    total_investido_geral = 0
    total_valor_mercado = 0

    resumo = []

    for ticker in df["Ticker"].unique():
        df_ticker = df[df["Ticker"] == ticker]

        # Filtra compras e vendas pelo campo "Entrada/Saída"
        compras = df_ticker[df_ticker["Entrada/Saída"] == "Credito"]
        vendas = df_ticker[df_ticker["Entrada/Saída"] == "Debito"]

        # Quantidade total comprada e vendida
        qtd_comprada = compras["Quantidade"].sum()
        qtd_vendida = vendas["Quantidade"].sum()
        qtd_liquida = qtd_comprada - qtd_vendida  # posição atual em aberto

        if qtd_liquida <= 0:
            continue  # Sem posição em aberto, não contabiliza

        # Valor total investido: soma do Valor da Operação de compras menos vendas
        total_comprado = compras["Valor da Operação"].sum()
        total_vendido = vendas["Valor da Operação"].sum()
        total_investido = total_comprado - total_vendido

        # Preço médio ponderado pela quantidade comprada
        preco_medio = (
            (compras["Quantidade"] * compras["Preço unitário"]).sum() / qtd_comprada
            if qtd_comprada > 0 else 0
        )

        # Preço atual do ticker (com sufixo '.SA' para B3)
        try:
            preco_atual = yf.Ticker(ticker + ".SA").history(period="1d")["Close"].iloc[-1]
            #preco_atual = fechamento_oficial_yahoo(ticker)
        except Exception:
            preco_atual = 0

        valor_mercado = preco_atual * qtd_liquida
        lucro_prejuizo = valor_mercado - total_investido

        total_investido_geral += total_investido
        total_valor_mercado += valor_mercado

        resumo.append({
            "Ticker": ticker,
            "Quantidade Atual": qtd_liquida,
            "Preço Médio": round(preco_medio, 2),
            "Preço Atual": round(preco_atual, 2),
            "Total Investido": round(total_investido, 2),
            "Valor de Mercado": round(valor_mercado, 2),
            "Lucro/Prejuízo": round(lucro_prejuizo, 2),
        })

    df_resumo = pd.DataFrame(resumo)
    df_resumo_formatted = df_resumo.copy()
    
    df_resumo_formatted = df_resumo_formatted.sort_values(by=['Ticker'], ascending=True) if not df_resumo_formatted.empty else df_resumo_formatted

    # Formatar colunas numéricas para string em pt-BR com 2 casas decimais
    cols_moeda = ["Preço Médio", "Preço Atual", "Total Investido", "Valor de Mercado", "Lucro/Prejuízo"]

    if not df_resumo_formatted.empty:
        for col in cols_moeda:
            df_resumo_formatted[col] = df_resumo_formatted[col].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

    # KPIs gerais
    lucro_total = total_valor_mercado - total_investido_geral
    delta = lucro_total / total_investido_geral if total_investido_geral > 0 else 0

    abas_resumo = st.tabs(["Minha Carteira", "Status por Ativo", "Histórico de Preços"])

    with abas_resumo[0]:
        st.subheader("Minha Carteira")
        st.warning("""
                    ##### Atenção:
                
                Os valores obtidos como *Preço Atual* e *Valor de Mercado* são extraídos com base no valor
                mais recente do ativo disponível no *Yahoo Finance*.
                """)

        
        

        col1, col2 = st.columns(2)
        col1.metric("Total Investido", f"R$ {total_investido_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Lucro/Prejuízo Total", f"R$ {lucro_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{delta:.2%}")

        # Donut chart com plotly
        fig_patrimonio_geral = grafico_patrimonio_donut(total_investido_geral, lucro_total, 'patrimonio_geral')
    
    with abas_resumo[1]:
        with st.expander('#### Investimentos', expanded=False):
            st.dataframe(df_resumo_formatted, use_container_width=True)    

        # Exibir cada ativo com seu gráfico donut
        for _, row in df_resumo.iterrows():
            with st.container(border=True):
                col_donut, col_info = st.columns([1, 2])
                with col_donut:
                    grafico_patrimonio_donut(
                        row['Total Investido'], 
                        row['Lucro/Prejuízo'], 
                        key=f"donut_{row['Ticker']}",
                        height_donut=300
                    )

                with col_info:
                    st.markdown(f"### {row['Ticker']}")            
                    col_qtde, col_medio, col_atual, col_lucro = st.columns(4)
                    col_qtde.metric("Quantidade", f"{row['Quantidade Atual']:,.0f}")
                    col_medio.metric("Preço Médio", f"R$ {row['Preço Médio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    col_atual.metric("Preço Atual", f"R$ {row['Preço Atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))                
                    col_lucro.metric("Lucro/Prejuízo", 
                            f"R$ {row['Lucro/Prejuízo']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                            f"{row['Lucro/Prejuízo']/row['Total Investido']:.2%}" if row['Total Investido'] > 0 else "0%")

    with abas_resumo[2]:
        tickers = ["Selecione"] + sorted(df["Ticker"].unique().tolist())
        ticker = st.selectbox("Escolha o ativo", tickers)


        if ticker != "Selecione":
            ticker_yf = ticker + ".SA"
            dados = yf.download(ticker_yf, period="6mo", interval="1d", group_by="ticker", threads=False)

            # Garantir que os dados estão em colunas simples
            if isinstance(dados.columns, pd.MultiIndex):
                # Extrai a coluna corretamente se MultiIndex
                dados.columns = dados.columns.get_level_values(1)

            # Tentativa alternativa sem o .SA, se vazio
            if dados.empty:
                dados = yf.download(ticker, period="6mo", interval="1d", group_by="ticker", threads=False)
                if isinstance(dados.columns, pd.MultiIndex):
                    dados.columns = dados.columns.get_level_values(1)

            if dados.empty or "Close" not in dados.columns:
                st.warning(f"Nenhum dado encontrado para {ticker_yf} ou {ticker}.")
                return
            
            dados.index = pd.to_datetime(dados.index)
            dados = dados[~dados.index.duplicated(keep='first')]  

            # Reindexar para dias úteis contínuos (evita gaps estranhos)
            idx = pd.date_range(start=dados.index.min(), end=dados.index.max(), freq='B')
            dados = dados.reindex(idx)

            dados = dados.dropna(subset=['Open', 'High', 'Low', 'Close'])

            #mostrar_analise_tecnica(dados)

            st.warning("""
                ##### Atenção:               
               
                * Nenhum desses métodos garante lucro. São ferramentas estatísticas, ajudam a interpretar comportamento 
                passado para tentar prever movimentos futuros.
                * É sempre recomendado validar e testar a estratégia (backtest), com filtros e contexto de mercado.
                * Indicadores técnicos normalmente são mais efetivos combinados 
                entre si e com análise fundamentalista.
               """)

def pagina_acoes(df_movimentacoes: pd.DataFrame):
    df = df_movimentacoes.copy(deep=True)

    st.markdown("### 📊 Resumo Geral")
    
    habilitar_selecao = st.checkbox("Habilitar seleção de registros", value=False)
    
    with st.expander("#### Suas movimentações", expanded=False):
        resultado = _mostrar_movimentacoes(df, habilitar_selecao)
        
        # Verificação segura das seleções
        if (habilitar_selecao and 
            isinstance(resultado['selected_rows'], pd.DataFrame) and 
            not resultado['selected_rows'].empty):
            
            st.subheader("Registros selecionados")
            selected_df = resultado['selected_rows']
            cols_to_drop = [col for col in selected_df.columns if col.startswith('_')]
            st.dataframe(selected_df.drop(columns=cols_to_drop, errors='ignore'))

    with st.expander('#### Informações Básicas', expanded=False):
        mostrar_resumo_investimentos(df)

    
    # Verificação de datas inválidas
    if isinstance(df, pd.DataFrame) and 'Data' in df.columns:
        if df['Data'].isna().any():
            st.warning("Algumas datas não puderam ser interpretadas corretamente.")