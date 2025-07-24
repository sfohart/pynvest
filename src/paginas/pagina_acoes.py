import pandas as pd
import numpy as np
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# from cotacoes import fechamento_oficial_yahoo
import yfinance as yf
import plotly.graph_objects as go

from analises import (
    analisar_bandas_bollinger,
    analisar_macd,
    analisar_media_movel,
    analisar_rsi
)

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

            mostrar_analise_tecnica(dados)

            st.warning("""
                ##### Atenção:               
               
                * Nenhum desses métodos garante lucro. São ferramentas estatísticas, ajudam a interpretar comportamento 
                passado para tentar prever movimentos futuros.
                * É sempre recomendado validar e testar a estratégia (backtest), com filtros e contexto de mercado.
                * Indicadores técnicos normalmente são mais efetivos combinados 
                entre si e com análise fundamentalista.
               """)
            
def mostrar_analise_tecnica(df):
    st.title("Análise Técnica para Decisão de Compra/Venda")
    
    # 1. Seletor de período
    periodo = st.radio(
        "Período de Análise:",
        options=["1 mês", "3 meses", "6 meses", "1 ano", "Máximo"],
        index=2,  # 6M como padrão
        horizontal=True,
        help="Selecione o período histórico para análise"
    )
    
    # Mapeamento para o parâmetro do Yahoo Finance
    period_map = {
        "1 mês": 30,
        "3 meses": 90,
        "6 meses": 180,
        "1 ano": 365,
        "Máximo": None
    }
    
    # 2. Calcular todos os indicadores
    try:
        dados = df.copy()
                
        # Aplicar o período selecionado (se não for o máximo)
        if periodo != "Máximo":
            dias = period_map[periodo]
            start_date = pd.Timestamp.now() - pd.Timedelta(days=dias)
            dados = dados[dados.index >= start_date]
        
        sinal_sma, dados_sma = analisar_media_movel(dados)
        sinal_rsi, dados_rsi = analisar_rsi(dados)
        sinal_bb, dados_bb = analisar_bandas_bollinger(dados)
        sinal_macd, dados_macd = analisar_macd(dados)
        
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        return
    
    # Função para formatar o delta corretamente para o Streamlit
    def formatar_delta(sinal):
        if "Compra" in sinal:
            return f"↑ {sinal}", "compra", "normal"  # Texto, delta, delta_color
        elif "Venda" in sinal:
            return f"↓ {sinal}", "venda", "inverse"  # Texto, delta, delta_color
        else:
            return sinal, "aguarde", "off"  # Texto, delta vazio, delta_color off
    
    # 3. Gráfico principal combinado
    with st.expander("📊 Visão Integrada - Gráfico Principal", expanded=True):
        st.markdown(f"**Período selecionado:** {periodo}")
        fig_principal = criar_grafico_principal(dados)
        st.plotly_chart(fig_principal, use_container_width=True)
    
    # 4. Análises individuais em 2 colunas
    col1, col2 = st.columns(2)

    
    with col1:
        # Médias Móveis
        with st.expander("📈 Médias Móveis (SMA)", expanded=True):
            st.markdown("""
            **Sobre Médias Móveis:**  
            As Médias Móveis suavizam os dados de preço para identificar tendências.  
            - **SMA 20:** Média de 20 períodos (curto prazo)  
            - **SMA 50:** Média de 50 períodos (médio prazo)  
            **Sinal de compra:** Quando a SMA curta cruza acima da SMA longa  
            **Sinal de venda:** Quando a SMA curta cruza abaixo da SMA longa
            """)
            texto_sma, delta_sma, cor_sma = formatar_delta(sinal_sma)
            st.metric("Sinal", texto_sma, delta=delta_sma, delta_color=cor_sma)
            with st.expander('Dados', expanded=False):
                fig_sma = go.Figure()
                fig_sma.add_trace(go.Scatter(x=dados_sma.index, y=dados_sma['Close'], name='Preço', line=dict(color='gray', width=1)))
                fig_sma.add_trace(go.Scatter(x=dados_sma.index, y=dados_sma['SMA_curta'], name='SMA 20', line=dict(color='orange', width=2)))
                fig_sma.add_trace(go.Scatter(x=dados_sma.index, y=dados_sma['SMA_longa'], name='SMA 50', line=dict(color='blue', width=2)))
                st.plotly_chart(fig_sma, use_container_width=True)
        
        # RSI
        with st.expander("📊 Índice de Força Relativa (RSI)", expanded=True):
            st.markdown("""
            **Sobre o RSI:**  
            O RSI mede a velocidade e mudança dos movimentos de preço (0-100).  
            - **Acima de 70:** Ativo pode estar sobrecomprado (sinal de venda)  
            - **Abaixo de 30:** Ativo pode estar sobrevendido (sinal de compra)  
            Ideal para identificar condições extremas do mercado.
            """)
            texto_rsi, delta_rsi, cor_rsi = formatar_delta(sinal_rsi)
            st.metric("Sinal", texto_rsi, delta=delta_rsi, delta_color=cor_rsi)
            with st.expander('Dados', expanded=False):
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=dados_rsi.index, y=dados_rsi['RSI'], name='RSI', line=dict(color='purple', width=2)))
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobre-vendido")
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobre-comprado")
                st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        # Bandas de Bollinger
        with st.expander("📉 Bandas de Bollinger", expanded=True):
            st.markdown("""
            **Sobre Bandas de Bollinger:**  
            Mostram a volatilidade e níveis de preço relativos.  
            - **Banda Superior:** SMA + 2 desvios padrão  
            - **Banda Inferior:** SMA - 2 desvios padrão  
            **Sinal de compra:** Quando o preço toca a banda inferior  
            **Sinal de venda:** Quando o preço toca a banda superior  
            Contração das bandas indica baixa volatilidade.
            """)
            texto_bb, delta_bb, cor_bb = formatar_delta(sinal_bb)
            st.metric("Sinal", texto_bb, delta=delta_bb, delta_color=cor_bb)
            with st.expander('Dados', expanded=False):
                fig_bb = go.Figure()
                fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['Close'], name='Preço', line=dict(color='gray', width=1)))
                fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['Banda_Superior'], name='Banda Superior', line=dict(color='red', width=1)))
                fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['SMA'], name='Média', line=dict(color='blue', width=1)))
                fig_bb.add_trace(go.Scatter(x=dados_bb.index, y=dados_bb['Banda_Inferior'], name='Banda Inferior', line=dict(color='green', width=1)))
                st.plotly_chart(fig_bb, use_container_width=True)
        
        # MACD
        with st.expander("📈 MACD (Convergência/Divergência de Médias Móveis)", expanded=True):
            st.markdown("""
            **Sobre o MACD:**  
            Mostra a relação entre duas médias móveis do preço.  
            - **MACD:** Diferença entre EMA 12 e EMA 26  
            - **Linha Sinal:** EMA 9 do MACD  
            **Sinal de compra:** Quando o MACD cruza acima da linha de sinal  
            **Sinal de venda:** Quando o MACD cruza abaixo da linha de sinal  
            O histograma mostra a diferença entre as linhas.
            """)
            texto_macd, delta_macd, cor_macd = formatar_delta(sinal_macd)
            st.metric("Sinal", texto_macd, delta=delta_macd, delta_color=cor_macd)
            with st.expander('Dados', expanded=False):
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(x=dados_macd.index, y=dados_macd['MACD'], name='MACD', line=dict(color='blue', width=2)))
                fig_macd.add_trace(go.Scatter(x=dados_macd.index, y=dados_macd['Sinal'], name='Linha Sinal', line=dict(color='orange', width=2)))
                fig_macd.add_bar(
                    x=dados_macd.index, 
                    y=dados_macd['MACD']-dados_macd['Sinal'], 
                    name='Histograma', 
                    marker_color=np.where((dados_macd['MACD']-dados_macd['Sinal']) > 0, 'green', 'red')
                )
                st.plotly_chart(fig_macd, use_container_width=True)
    
    # Nota importante
    st.info("""
    **📌 Nota Importante:**  
    - Os indicadores técnicos são recalculados automaticamente quando você altera o período de análise.  
    - Períodos mais longos mostram tendências gerais, enquanto períodos curtos revelam oportunidades de curto prazo.  
    - Recomenda-se usar múltiplos indicadores para confirmar os sinais antes de tomar decisões de investimento.
    """)


def criar_grafico_principal(dados):
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dados.index,
        open=dados['Open'],
        high=dados['High'],
        low=dados['Low'],
        close=dados['Close'],
        name='Preço',
        increasing_line_color='#2ecc71',
        decreasing_line_color='#e74c3c'
    ))
    
    # Adicionar indicadores
    if 'SMA_curta' in dados.columns:
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['SMA_curta'],
            name='SMA 20',
            line=dict(color='#f39c12', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['SMA_longa'],
            name='SMA 50', 
            line=dict(color='#3498db', width=2)
        ))
    
    if 'Banda_Superior' in dados.columns:
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['Banda_Superior'],
            name='B. Superior',
            line=dict(color='#e74c3c', width=1, dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=dados.index, y=dados['Banda_Inferior'],
            name='B. Inferior',
            line=dict(color='#2ecc71', width=1, dash='dot')
        ))
    
    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=40, l=40, r=40, b=40),
        hovermode="x unified"
    )
    
    return fig

def criar_grafico_principal(dados):
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dados.index, open=dados['Open'], high=dados['High'],
        low=dados['Low'], close=dados['Close'], name='Preço'
    ))
    
    # Adicionar todos os indicadores principais
    if 'SMA_curta' in dados.columns:
        fig.add_trace(go.Scatter(x=dados.index, y=dados['SMA_curta'], name='SMA 20', line=dict(color='orange', width=1.5)))
        fig.add_trace(go.Scatter(x=dados.index, y=dados['SMA_longa'], name='SMA 50', line=dict(color='blue', width=1.5)))
    
    if 'Banda_Superior' in dados.columns:
        fig.add_trace(go.Scatter(x=dados.index, y=dados['Banda_Superior'], name='Bollinger Superior', line=dict(color='red', width=1, dash='dot')))
        fig.add_trace(go.Scatter(x=dados.index, y=dados['Banda_Inferior'], name='Bollinger Inferior', line=dict(color='green', width=1, dash='dot')))
    
    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, l=40, r=40, b=40)
    )
    return fig
    


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