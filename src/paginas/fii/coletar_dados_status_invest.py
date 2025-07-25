import requests
from bs4 import BeautifulSoup
from typing import Any, Dict
import pandas as pd

import streamlit as st
from src.utils import parse_percent, parse_currency

import yfinance as yf
import fundamentus as fd

HEADERS = {"User-Agent": "Mozilla/5.0"}


def obter_soup(ticker: str) -> BeautifulSoup:
    url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker.lower()}"
    html = requests.get(url, headers=HEADERS).text
    return BeautifulSoup(html, "html.parser")

def extrair_valor_atual(soup: BeautifulSoup) -> float | None:
    try:
        h3 = soup.find("h3", string="Valor atual")
        valor = h3.find_next("strong", class_="value").text.strip()
        return float(valor.replace(".", "").replace(",", "."))
    except Exception:
        return None
    
def extrair_dy_12m(soup: BeautifulSoup) -> float | None:
    try:
        div = soup.find("div", title=lambda t: t and "Dividend Yield" in t)
        if div:
            valor_str = div.find("strong", class_="value").text.strip()
            return parse_percent(valor_str)
        return None
    except Exception:
        return None

def extrair_valor_patrimonial(soup: BeautifulSoup) -> float | None:
    try:
        h3 = soup.find("h3", string=lambda s: s and "Val. patrimonial" in s)
        valor = h3.find_next("strong", class_="value").text.strip()
        return float(valor.replace(".", "").replace(",", "."))
    except Exception:
        return None

def extrair_pvp(soup: BeautifulSoup) -> float | None:
    try:
        h3 = soup.find("h3", string="P/VP")
        valor = h3.find_next("strong", class_="value").text.strip()
        return float(valor.replace(",", "."))
    except Exception:
        return None

def extrair_rendimento_medio_24m(soup: BeautifulSoup) -> float | None:
    try:
        h3 = soup.find("h3", string=lambda s: s and "MENSAL MÉDIO" in s)
        valor = h3.find_next("strong", class_="value").text.strip()
        return float(valor.replace(",", "."))
    except Exception:
        return None

def extrair_liquidez_media(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "Liquidez média diária" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return float(valor.replace(".", "").replace(",", "."))
    except Exception:
        return None

def extrair_participacao_ifix(soup: BeautifulSoup) -> float | None:
    try:
        h3 = soup.find("h3", string=lambda s: s and "IFIX" in s)
        valor = h3.find_next("strong", class_="value").text.strip()
        return float(valor.replace(",", "."))
    except Exception:
        return None

def extrair_valor_em_caixa(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "Valor em caixa" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return float(valor.replace("R$", "").replace(".", "").replace(",", "."))
    except Exception:
        return None

def extrair_patrimonio(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "Patrimônio" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return float(valor.replace("R$", "").replace(".", "").replace(",", "."))
    except Exception:
        return None
    
def extrair_numero_cotistas(soup: BeautifulSoup) -> int | None:
    try:
        span = soup.find("span", string=lambda s: s and "Número de cotistas" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return int(valor.replace(".", ""))
    except Exception:
        return None

def extrair_numero_cotas(soup: BeautifulSoup) -> int | None:
    try:
        span = soup.find("span", string=lambda s: s and "Número de cotas" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return int(valor.replace(".", ""))
    except Exception:
        return None

def extrair_valorizacao_12m(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "Valorização 12 meses" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return float(valor.replace("%", "").replace(",", "."))
    except Exception:
        return None

def extrair_valorizacao_mensal(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "Valorização no mês" in s)
        valor = span.find_next("strong", class_="value").text.strip()
        return float(valor.replace("%", "").replace(",", "."))
    except Exception:
        return None

def extrair_dy_cagr_3y(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "CAGR 3 anos" in s)
        valor = span.find_next("span", class_="value").text.strip()
        return float(valor.replace("%", "").replace(",", "."))
    except Exception:
        return None

def extrair_dy_cagr_5y(soup: BeautifulSoup) -> float | None:
    try:
        span = soup.find("span", string=lambda s: s and "CAGR 5 anos" in s)
        valor = span.find_next("span", class_="value").text.strip()
        return float(valor.replace("%", "").replace(",", "."))
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def obter_dados_fii(ticker_fii: str) -> dict[str,any]:
    soup = obter_soup(ticker_fii)
    return {
        "ticker": ticker_fii.upper(),
        "valor_atual": extrair_valor_atual(soup),
        "dividend_yield_12m": extrair_dy_12m(soup),
        "valor_patrimonial_p_cota": extrair_valor_patrimonial(soup),
        "pvp": extrair_pvp(soup),
        "rendimento_mensal_medio_24m": extrair_rendimento_medio_24m(soup),
        "liquidez_media_diaria": extrair_liquidez_media(soup),
        "participacao_ifix": extrair_participacao_ifix(soup),
        "valor_em_caixa": extrair_valor_em_caixa(soup),
        "patrimonio_total": extrair_patrimonio(soup),
        "numero_cotistas": extrair_numero_cotistas(soup),
        "numero_cotas": extrair_numero_cotas(soup),
        "valorizacao_12m": extrair_valorizacao_12m(soup),
        "valorizacao_mensal": extrair_valorizacao_mensal(soup),
        "dy_cagr_3y": extrair_dy_cagr_3y(soup),
        "dy_cagr_5y": extrair_dy_cagr_5y(soup),
    }



@st.cache_data(show_spinner=False)
def obter_fiis_por_categoria_segmento(segmento_id: int, categoria_id: int = 2) -> pd.DataFrame:
    url = "https://statusinvest.com.br/sector/getcompanies"
    params = {
        "categoryType": categoria_id,
        "segmentoId": segmento_id
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://statusinvest.com.br/fundos-imobiliarios",
        "Origin": "https://statusinvest.com.br",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Erro na requisição: {response.status_code}\nResposta: {response.text}")

    resposta_json = response.json()

    # Verifica se a chave 'success' é True e 'data' existe
    if not resposta_json.get("success", False) or "data" not in resposta_json:
        raise ValueError("Resposta da API inválida ou vazia")

    dados = resposta_json["data"]

    # Converte a lista de dicionários em DataFrame pandas
    df = pd.DataFrame(dados)

    return df
