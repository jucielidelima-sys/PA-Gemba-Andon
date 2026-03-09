
import io
from datetime import date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

DATA_PATH = "data/pa.xlsx"  # fonte fixa (sem upload)

st.set_page_config(page_title="PA • Gemba Board ANDON", layout="wide")

st.markdown("""
<style>

/* FUNDO PRETO AZULADO INDUSTRIAL */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"]{
  background:#0A0F1F !important;
  color: rgba(255,255,255,0.96) !important;
}

/* HEADER */
[data-testid="stHeader"]{
  background:transparent !important;
}

/* SIDEBAR */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"]{
  background:#0D1428 !important;
  border-right:1px solid rgba(255,255,255,0.10);
}

/* VARIÁVEIS VISUAIS */
:root{
  --bg: #0A0F1F;
  --panel: #121A33;

  --line: rgba(255,255,255,0.10);
  --muted: rgba(255,255,255,0.70);
  --muted2: rgba(255,255,255,0.60);

  --neon:#00E5FF;
  --good:#00C853;
  --warn:#FF9100;
  --bad:#FF1744;
  --info:#40C4FF;
}

/* CONTAINER */
.block-container{
  max-width:1750px;
}

/* DATAFRAME */
div[data-testid="stDataFrame"]{
  background:#0A0F1F !important;
  border:1px solid rgba(255,255,255,0.12) !important;
  border-radius:14px !important;
}

div[data-testid="stDataFrame"] .ag-root-wrapper,
div[data-testid="stDataFrame"] .ag-root,
div[data-testid="stDataFrame"] .ag-body-viewport,
div[data-testid="stDataFrame"] .ag-header,
div[data-testid="stDataFrame"] .ag-center-cols-container,
div[data-testid="stDataFrame"] .ag-row{
  background:#0A0F1F !important;
}

div[data-testid="stDataFrame"] .ag-row:hover{
  background:#121A33 !important;
}

/* TITLE BAR */
.titlebar{
  border:1px solid rgba(255,255,255,0.10);
  border-radius:18px;
  padding:16px 18px;
  background:
  radial-gradient(900px 260px at 0% 0%, rgba(0,229,255,0.18), rgba(0,0,0,0)),
  linear-gradient(180deg, #121A33, #0A0F1F);
}

/* CARDS */
.card{
  border:1px solid rgba(255,255,255,0.12);
  border-radius:16px;
  padding:12px;
  background:#121A33;
}

/* KPIs */
.kpi{
  border:1px solid rgba(255,255,255,0.10);
  border-radius:16px;
  padding:14px;
  background:#121A33;
}

/* HUD VELOCÍMETRO */
.hud{
  border-radius:22px;
  border:1px solid rgba(255,255,255,0.10);
  background:#121A33;
  backdrop-filter: blur(10px);
}

</style>
""", unsafe_allow_html=True)

STATUS_MAP = {
    "executado": "Executado",
    "em execução": "Em execução",
    "em execucao": "Em execução",
    "atrasada": "Atrasada",
    "atrasado": "Atrasada",
    "aberta": "Aberta",
    "open": "Aberta",
    "cancelada": "Cancelada",
    "em espera": "Em espera",
    "stand by": "Em espera",
}
CLOSED_STATUSES = {"Executado", "Cancelada"}

def _norm(s: str) -> str:
    return str(s).strip()

def _norm_status(s: str) -> str:
    s0 = str(s).strip()
    if not s0 or s0.lower() == "nan":
        return ""
    key = s0.lower().split("(")[0].strip()
    return STATUS_MAP.get(key, s0.split("(")[0].strip())

@st.cache_data(show_spinner=False)
def load_from_repo() -> dict:
    with open(DATA_PATH, "rb") as f:
        file_bytes = f.read()

    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="PA", header=None).dropna(how="all")

    header_row = None
    for i, row in raw.iterrows():
        row_str = row.astype(str)
        if row_str.str.contains("Ação", case=False, na=False).any() and row_str.str.contains("Indicador", case=False, na=False).any():
            header_row = i
            break
    if header_row is None:
        raise RuntimeError("Não encontrei o cabeçalho da tabela de ações (Ação/Indicador).")

    table = pd.read_excel(io.BytesIO(file_bytes), sheet_name="PA", header=header_row).dropna(how="all").copy()
    table.columns = [_norm(c) for c in table.columns]

    rename = {}
    for c in table.columns:
        cl = c.lower()
        if "causa" in cl:
            rename[c] = "Causa"
        elif "ação" in cl or "acao" in cl:
            rename[c] = "Ação"
        elif "indicador" in cl:
            rename[c] = "Indicador"
        elif "setor" in cl or "deposit" in cl:
            rename[c] = "Setor"
        elif "respons" in cl:
            rename[c] = "Responsável"
        elif "prazo" in cl or "deadline" in cl:
            rename[c] = "Prazo"
        elif "status" in cl:
            rename[c] = "Status"
        elif "observ" in cl or "remarks" in cl:
            rename[c] = "Observações"
    table = table.rename(columns=rename)

    wanted = ["Causa", "Ação", "Indicador", "Setor", "Responsável", "Prazo", "Status", "Observações"]
    cols = [c for c in wanted if c in table.columns]
    table = table[cols].copy()

    if "Status" in table.columns:
        table["Status"] = table["Status"].map(_norm_status)

    if "Prazo" in table.columns:
        table["Prazo_dt"] = pd.to_datetime(table["Prazo"], errors="coerce", dayfirst=True).dt.date
    else:
        table["Prazo_dt"] = pd.NaT

    today = date.today()
    if "Status" in table.columns:
        table["Atrasada_calc"] = (table["Prazo_dt"].notna()) & (table["Prazo_dt"] < today) & (~table["Status"].isin(CLOSED_STATUSES))
    else:
        table["Atrasada_calc"] = (table["Prazo_dt"].notna()) & (table["Prazo_dt"] < today)

    table["Dias_para_prazo"] = table["Prazo_dt"].apply(lambda d: (d - today).days if pd.notna(d) else None)

    meta = {}
    for _, r in raw.head(30).iterrows():
        left = str(r.iloc[1]) if len(r) > 1 else ""
        val = str(r.iloc[2]) if len(r) > 2 else ""
        if "Data de abertura" in left:
            meta["Data de abertura"] = val
        if "Data de atualização" in left:
            meta["Data de atualização"] = val
        if "Assunto" in left:
            meta["Assunto"] = val
        if "Responsável" in left:
            meta["Responsável do PA"] = val

    return {"meta": meta, "table": table}

def pill(dot_class: str, text: str) -> str:
    return f'<span class="badge"><span class="dot {dot_class}"></span>{text}</span>'

def kpis(df: pd.DataFrame):
    total = len(df)
    s = df["Status"] if "Status" in df.columns else pd.Series([], dtype=str)
    execd = int((s == "Executado").sum())
    running = int((s == "Em execução").sum())
    open_ = int((s == "Aberta").sum())
    overdue = int(df["Atrasada_calc"].sum()) if "Atrasada_calc" in df.columns else 0
    completion = (execd / total * 100) if total else 0.0
    return dict(total=total, execd=execd, running=running, open=open_,
                overdue=overdue, completion=completion)

def gauge_fig(value: float, title: str, threshold_bad: float, threshold_warn: float):
    value = max(0.0, min(100.0, float(value)))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 44}},
        title={"text": title, "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.35)"},
            "bar": {"color": "rgba(0,229,255,0.85)"},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 1,
            "bordercolor": "rgba(255,255,255,0.12)",
            "steps": [
                {"range": [0, threshold_bad], "color": "rgba(255,23,68,0.30)"},
                {"range": [threshold_bad, threshold_warn], "color": "rgba(255,145,0,0.28)"},
                {"range": [threshold_warn, 100], "color": "rgba(0,200,83,0.22)"},
            ],
            "threshold": {
                "line": {"color": "rgba(255,214,10,0.95)", "width": 5},
                "thickness": 0.78,
                "value": value,
            }
        }
    ))
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
    )
    return fig

# Load
try:
    payload = load_from_repo()
except FileNotFoundError:
    st.error(f"Não achei o arquivo: {DATA_PATH}. Coloque o Excel em `data/pa.xlsx`.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao ler o Excel: {e}")
    st.stop()

meta = payload["meta"]
table = payload["table"].copy()

# Sidebar filtros
with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.markdown(pill("safety", "Fonte fixa: data/pa.xlsx"), unsafe_allow_html=True)
    st.caption("Atualize o arquivo no GitHub e o painel lê sempre o último.")
    st.divider()

def safe_unique(col):
    if col in table.columns:
        vals = [v for v in table[col].dropna().astype(str).unique().tolist() if v.strip()]
        return sorted(vals)
    return []

with st.sidebar:
    status_opts = safe_unique("Status")
    setor_opts = safe_unique("Setor")
    resp_opts = safe_unique("Responsável")
    ind_opts = safe_unique("Indicador")

    f_status = st.multiselect("Status", status_opts, default=status_opts)
    f_setor = st.multiselect("Setor", setor_opts, default=setor_opts)
    f_resp = st.multiselect("Responsável", resp_opts, default=resp_opts)
    f_ind = st.multiselect("Indicador", ind_opts, default=ind_opts)
    only_overdue = st.checkbox("Somente atrasadas (calculado)", value=False)

    has_dates = table["Prazo_dt"].notna().any()
    if has_dates:
        min_d = table["Prazo_dt"].dropna().min()
        max_d = table["Prazo_dt"].dropna().max()
        f_range = st.date_input("Janela de prazos", value=(min_d, max_d))
    else:
        f_range = None

f = table.copy()
if "Status" in f.columns:
    f = f[f["Status"].isin(f_status)]
if "Setor" in f.columns:
    f = f[f["Setor"].astype(str).isin(f_setor)]
if "Responsável" in f.columns:
    f = f[f["Responsável"].astype(str).isin(f_resp)]
if "Indicador" in f.columns:
    f = f[f["Indicador"].astype(str).isin(f_ind)]
if only_overdue:
    f = f[f["Atrasada_calc"] == True]
if f_range and isinstance(f_range, (list, tuple)) and len(f_range) == 2:
    a, b = f_range
    f = f[(f["Prazo_dt"].isna()) | ((f["Prazo_dt"] >= a) & (f["Prazo_dt"] <= b))]

k = kpis(f)

# Title highlighted
st.markdown(
    f"""
<div class="titlebar">
  <div class="big-title">PA • Gemba Board ANDON</div>
  <div class="subtitle">
    Fonte fixa: <b>{DATA_PATH}</b> • Assunto: <b>{meta.get("Assunto","—")}</b> •
    Abertura: <b>{meta.get("Data de abertura","—")}</b> •
    Atualização (planilha): <b>{meta.get("Data de atualização","—")}</b> •
    Responsável: <b>{meta.get("Responsável do PA","—")}</b>
  </div>
  <div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">
    {pill("good", "Executado")}
    {pill("warn", "Em execução")}
    {pill("bad", "Atraso")}
    {pill("info", "Abertas")}
    {pill("neon", "Indústria 4.0")}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if k["overdue"] > 0:
    st.error(f"🔴 ANDON: {k['overdue']} ação(ões) com PRAZO VENCIDO no filtro atual.")
else:
    st.success("🟢 ANDON: Nenhuma ação com prazo vencido no filtro atual.")

st.divider()

# KPIs
cols = st.columns(6)
def kpi_html(label, value, sub=""):
    return f"""
<div class="kpi">
  <div class="label">{label}</div>
  <div class="value">{value}</div>
  <div class="sub">{sub}</div>
</div>
"""
cols[0].markdown(kpi_html("Total", k["total"], "Escopo selecionado"), unsafe_allow_html=True)
cols[1].markdown(kpi_html("Executadas", k["execd"], "Fechadas"), unsafe_allow_html=True)
cols[2].markdown(kpi_html("Em execução", k["running"], "Ativas"), unsafe_allow_html=True)
cols[3].markdown(kpi_html("Abertas", k["open"], "Backlog"), unsafe_allow_html=True)
cols[4].markdown(kpi_html("Atrasadas (calc.)", k["overdue"], "Prazo vencido"), unsafe_allow_html=True)
cols[5].markdown(kpi_html("Conclusão", f'{k["completion"]:.1f}%', "Executadas/Total"), unsafe_allow_html=True)

st.progress(min(max(k["completion"]/100, 0.0), 1.0), text=f'Conclusão do PA: {k["completion"]:.1f}%')

st.divider()

# Gauges
left, right = st.columns([1.05, 0.95])
with left:
    st.subheader("Velocímetro • Saúde do PA (Indústria 4.0)")
    total = max(k["total"], 1)
    penalty = (k["overdue"] / total) * 100 * 0.60
    health = max(0.0, min(100.0, k["completion"] - penalty))
    st.plotly_chart(gauge_fig(health, "Saúde do PA", threshold_bad=50, threshold_warn=75), use_container_width=True)
    st.caption(f"Saúde = Conclusão − penalidade por atrasos (penalidade: {penalty:.1f} pts).")

with right:
    st.subheader("Velocímetro • Conclusão (%)")
    st.plotly_chart(gauge_fig(k["completion"], "Conclusão do PA", threshold_bad=40, threshold_warn=70), use_container_width=True)

st.divider()

# Prioridades + Pareto Indicador
c1, c2 = st.columns([1.1, 0.9])
with c1:
    st.subheader("Prioridades (críticas)")
    crit = f[f["Atrasada_calc"] == True].copy() if "Atrasada_calc" in f.columns else f.iloc[0:0].copy()
    crit = crit.sort_values(["Dias_para_prazo"], ascending=True) if "Dias_para_prazo" in crit.columns else crit
    if len(crit):
        show_cols = [x for x in ["Ação","Setor","Responsável","Prazo","Status","Dias_para_prazo"] if x in crit.columns]
        st.dataframe(crit[show_cols].head(14), use_container_width=True, height=380)
    else:
        st.success("Sem ações críticas no filtro atual ✅")
with c2:
    st.subheader("Pareto por Indicador (Qtd)")
    if "Indicador" in f.columns and len(f):
        g = f.groupby("Indicador", dropna=False).size().reset_index(name="Qtd").sort_values("Qtd", ascending=False)
        fig = px.bar(g, x="Indicador", y="Qtd")
        fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=380, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem coluna Indicador ou sem dados.")

st.divider()

# Kanban
st.subheader("Quadro Kanban (Gestão à vista)")
st.caption("Abertas → Em execução → Executadas. Atrasadas = foco do turno.")

board_cols = st.columns(4)
board = [
    ("Abertas", "info", board_cols[0], "Aberta"),
    ("Em execução", "warn", board_cols[1], "Em execução"),
    ("Atrasadas", "bad", board_cols[2], "Atrasada"),
    ("Executadas", "good", board_cols[3], "Executado"),
]

def render_col(df, container, title, dot, status_value):
    with container:
        st.markdown(pill(dot, title), unsafe_allow_html=True)
        subset = df[df["Status"] == status_value].copy() if "Status" in df.columns else df.iloc[0:0].copy()
        subset = subset.sort_values(["Prazo_dt"], ascending=True) if "Prazo_dt" in subset.columns else subset
        if len(subset) == 0:
            st.markdown('<div class="card"><div class="card-small">Sem itens</div></div>', unsafe_allow_html=True)
            return
        for _, r in subset.head(10).iterrows():
            acao = str(r.get("Ação","")).strip()
            setor = str(r.get("Setor","")).strip()
            resp = str(r.get("Responsável","")).strip()
            prazo = str(r.get("Prazo","")).strip()
            dias = r.get("Dias_para_prazo", None)
            line2 = " • ".join([x for x in [setor, resp, (f"{dias}d" if dias is not None else "")] if x and x != "nan"])
            st.markdown(
                f"""
<div class="card" style="margin-top:8px;">
  <div class="card-title">{acao if acao else "—"}</div>
  <div class="card-small">{line2}</div>
  <div class="card-small">Prazo: <b>{prazo if prazo else "—"}</b></div>
</div>
""",
                unsafe_allow_html=True,
            )

for title, dot, cont, status_value in board:
    render_col(f, cont, title, dot, status_value)

st.divider()

# Table + export
st.subheader("Lista completa (filtro aplicado)")
show_cols = [x for x in ["Causa","Ação","Indicador","Setor","Responsável","Prazo","Status","Dias_para_prazo"] if x in f.columns]
st.dataframe(f[show_cols], use_container_width=True, height=520)

st.subheader("Exportar")
csv = f.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Baixar CSV (filtro aplicado)", data=csv, file_name="pa_filtrado.csv", mime="text/csv")
