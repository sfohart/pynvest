from datetime import datetime
import yfinance as yf
import pandas as pd

def analisar_media_movel(dados: pd.DataFrame, periodo_curto: int = 20, periodo_longo: int = 50):
    # Calcular médias móveis
    dados['SMA_curta'] = dados['Close'].rolling(window=periodo_curto).mean()
    dados['SMA_longa'] = dados['Close'].rolling(window=periodo_longo).mean()
    
    # Gerar sinal
    ultimo_sinal = "Neutro"
    if dados['SMA_curta'].iloc[-1] > dados['SMA_longa'].iloc[-1]:
        if dados['SMA_curta'].iloc[-2] <= dados['SMA_longa'].iloc[-2]:
            ultimo_sinal = "Compra (cruzamento para cima)"
    elif dados['SMA_curta'].iloc[-1] < dados['SMA_longa'].iloc[-1]:
        if dados['SMA_curta'].iloc[-2] >= dados['SMA_longa'].iloc[-2]:
            ultimo_sinal = "Venda (cruzamento para baixo)"
    
    return ultimo_sinal, dados[['Close', 'SMA_curta', 'SMA_longa']].tail(10)

def analisar_rsi(dados: pd.DataFrame, periodo:int=14, limiar_compra:int=30, limiar_venda:int=70):
    delta = dados['Close'].diff()
    ganho = delta.where(delta > 0, 0)
    perda = -delta.where(delta < 0, 0)
    
    avg_ganho = ganho.rolling(window=periodo).mean()
    avg_perda = perda.rolling(window=periodo).mean()
    
    rs = avg_ganho / avg_perda
    dados['RSI'] = 100 - (100 / (1 + rs))
    
    ultimo_sinal = "Neutro"
    if dados['RSI'].iloc[-1] < limiar_compra:
        ultimo_sinal = "Compra (RSI baixo)"
    elif dados['RSI'].iloc[-1] > limiar_venda:
        ultimo_sinal = "Venda (RSI alto)"
    
    return ultimo_sinal, dados[['Close', 'RSI']].tail(10)

def analisar_bandas_bollinger(dados: pd.DataFrame, periodo:int=20, desvios:int=2):
    dados['SMA'] = dados['Close'].rolling(window=periodo).mean()
    dados['STD'] = dados['Close'].rolling(window=periodo).std()
    
    dados['Banda_Superior'] = dados['SMA'] + (dados['STD'] * desvios)
    dados['Banda_Inferior'] = dados['SMA'] - (dados['STD'] * desvios)
    
    ultimo_sinal = "Neutro"
    if dados['Close'].iloc[-1] < dados['Banda_Inferior'].iloc[-1]:
        ultimo_sinal = "Compra (preço abaixo da banda inferior)"
    elif dados['Close'].iloc[-1] > dados['Banda_Superior'].iloc[-1]:
        ultimo_sinal = "Venda (preço acima da banda superior)"
    
    return ultimo_sinal, dados[['Close', 'SMA', 'Banda_Superior', 'Banda_Inferior']].tail(10)

def analisar_macd(dados: pd.DataFrame, periodo_rapido:int=12, periodo_lento:int=26, periodo_sinal:int=9):
    dados['EMA_rapida'] = dados['Close'].ewm(span=periodo_rapido, adjust=False).mean()
    dados['EMA_lenta'] = dados['Close'].ewm(span=periodo_lento, adjust=False).mean()
    dados['MACD'] = dados['EMA_rapida'] - dados['EMA_lenta']
    dados['Sinal'] = dados['MACD'].ewm(span=periodo_sinal, adjust=False).mean()
    
    ultimo_sinal = "Neutro"
    if dados['MACD'].iloc[-1] > dados['Sinal'].iloc[-1] and dados['MACD'].iloc[-2] <= dados['Sinal'].iloc[-2]:
        ultimo_sinal = "Compra (MACD cruzou para cima)"
    elif dados['MACD'].iloc[-1] < dados['Sinal'].iloc[-1] and dados['MACD'].iloc[-2] >= dados['Sinal'].iloc[-2]:
        ultimo_sinal = "Venda (MACD cruzou para baixo)"
    
    return ultimo_sinal, dados[['Close', 'MACD', 'Sinal']].tail(10)