import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import date

st.set_page_config(page_title="PA • Gemba Board ANDON", layout="wide")

# ==============================
# CSS
# ==============================

st.markdown("""
<style>

/* FUNDO GERAL */

.stApp{
background: linear-gradient(180deg,#6a707a,#4a4f57);
color:white;
}

/* SIDEBAR */

[data-testid="stSidebar"]{
background: rgba(70,75,85,0.9);
}

/* FILTROS */

div[data-baseweb="select"]{
background:#FFFFFF !important;
border-radius:10px !important;
}

div[data-baseweb="select"] > div{
background:#FFFFFF !important;
border:1px solid #FFFFFF !important;
color:#000000 !important;
}

div[data-baseweb="select"] *{
color:#000000 !important;
}

/* LISTA DROPDOWN */

ul[role="listbox"]{
background:#FFFFFF !important;
border:1px solid #FFFFFF !important;
}

ul[role="listbox"] li{
background:#FFFFFF !important;
color:#000000 !important;
}

ul[role="listbox"] li:hover{
background:#EDEDED !important;
color:#000000 !important;
}

/* TAGS */

span[data-baseweb="tag"]{
background:#FFFFFF !important;
color:#000000 !important;
border:1px solid #FFFFFF !important;
font-weight:700 !important;
}

span[data-baseweb="tag"] span{
color:#000000 !important;
}

span[data-baseweb="tag"] svg{
fill:#000000 !important;
}

/* TABELA */

div[data-testid="stDataFrame"]{
background:rgba(80,85,95,0.9);
border-radius:10px;
}

/* KPI */

.kpi{
background:rgba(90,95,105,0.8);
padding:14px;
border-radius:12px;
border:1px solid rgba(255,255,255,0.1);
}

</style>
""", unsafe_allow_html=True)

# ==============================
# CARREGAR PLANILHA
# ==============================

DATA_PATH = Path("data/pa.xlsx")

@st.cache_data
def load_data():

    df = pd.read_excel(DATA_PATH)

    if "Prazo" in df.columns:
        df["Prazo"] = pd.to_datetime(df["Prazo"], errors="coerce")

    if "Status" not in df.columns:
        df["Status"] = ""

    today = date.today()

    df["Atrasada_calc"] = (
        (df["Prazo"].dt.date < today) &
        (df["Status"] != "Executado")
    )

    return df

df = load_data()

# ==============================
# FILTROS
# ==============================

st.sidebar.title("Filtros")

status = st.sidebar.multiselect(
    "Status",
    df["Status"].dropna().unique(),
    default=df["Status"].dropna().unique()
)

setor = st.sidebar.multiselect(
    "Setor",
    df["Setor"].dropna().unique(),
    default=df["Setor"].dropna().unique()
)

responsavel = st.sidebar.multiselect(
    "Responsável",
    df["Responsável"].dropna().unique(),
    default=df["Responsável"].dropna().unique()
)

f = df[
    (df["Status"].isin(status)) &
    (df["Setor"].isin(setor)) &
    (df["Responsável"].isin(responsavel))
]

# ==============================
# MÉTRICAS
# ==============================

total = len(f)
executado = (f["Status"] == "Executado").sum()
execucao = (f["Status"] == "Em execução").sum()
abertas = (f["Status"] == "Aberta").sum()
atrasadas = f["Atrasada_calc"].sum()

col1,col2,col3,col4,col5 = st.columns(5)

col1.metric("Total", total)
col2.metric("Executadas", executado)
col3.metric("Em execução", execucao)
col4.metric("Abertas", abertas)
col5.metric("Atrasadas", atrasadas)

# ==============================
# PARETO
# ==============================

st.subheader("Pareto por Indicador")

if "Indicador" in f.columns:

    pareto = f.groupby("Indicador").size().sort_values(ascending=False)

    acumulado = pareto.cumsum()/pareto.sum()*100

    fig = go.Figure()

    fig.add_bar(
        x=pareto.index,
        y=pareto.values,
        marker_color="#49CFFF"
    )

    fig.add_scatter(
        x=pareto.index,
        y=acumulado,
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#FFE06A")
    )

    fig.update_layout(
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[0,100]
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# TABELA
# ==============================

st.subheader("Lista de Ações")

st.dataframe(f, use_container_width=True)
