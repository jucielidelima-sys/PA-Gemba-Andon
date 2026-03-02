
import io
from datetime import date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

DATA_PATH = "data/pa.xlsx"  # fonte fixa (sem upload)

st.set_page_config(page_title="PA • Gemba Board ANDON", layout="wide")

st.markdown(
    """
<style>
/* força fundo preto em tudo */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="stSidebarContent"]{
  background:#000000 !important;
}
[data-testid="stHeader"]{background:transparent !important;}

:root{
  --bg:#000000;
  --panel:#050713;
  --panel2:#070b1a;
  --line: rgba(255,255,255,0.10);
  --text:#e5e7eb;
  --muted:#a7b1c2;

  --neon:#00e5ff;
  --safety:#ffd60a;
  --good:#00c853;
  --warn:#ff9100;
  --bad:#ff1744;
  --info:#40c4ff;
}

.block-container{padding-top:1.0rem; padding-bottom:2.2rem; max-width: 1550px;}
section[data-testid="stSidebar"]{border-right:1px solid var(--line);}

.titlebar{
  border:1px solid var(--line);
  border-radius:18px;
  padding:16px 18px;
  background:
    radial-gradient(900px 260px at 0% 0%, rgba(0,229,255,0.20), rgba(0,0,0,0)),
    radial-gradient(700px 220px at 100% 0%, rgba(255,214,10,0.18), rgba(0,0,0,0)),
    linear-gradient(180deg, rgba(10,12,26,0.98), rgba(0,0,0,0.92));
  position: relative;
  overflow:hidden;
}
.titlebar:after{
  content:"";
  position:absolute;
  left:-50%;
  top:0;
  width:200%;
  height:2px;
  background: linear-gradient(90deg, rgba(0,229,255,0), rgba(0,229,255,1.0), rgba(0,229,255,0));
  opacity: 0.78;
}
.big-title{
  font-size:32px;
  font-weight:1000;
  letter-spacing:0.8px;
  text-transform: uppercase;
  text-shadow: 0 0 22px rgba(0,229,255,0.30);
}
.subtitle{
  color:var(--muted);
  font-size:12px;
  margin-top:4px;
}
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border-radius:999px; font-size:12px;
  border:1px solid var(--line); color:var(--muted);
  background: rgba(255,255,255,0.03);
}
.dot{width:9px; height:9px; border-radius:999px; display:inline-block;}
.dot.good{background:var(--good);}
.dot.warn{background:var(--warn);}
.dot.bad{background:var(--bad);}
.dot.info{background:var(--info);}
.dot.safety{background:var(--safety);}
.dot.neon{background:var(--neon); box-shadow: 0 0 10px rgba(0,229,255,0.7);}

.kpi{
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px 16px;
  background:
    radial-gradient(500px 180px at 0% 0%, rgba(0,229,255,0.10), rgba(0,0,0,0)),
    linear-gradient(180deg, rgba(255,214,10,0.06), rgba(0,0,0,0));
}
.kpi .label{color:var(--muted); font-size:12px;}
.kpi .value{font-size:28px; font-weight:1000; margin-top:4px;}
.kpi .sub{color:var(--muted); font-size:12px; margin-top:4px;}

.card{
  border:1px solid var(--line);
  border-radius:16px;
  padding:12px 12px;
  background: rgba(10,12,26,0.55);
}
.card-title{font-weight:900; margin-bottom:6px;}
.card-small{color:var(--muted); font-size:12px;}

/* Gauge glass + neon ring */
.gauge-glass{
  border-radius: 22px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.035);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  position: relative;
  padding: 10px 10px 6px 10px;
  box-shadow:
    0 0 0 1px rgba(0,229,255,0.14) inset,
    0 12px 26px rgba(0,0,0,0.65);
  overflow: hidden;
}
.gauge-glass:before{
  content:"";
  position:absolute;
  left:-50px;
  top:-50px;
  width:220px;
  height:220px;
  border-radius:999px;
  background: radial-gradient(circle, rgba(0,229,255,0.32), rgba(0,0,0,0));
  filter: blur(3px);
}
.gauge-glass:after{
  content:"";
  position:absolute;
  inset: 10px;
  border-radius: 18px;
  border: 2px solid rgba(0,229,255,0.20);
  box-shadow:
    0 0 22px rgba(0,229,255,0.28),
    0 0 65px rgba(0,229,255,0.12);
  pointer-events:none;
}
.gauge-title{
  font-weight:900;
  letter-spacing:0.3px;
  margin: 2px 0 10px 6px;
  color: rgba(229,231,235,0.95);
}
.small-note{color:var(--muted); font-size:12px;}
</style>
""",
    unsafe_allow_html=True,
)

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

def compute_metrics(df: pd.DataFrame) -> dict:
    total = len(df)
    s = df["Status"] if "Status" in df.columns else pd.Series([], dtype=str)
    execd = int((s == "Executado").sum())
    running = int((s == "Em execução").sum())
    open_ = int((s == "Aberta").sum())
    overdue = int(df["Atrasada_calc"].sum()) if "Atrasada_calc" in df.columns else 0
    completion = (execd / total * 100) if total else 0.0

    denom = max(total, 1)
    penalty = (overdue / denom) * 100 * 0.60
    health = max(0.0, min(100.0, completion - penalty))

    return dict(
        total=total, execd=execd, running=running, open=open_,
        overdue=overdue, completion=completion, penalty=penalty, health=health
    )

def gauge_fig(value: float, title: str, threshold_bad: float, threshold_warn: float):
    value = max(0.0, min(100.0, float(value)))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 44}},
        title={"text": title, "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.35)"},
            "bar": {"color": "rgba(0,229,255,0.92)"},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 1,
            "bordercolor": "rgba(255,255,255,0.12)",
            "steps": [
                {"range": [0, threshold_bad], "color": "rgba(255,23,68,0.33)"},
                {"range": [threshold_bad, threshold_warn], "color": "rgba(255,145,0,0.30)"},
                {"range": [threshold_warn, 100], "color": "rgba(0,200,83,0.25)"},
            ],
            "threshold": {
                "line": {"color": "rgba(255,214,10,0.98)", "width": 5},
                "thickness": 0.78,
                "value": value,
            }
        }
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=18, r=18, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
    )
    return fig

def render_gauge_glass(fig, title: str, height: int = 380):
    html = fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displayModeBar": False})
    components.html(
        f"""
<div class="gauge-glass">
  <div class="gauge-title">{title}</div>
  <div style="height:{height-54}px; margin-top:-8px;">
    {html}
  </div>
</div>
""",
        height=height,
        scrolling=False,
    )

# Load data
payload = load_from_repo()
meta = payload["meta"]
table = payload["table"].copy()

# Sidebar filters
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

m = compute_metrics(f)

# Title
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

# ANDON
if m["overdue"] > 0:
    st.error(f"🔴 ANDON: {m['overdue']} ação(ões) com PRAZO VENCIDO no filtro atual.")
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
cols[0].markdown(kpi_html("Total", m["total"], "Escopo selecionado"), unsafe_allow_html=True)
cols[1].markdown(kpi_html("Executadas", m["execd"], "Fechadas"), unsafe_allow_html=True)
cols[2].markdown(kpi_html("Em execução", m["running"], "Ativas"), unsafe_allow_html=True)
cols[3].markdown(kpi_html("Abertas", m["open"], "Backlog"), unsafe_allow_html=True)
cols[4].markdown(kpi_html("Atrasadas (calc.)", m["overdue"], "Prazo vencido"), unsafe_allow_html=True)
cols[5].markdown(kpi_html("Conclusão", f'{m["completion"]:.1f}%', "Executadas/Total"), unsafe_allow_html=True)

st.progress(min(max(m["completion"]/100, 0.0), 1.0), text=f'Conclusão do PA: {m["completion"]:.1f}%')

st.divider()

# Gauges
g1, g2 = st.columns(2)
with g1:
    render_gauge_glass(gauge_fig(m["health"], "Saúde do PA", 50, 75), "Velocímetro Geral • Saúde do PA", 380)
    st.markdown(f'<div class="small-note">Penalidade por atrasos: <b>{m["penalty"]:.1f}</b> pts</div>', unsafe_allow_html=True)
with g2:
    render_gauge_glass(gauge_fig(m["completion"], "Conclusão do PA", 40, 70), "Velocímetro Geral • Conclusão", 380)

st.divider()

st.subheader("Velocímetro por Setor (dropdown)")
setores_current = sorted([s for s in f.get("Setor", pd.Series([], dtype=str)).dropna().astype(str).unique().tolist() if str(s).strip()])
if not setores_current:
    st.info("Não há coluna Setor no arquivo ou não existem setores no filtro atual.")
else:
    sel = st.selectbox("Selecione o Setor", options=setores_current, index=0)
    f_set = f[f["Setor"].astype(str) == str(sel)].copy()
    ms = compute_metrics(f_set)

    s1, s2 = st.columns(2)
    with s1:
        render_gauge_glass(gauge_fig(ms["health"], f"Saúde • {sel}", 50, 75), f"Setor: {sel} • Saúde", 380)
        st.markdown(f'<div class="small-note">Atrasos no setor: <b>{ms["overdue"]}</b> • Penalidade: <b>{ms["penalty"]:.1f}</b> pts</div>', unsafe_allow_html=True)
    with s2:
        render_gauge_glass(gauge_fig(ms["completion"], f"Conclusão • {sel}", 40, 70), f"Setor: {sel} • Conclusão", 380)

st.divider()

st.subheader("Lista completa (filtro aplicado)")
show_cols = [x for x in ["Causa","Ação","Indicador","Setor","Responsável","Prazo","Status","Dias_para_prazo"] if x in f.columns]
st.dataframe(f[show_cols], use_container_width=True, height=520)

st.subheader("Exportar")
csv = f.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Baixar CSV (filtro aplicado)", data=csv, file_name="pa_filtrado.csv", mime="text/csv")
