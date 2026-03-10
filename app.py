import io
import base64
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="PA • Gemba Board ANDON", layout="wide")

REL_DATA_PATH = Path("data") / "pa.xlsx"
ASSETS_DIR = Path(__file__).parent / "assets"
FUNDO_IMG = ASSETS_DIR / "fundo_industria.png"


def img_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


fundo_bg_uri = img_to_data_uri(FUNDO_IMG)

st.markdown(
    f"""
<style>
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"]{{
  background:
    linear-gradient(rgba(92, 98, 108, 0.82), rgba(58, 64, 74, 0.90)),
    url("{fundo_bg_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-repeat: no-repeat !important;
  background-attachment: fixed !important;
  color: rgba(255,255,255,0.97) !important;
}}

[data-testid="stHeader"]{{background: transparent !important;}}
*{{color: rgba(255,255,255,0.97);}}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"]{{
  background: rgba(63, 69, 80, 0.88) !important;
  backdrop-filter: blur(8px);
  border-right: 1px solid rgba(255,255,255,0.12);
}}

div[data-baseweb="select"]{{
  background:#FFFFFF !important;
  border-radius:10px !important;
}}
div[data-baseweb="select"] > div{{
  background:#FFFFFF !important;
  border:1px solid #FFFFFF !important;
  color:#000000 !important;
}}
div[data-baseweb="select"] *{{
  color:#000000 !important;
}}

ul[role="listbox"]{{
  background:#FFFFFF !important;
  border:1px solid #FFFFFF !important;
}}
ul[role="listbox"] li{{
  background:#FFFFFF !important;
  color:#000000 !important;
}}
ul[role="listbox"] li:hover{{
  background:#EDEDED !important;
  color:#000000 !important;
}}

span[data-baseweb="tag"]{{
  background:#FFFFFF !important;
  color:#000000 !important;
  border:1px solid #FFFFFF !important;
  font-weight:700 !important;
}}
span[data-baseweb="tag"] span{{
  color:#000000 !important;
}}
span[data-baseweb="tag"] svg{{
  fill:#000000 !important;
}}

div[data-testid="stDataFrame"]{{
  background: rgba(82, 88, 98, 0.88) !important;
  border:1px solid rgba(255,255,255,0.14) !important;
  border-radius:14px !important;
  padding:6px !important;
}}

.titlebar{{
  border:1px solid rgba(255,255,255,0.14);
  border-radius:18px;
  padding:16px 18px;
  background:
    radial-gradient(900px 260px at 0% 0%, rgba(73,207,255,0.12), rgba(0,0,0,0)),
    linear-gradient(180deg, rgba(82,88,98,0.82), rgba(58,64,74,0.84));
}}

.kpi-box{{
  background: rgba(78, 84, 94, 0.78);
  border:1px solid rgba(255,255,255,0.14);
  border-radius:16px;
  padding:14px;
  text-align:center;
}}
.kpi-title{{font-size:12px; color:rgba(255,255,255,0.72);}}
.kpi-value{{font-size:28px; font-weight:800;}}

.section-card{{
  border:1px solid rgba(255,255,255,0.14);
  border-radius:18px;
  background: rgba(78, 84, 94, 0.76);
  padding:12px;
}}
</style>
""",
    unsafe_allow_html=True,
)


def normalize_status(value: str) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip().lower()
    mapping = {
        "executado": "Executado",
        "em execução": "Em execução",
        "em execucao": "Em execução",
        "aberta": "Aberta",
        "atrasada": "Atrasada",
        "atrasado": "Atrasada",
        "em espera": "Em espera",
        "cancelada": "Cancelada",
    }
    return mapping.get(s, str(value).strip())


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not REL_DATA_PATH.exists():
        raise FileNotFoundError("Arquivo não encontrado em data/pa.xlsx")

    with open(REL_DATA_PATH, "rb") as f:
        file_bytes = f.read()

    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="PA", header=None).dropna(how="all")

    header_row = None
    for i, row in raw.iterrows():
        row_str = row.astype(str)
        if row_str.str.contains("Ação", case=False, na=False).any() and row_str.str.contains("Indicador", case=False, na=False).any():
            header_row = i
            break

    if header_row is None:
        raise RuntimeError("Não encontrei o cabeçalho da tabela na aba PA.")

    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="PA", header=header_row).dropna(how="all").copy()
    df.columns = [str(c).strip() for c in df.columns]

    rename = {}
    for c in df.columns:
        cl = c.lower()
        if "causa" in cl:
            rename[c] = "Causa"
        elif "ação" in cl or "acao" in cl:
            rename[c] = "Ação"
        elif "indicador" in cl:
            rename[c] = "Indicador"
        elif "setor" in cl:
            rename[c] = "Setor"
        elif "respons" in cl:
            rename[c] = "Responsável"
        elif "prazo" in cl:
            rename[c] = "Prazo"
        elif "status" in cl:
            rename[c] = "Status"
        elif "observ" in cl:
            rename[c] = "Observações"

    df = df.rename(columns=rename)

    for col in ["Ação", "Indicador", "Setor", "Responsável", "Prazo", "Status"]:
        if col not in df.columns:
            df[col] = pd.NA

    df["Status"] = df["Status"].apply(normalize_status)
    df["Prazo_dt"] = pd.to_datetime(df["Prazo"], errors="coerce", dayfirst=True)

    today = date.today()
    df["Atrasada_calc"] = (
        df["Prazo_dt"].notna()
        & (df["Prazo_dt"].dt.date < today)
        & (~df["Status"].isin(["Executado", "Cancelada"]))
    )

    return df


df = load_data()

st.markdown(
    """
<div class="titlebar">
  <div style="font-size:34px;font-weight:1000;letter-spacing:1px;text-transform:uppercase;">
    PA • GEMBA BOARD ANDON
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("Filtros")

status_opts = sorted([x for x in df["Status"].dropna().astype(str).unique().tolist() if x.strip()])
setor_opts = sorted([x for x in df["Setor"].dropna().astype(str).unique().tolist() if x.strip()])
resp_opts = sorted([x for x in df["Responsável"].dropna().astype(str).unique().tolist() if x.strip()])

status = st.sidebar.multiselect("Status", status_opts, default=status_opts)
setor = st.sidebar.multiselect("Setor", setor_opts, default=setor_opts)
responsavel = st.sidebar.multiselect("Responsável", resp_opts, default=resp_opts)

f = df.copy()
if status:
    f = f[f["Status"].isin(status)]
if setor:
    f = f[f["Setor"].astype(str).isin(setor)]
if responsavel:
    f = f[f["Responsável"].astype(str).isin(responsavel)]

total = len(f)
executado = int((f["Status"] == "Executado").sum())
execucao = int((f["Status"] == "Em execução").sum())
abertas = int((f["Status"] == "Aberta").sum())
atrasadas = int(f["Atrasada_calc"].sum())

c1, c2, c3, c4, c5 = st.columns(5)
for col, title, value in [
    (c1, "Total", total),
    (c2, "Executadas", executado),
    (c3, "Em execução", execucao),
    (c4, "Abertas", abertas),
    (c5, "Atrasadas", atrasadas),
]:
    col.markdown(
        f"<div class='kpi-box'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )

st.divider()

left, right = st.columns([1.05, 0.95])

with left:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Prioridades (críticas)")
    crit = f[f["Atrasada_calc"] == True].copy()
    if len(crit):
        show_cols = [c for c in ["Ação", "Setor", "Responsável", "Prazo", "Status"] if c in crit.columns]
        st.dataframe(crit[show_cols].head(15), use_container_width=True, height=380)
    else:
        st.success("Sem ações críticas no filtro atual.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Pareto por Indicador")
    if "Indicador" in f.columns and len(f) > 0:
        pareto = f.groupby("Indicador").size().sort_values(ascending=False)
        acumulado = pareto.cumsum() / pareto.sum() * 100 if pareto.sum() else pareto

        fig = go.Figure()
        fig.add_bar(x=pareto.index, y=pareto.values, marker_color="#49CFFF", name="Qtd")
        fig.add_scatter(
            x=pareto.index,
            y=acumulado,
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#FFE06A", width=3),
            name="Acumulado %",
        )

        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", range=[0, 100]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para o Pareto.")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.subheader("Lista de Ações")
show_cols = [c for c in ["Causa", "Ação", "Indicador", "Setor", "Responsável", "Prazo", "Status"] if c in f.columns]
st.dataframe(f[show_cols], use_container_width=True, height=500)
