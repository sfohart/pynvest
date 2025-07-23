from datetime import datetime
import yfinance as yf
import pandas as pd

def sinal_sma(ticker: str, dados: pd.DataFrame, curto: int=10, longo: int=50):
    df = dados.copy()
    df['SMA_curto'] = df['Close'].rolling(window=curto).mean()
    df['SMA_longo'] = df['Close'].rolling(window=longo).mean()

    if len(df) < longo:
        return "Aguardar"  # Não tem dados suficientes
    
    # Pega as últimas médias
    sma_curto_ultimo = df['SMA_curto'].iloc[-1]
    sma_longo_ultimo = df['SMA_longo'].iloc[-1]
    sma_curto_anterior = df['SMA_curto'].iloc[-2]
    sma_longo_anterior = df['SMA_longo'].iloc[-2]
    
    # Cruzamento para cima: comprar
    if sma_curto_anterior < sma_longo_anterior and sma_curto_ultimo > sma_longo_ultimo:
        return "Comprar"
    # Cruzamento para baixo: vender
    elif sma_curto_anterior > sma_longo_anterior and sma_curto_ultimo < sma_longo_ultimo:
        return "Vender"
    else:
        return "Aguardar"


def calcula_rsi(series, periodo=14):
    delta = series.diff()
    ganho = delta.where(delta > 0, 0).rolling(window=periodo).mean()
    perda = -delta.where(delta < 0, 0).rolling(window=periodo).mean()
    rs = ganho / perda
    rsi = 100 - (100 / (1 + rs))
    return rsi

def sinal_rsi(ticker: str, dados: pd.DataFrame, periodo: int=14):
    df = dados.copy()
    if len(df) < periodo + 1:
        return "Aguardar"
    
    df['RSI'] = calcula_rsi(df['Close'], periodo)
    rsi_ultimo = df['RSI'].iloc[-1]
    
    if rsi_ultimo < 30:
        return "Comprar"
    elif rsi_ultimo > 70:
        return "Vender"
    else:
        return "Aguardar"


def sinal_bollinger(ticker: str, dados: pd.DataFrame, periodo: int=20):
    df = dados.copy()
    if len(df) < periodo:
        return "Aguardar"
    
    df['SMA'] = df['Close'].rolling(window=periodo).mean()
    df['stddev'] = df['Close'].rolling(window=periodo).std()
    df['banda_superior'] = df['SMA'] + 2 * df['stddev']
    df['banda_inferior'] = df['SMA'] - 2 * df['stddev']
    
    close_ultimo = df['Close'].iloc[-1]
    banda_sup_ultimo = df['banda_superior'].iloc[-1]
    banda_inf_ultimo = df['banda_inferior'].iloc[-1]
    
    if close_ultimo < banda_inf_ultimo:
        return "Comprar"
    elif close_ultimo > banda_sup_ultimo:
        return "Vender"
    else:
        return "Aguardar"
