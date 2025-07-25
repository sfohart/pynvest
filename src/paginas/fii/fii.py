

import yfinance as yf
import fundamentus as fd
import pandas as pd
import numpy as np

import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots


import streamlit as st
from streamlit_extras.card import card
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

from utils import parse_from_string_to_numeric

from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import os

from .coletar_dados_status_invest import (
    obter_dados_fii,
    obter_fiis_por_categoria_segmento
)

from .analise_fundamentalista import analise_fundamentalista_avancada
from .analise_setorial import analise_setorial


arquivos_necessarios = ['path_segmentos_fii_status_invest','path_categorias_fii_status_invest']
arquivos_faltando = [path for path in arquivos_necessarios if path not in st.session_state]

if arquivos_faltando:
    str.error(f'Arquivos de configuração/dados estão faltando na pasta \'dados\': {arquivos_faltando}')
else:    
    df_segmentos_fii = pd.read_csv(st.session_state['path_segmentos_fii_status_invest'])
    df_categorias_fii = pd.read_csv(st.session_state['path_categorias_fii_status_invest'])