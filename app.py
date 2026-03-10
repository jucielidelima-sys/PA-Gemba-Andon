import io
import base64
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

REL_DATA_PATH = Path("data") / "pa.xlsx"
ASSETS_DIR = Path(__file__).parent / "assets"
PARETO_BG = ASSETS_DIR / "pareto_bg.png"
FUNDO_IMG = ASSETS_DIR / "fundo_industria.png"

st.set_page_config(page_title="PA • Gemba Board ANDON", layout="wide")


def img_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


pareto_bg_uri = img_to_data_uri(PARETO_BG)
fundo_bg_uri = img_to_data_uri(FUNDO_IMG)

st.markdown(
    f'''
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

[data-testid="stHeader"]{{
  background: transparent !important;
}}

*{{
  color: rgba(255,255,255,0.97);
}}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"]{{
  background: rgba(63, 69, 80, 0.88) !important;
  backdrop-filter: blur(8px);
  border-right: 1px solid rgba(255,255,255,0.12);
}}

:root{{
  --line: rgba(255,255,255,0.14);
  --muted: rgba(255,255,255,0.76);
  --muted2: rgba(255,255,255,0.62);
  --neon: #7EE6FF;
  --ai: #49CFFF;
  --good: #46E79B;
  --warn: #FFC25C;
  --bad: #FF617E;
  --info: #7ABEFF;
  --safety: #FFE06A;
}}

.block-container{{
  padding-top: 1rem;
  padding-bottom: 2rem;
  max-width: 1850px;
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
  color:#000000 !important;
}}


div[data-testid="stDataFrame"]{{
  background: rgba(82, 88, 98, 0.88) !important;
  border:1px solid rgba(255,255,255,0.14) !important;
  border-radius:14px !important;
  padding:6px !important;
}}
div[data-testid="stDataFrame"] .ag-root-wrapper,
div[data-testid="stDataFrame"] .ag-root,
div[data-testid="stDataFrame"] .ag-body-viewport,
div[data-testid="stDataFrame"] .ag-header,
div[data-testid="stDataFrame"] .ag-center-cols-container,
div[data-testid="stDataFrame"] .ag-row{{
  background: rgba(82, 88, 98, 0.88) !important;
}}
div[data-testid="stDataFrame"] .ag-header-cell,
div[data-testid="stDataFrame"] .ag-cell{{
  color: rgba(255,255,255,0.96) !important;
  border-color: rgba(255,255,255,0.10) !important;
}}
div[data-testid="stDataFrame"] .ag-row:hover{{
  background: rgba(96, 103, 114, 0.92) !important;
}}

.titlebar{{
  border:1px solid var(--line);
  border-radius:18px;
  padding:16px 18px;
  background:
    radial-gradient(900px 260px at 0% 0%, rgba(73,207,255,0.12), rgba(0,0,0,0)),
    linear-gradient(180deg, rgba(82,88,98,0.82), rgba(58,64,74,0.84));
  position:relative;
  overflow:hidden;
}}
.titlebar:after{{
  content:"";
  position:absolute;
  left:-50%;
  top:0;
  width:200%;
  height:2px;
  background: linear-gradient(90deg, rgba(73,207,255,0), rgba(126,230,255,1), rgba(73,207,255,0));
  opacity:0.9;
}}

.big-title{{
  font-size:34px;
  font-weight:1000;
  letter-spacing:1px;
  text-transform:uppercase;
  text-shadow:0 0 18px rgba(126,230,255,0.25);
}}

.subtitle{{
  color:var(--muted);
  font-size:12px;
  margin-top:4px;
}}

.badge{{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:6px 10px;
  border-radius:999px;
  font-size:12px;
  border:1px solid var(--line);
  background: rgba(255,255,255,0.05);
  color:var(--muted);
}}

.dot{{width:9px; height:9px; border-radius:999px; display:inline-block;}}
.dot.good{{background:var(--good);}}
.dot.warn{{background:var(--warn);}}
.dot.bad{{background:var(--bad);}}
.dot.info{{background:var(--info);}}
.dot.neon{{background:var(--neon); box-shadow:0 0 12px rgba(126,230,255,0.85);}}

.kpi{{
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px 16px;
  background:
    radial-gradient(500px 180px at 0% 0%, rgba(73,207,255,0.08), rgba(0,0,0,0)),
    rgba(78, 84, 94, 0.78);
}}
.kpi .label{{color:var(--muted2); font-size:12px;}}
.kpi .value{{font-size:30px; font-weight:1000; margin-top:4px;}}
.kpi .sub{{color:var(--muted2); font-size:12px; margin-top:4px;}}

.hud{{
  border-radius:22px;
  border:1px solid rgba(255,255,255,0.14);
  background:
    radial-gradient(520px 220px at 0% 0%, rgba(73,207,255,0.08), rgba(0,0,0,0)),
    rgba(78, 84, 94, 0.76);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  position: relative;
  padding: 12px 12px 8px 12px;
  overflow: hidden;
  box-shadow: 0 16px 34px rgba(0,0,0,0.28);
}}
.hud:before{{
  content:"";
  position:absolute;
  inset:0;
  background: radial-gradient(circle at 50% 45%, rgba(73,207,255,0.08), rgba(0,0,0,0) 58%);
  animation: pulseGlow 2.4s infinite ease-in-out;
  pointer-events:none;
}}

@keyframes pulseGlow{{
  0%{{opacity:0.55; transform:scale(1);}}
  50%{{opacity:1.00; transform:scale(1.02);}}
  100%{{opacity:0.55; transform:scale(1);}}
}}

.card{{
  border:1px solid rgba(255,255,255,0.12);
  border-left:5px solid rgba(255,255,255,0.25);
  border-radius:16px;
  padding:12px 12px;
  background: rgba(78, 84, 94, 0.82);
  box-shadow:0 10px 22px rgba(0,0,0,0.22);
}}
.card.open{{ border-left-color: var(--info); }}
.card.run{{ border-left-color: var(--warn); }}
.card.late{{ border-left-color: var(--bad); }}
.card.done{{ border-left-color: var(--good); }}

.card-title{{
  font-weight:900;
  margin-bottom:6px;
  color:rgba(255,255,255,0.98);
}}

.card-small{{
  color:var(--muted2);
  font-size:12px;
}}

.section-card{{
  border:1px solid rgba(255,255,255,0.14);
  border-radius:18px;
  background: rgba(78, 84, 94, 0.76);
  padding:12px;
}}

.pareto-panel{{
  border:1px solid rgba(255,255,255,0.14);
  border-radius:18px;
  background: rgba(78, 84, 94, 0.58);
  padding: 8px 10px 2px 10px;
}}
</style>
''',
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

NEON = "#7EE6FF"
GOOD = "#46E79B"
WARN = "#FFC25C"
BAD = "#FF617E"
SAFETY = "#FFE06A"
AI_BLUE = "#49CFFF"


def _norm_status(s: str) -> str:
    s0 = str(s).strip()
    if not s0 or s0.lower() == "nan":
        return ""
    key = s0.lower().split("(")[0].strip()
    return STATUS_MAP.get(key, s0.split("(")[0].strip())


def _rgba(hex_color: str, alpha: float) -> str:
    c = hex_color.lstrip("#")
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def pill(dot_class: str, text: str) -> str:
    return f'<span class="badge"><span class="dot {dot_class}"></span>{text}</span>'


def resolve_data_path() -> Path:
    app_dir = Path(__file__).parent
    expected = (app_dir / REL_DATA_PATH).resolve()
    data_dir = app_dir / "data"
    if expected.exists() and expected.is_file():
        return expected
    if data_dir.exists() and data_dir.is_dir():
        cands = sorted([x for x in data_dir.glob("*.xlsx") if x.is_file()])
        if cands:
            return cands[0]
    raise FileNotFoundError("Não encontrei o Excel. Esperado: data/pa.xlsx")


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
    return {"total": total, "execd": execd, "running": running, "open": open_, "overdue": overdue, "completion": completion, "penalty": penalty, "health": health}


def led_gauge(value: float, label: str, bad_th: float, warn_th: float, segments: int = 28):
    v = float(max(0.0, min(100.0, value)))
    start_deg = 210
    sweep_deg = 240
    width = sweep_deg / segments
    theta = [start_deg - (sweep_deg * i / segments) for i in range(segments)]
    seg_vals = [100.0 * i / segments for i in range(segments)]
    active = [sv < v for sv in seg_vals]
    zone_colors = []
    for sv in seg_vals:
        if sv < bad_th:
            zone_colors.append(BAD)
        elif sv < warn_th:
            zone_colors.append(WARN)
        else:
            zone_colors.append(GOOD)
    inactive_cols = [_rgba(c, 0.18) for c in zone_colors]
    active_cols_neon = [_rgba(NEON, 0.94) if a else "rgba(0,0,0,0)" for a in active]
    active_cols_zone = [_rgba(c, 0.35) if a else "rgba(0,0,0,0)" for a, c in zip(active, zone_colors)]
    r_outer = 1.0
    thickness = 0.22
    r_inner = r_outer - thickness
    fig = go.Figure()
    fig.add_trace(go.Barpolar(r=[thickness] * segments, theta=theta, width=[width * 0.92] * segments, base=[r_inner] * segments,
                              marker_color=inactive_cols, marker_line_color="rgba(255,255,255,0.05)", marker_line_width=1, hoverinfo="skip"))
    fig.add_trace(go.Barpolar(r=[thickness * 0.98] * segments, theta=theta, width=[width * 0.92] * segments, base=[r_inner] * segments,
                              marker_color=active_cols_zone, marker_line_color="rgba(255,255,255,0.00)", hoverinfo="skip"))
    fig.add_trace(go.Barpolar(r=[thickness * 1.06] * segments, theta=theta, width=[width * 0.86] * segments, base=[r_inner - 0.01] * segments,
                              marker_color=active_cols_neon, marker_line_color=_rgba(NEON, 0.22), marker_line_width=1, hoverinfo="skip"))
    needle_deg = start_deg - (v / 100.0) * sweep_deg
    fig.add_trace(go.Scatterpolar(r=[0.0, r_inner + thickness * 0.85], theta=[needle_deg, needle_deg], mode="lines",
                                  line=dict(color=_rgba(SAFETY, 0.95), width=6), hoverinfo="skip"))
    fig.add_trace(go.Scatterpolar(r=[0.0], theta=[0], mode="markers",
                                  marker=dict(size=18, color="rgba(0,0,0,0.65)", line=dict(color=_rgba(NEON, 0.40), width=3)),
                                  hoverinfo="skip"))
    fig.add_annotation(x=0.5, y=0.42, xref="paper", yref="paper",
                       text=f"<span style='font-size:58px; font-weight:1000; color:rgba(255,255,255,0.98);'>{v:.0f}%</span>", showarrow=False)
    fig.add_annotation(x=0.5, y=0.29, xref="paper", yref="paper",
                       text=f"<span style='font-size:13px; color:rgba(230,245,255,0.72); letter-spacing:0.6px; text-transform:uppercase;'>{label}</span>", showarrow=False)
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                      polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=False, range=[0, 1.1]), angularaxis=dict(visible=False)))
    return fig


def render_hud(fig, title: str, subtitle: str = "", height: int = 455):
    html = fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displayModeBar": False})
    components.html(
        f"<div class='hud'><div style='font-weight:1000; margin:2px 0 4px 6px; text-transform:uppercase;'>{title}</div>"
        f"<div style='margin:0 0 10px 6px; color:rgba(230,245,255,0.58); font-size:12px;'>{subtitle}</div>"
        f"<div style='height:{height-88}px; margin-top:-10px;'>{html}</div></div>",
        height=height,
        scrolling=False,
    )


def pareto_chart(df: pd.DataFrame, col: str, title: str):
    if col not in df.columns or len(df) == 0:
        return None
    g = df.groupby(col, dropna=False).size().reset_index(name="Qtd").sort_values("Qtd", ascending=False)
    g[col] = g[col].fillna("—").astype(str)
    total = g["Qtd"].sum()
    g["Acumulado_%"] = (g["Qtd"].cumsum() / total) * 100 if total else 0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=g[col], y=g["Qtd"], name="Qtd", marker=dict(color=AI_BLUE, line=dict(color="#BFF3FF", width=1.2)), opacity=0.96))
    fig.add_trace(go.Scatter(x=g[col], y=g["Acumulado_%"], name="Acumulado %", mode="lines+markers", yaxis="y2",
                             line=dict(color="#FFE06A", width=3), marker=dict(size=8, color="#FFE06A")))
def pareto_chart(df: pd.DataFrame, col: str, title: str):
    if col not in df.columns or len(df) == 0:
        return None

    g = (
        df.groupby(col, dropna=False)
        .size()
        .reset_index(name="Qtd")
        .sort_values("Qtd", ascending=False)
    )
    g[col] = g[col].fillna("—").astype(str)

    total = g["Qtd"].sum()
    g["Acumulado_%"] = (g["Qtd"].cumsum() / total) * 100 if total else 0

    fig = go.Figure()

    # BARRAS - CINZA GRAFITE / PADRÃO IA
    fig.add_trace(
        go.Bar(
            x=g[col],
            y=g["Qtd"],
            name="Qtd",
            marker=dict(
                color="#5F6672",          # cinza grafite
                line=dict(color="#AEB6C2", width=1.2)
            ),
            opacity=0.96,
            text=g["Qtd"],
            textposition="outside",
            textfont=dict(color="white", size=12),
        )
    )

    # LINHA ACUMULADA
    fig.add_trace(
        go.Scatter(
            x=g[col],
            y=g["Acumulado_%"],
            name="Acumulado %",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="#FFD54A", width=3),   # amarelo tecnológico
            marker=dict(size=8, color="#FFD54A"),
        )
    )

    if pareto_bg_uri:
        fig.add_layout_image(
            dict(
                source=pareto_bg_uri,
                xref="paper",
                yref="paper",
                x=1.0,
                y=1.0,
                sizex=1.0,
                sizey=1.0,
                xanchor="right",
                yanchor="top",
                sizing="stretch",
                opacity=0.12,   # menor opacidade para não atrapalhar leitura
                layer="below",
            )
        )

    fig.update_layout(
        title=dict(
    text=title,
    font=dict(
        size=20,
        color="white",
        family="Arial Black"
    ),
    x=0.02
),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(35,40,48,0.18)",   # grafite leve
        font=dict(color="white", size=12),
        margin=dict(l=10, r=10, t=50, b=110),
        height=560,
        legend=dict(
            orientation="h",
            y=1.10,
            x=0,
            font=dict(size=11)
        ),
        xaxis=dict(
            title="",
            tickangle=-20,                 # melhora leitura
            showgrid=False,
            tickfont=dict(size=11, color="white"),
            automargin=True,
        ),
        yaxis=dict(
            title="Quantidade",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            tickfont=dict(size=11, color="white"),
            title_font=dict(color="white"),
        ),
        yaxis2=dict(
            title="Acumulado %",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
            ticksuffix="%",
            tickfont=dict(size=11, color="white"),
            title_font=dict(color="white"),
        ),
    )

    return fig


@st.cache_data(show_spinner=False)
def load_from_repo() -> dict:
    excel_path = resolve_data_path()
    with open(excel_path, "rb") as f:
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
    table.columns = [str(c).strip() for c in table.columns]
    rename = {}
    for c in table.columns:
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
        table["Atrasada_calc"] = table["Prazo_dt"].notna() & (table["Prazo_dt"] < today)
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
    return {"meta": meta, "table": table, "excel_path": str(excel_path)}


payload = load_from_repo()
meta = payload["meta"]
table = payload["table"].copy()
excel_path_used = payload.get("excel_path", "—")

with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.markdown(pill("neon", "Fonte fixa: data/pa.xlsx"), unsafe_allow_html=True)
    st.caption("Atualize o arquivo no GitHub e o painel lê sempre o último.")
    st.caption(f"📌 Lendo: {excel_path_used}")
    st.divider()


def safe_unique(col):
    if col in table.columns:
        vals = [v for v in table[col].dropna().astype(str).unique().tolist() if str(v).strip()]
        return sorted(vals)
    return []


status_opts = safe_unique("Status")
setor_opts = safe_unique("Setor")
resp_opts = safe_unique("Responsável")
ind_opts = safe_unique("Indicador")

with st.sidebar:
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

st.markdown(
    f'''
<div class="titlebar">
  <div class="big-title">PA • GEMBA BOARD ANDON</div>
  <div class="subtitle">
    Fonte fixa: <b>data/pa.xlsx</b> • Assunto: <b>{meta.get("Assunto","—")}</b> •
    Abertura: <b>{meta.get("Data de abertura","—")}</b> •
    Atualização (planilha): <b>{meta.get("Data de atualização","—")}</b> •
    Responsável: <b>{meta.get("Responsável do PA","—")}</b>
  </div>
  <div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">
    {pill("good","Executado")}
    {pill("warn","Em execução")}
    {pill("bad","Atraso")}
    {pill("info","Abertas")}
    {pill("neon","Indústria 4.0")}
  </div>
</div>
''',
    unsafe_allow_html=True,
)

if m["overdue"] > 0:
    st.error(f"🔴 ANDON: {m['overdue']} ação(ões) com PRAZO VENCIDO no filtro atual.")
else:
    st.success("🟢 ANDON: Nenhuma ação com prazo vencido no filtro atual.")

st.divider()

cols = st.columns(6)

def kpi_html(label, value, sub=""):
    return f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{value}</div><div class='sub'>{sub}</div></div>"

cols[0].markdown(kpi_html("Total", m["total"], "Escopo selecionado"), unsafe_allow_html=True)
cols[1].markdown(kpi_html("Executadas", m["execd"], "Fechadas"), unsafe_allow_html=True)
cols[2].markdown(kpi_html("Em execução", m["running"], "Ativas"), unsafe_allow_html=True)
cols[3].markdown(kpi_html("Abertas", m["open"], "Backlog"), unsafe_allow_html=True)
cols[4].markdown(kpi_html("Atrasadas (calc.)", m["overdue"], "Prazo vencido"), unsafe_allow_html=True)
cols[5].markdown(kpi_html("Conclusão", f"{m['completion']:.1f}%", "Executadas/Total"), unsafe_allow_html=True)

st.progress(min(max(m["completion"] / 100, 0.0), 1.0), text=f"Conclusão do PA: {m['completion']:.1f}%")
st.divider()

g1, g2 = st.columns(2)
with g1:
    render_hud(led_gauge(m["health"], "Saúde do PA", 50, 75, 28), "Velocímetro LED • Saúde do PA", subtitle=f"Penalidade por atrasos: {m['penalty']:.1f} pts")
with g2:
    render_hud(led_gauge(m["completion"], "Conclusão do PA", 40, 70, 28), "Velocímetro LED • Conclusão do PA", subtitle="Gestão à vista (ANDON)")

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
        render_hud(led_gauge(ms["health"], f"Saúde • {sel}", 50, 75, 28), f"Setor: {sel} • Saúde (LED)", subtitle=f"Atrasos: {ms['overdue']} • Penalidade: {ms['penalty']:.1f} pts")
    with s2:
        render_hud(led_gauge(ms["completion"], f"Conclusão • {sel}", 40, 70, 28), f"Setor: {sel} • Conclusão (LED)", subtitle="Monitoramento turno a turno")

st.divider()

left, right = st.columns([1.05, 0.95])

with left:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Prioridades (críticas)")
    crit = f[f["Atrasada_calc"] == True].copy() if "Atrasada_calc" in f.columns else f.iloc[0:0].copy()
    if "Dias_para_prazo" in crit.columns:
        crit = crit.sort_values(["Dias_para_prazo"], ascending=True)
    if len(crit):
        show_cols = [x for x in ["Ação", "Setor", "Responsável", "Prazo", "Status", "Dias_para_prazo"] if x in crit.columns]
        st.dataframe(crit[show_cols].head(14), use_container_width=True, height=380)
    else:
        st.success("Sem ações críticas no filtro atual.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='pareto-panel'>", unsafe_allow_html=True)
    fig_pareto = pareto_chart(f, "Indicador", "Pareto por Indicador (Qtd)")
    if fig_pareto is not None:
        st.plotly_chart(fig_pareto, use_container_width=True)
    else:
        st.info("Sem dados suficientes para o Pareto.")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.subheader("Quadro Kanban (Gestão à vista)")
st.caption("Abertas → Em execução → Executadas. Atrasadas = foco do turno.")

board_cols = st.columns(4)
board = [
    ("Abertas", "info", board_cols[0], "Aberta", "open"),
    ("Em execução", "warn", board_cols[1], "Em execução", "run"),
    ("Atrasadas", "bad", board_cols[2], "Atrasada", "late"),
    ("Executadas", "good", board_cols[3], "Executado", "done"),
]

def render_col(df, container, title, dot, status_value, css_class):
    with container:
        st.markdown(pill(dot, title), unsafe_allow_html=True)
        subset = df[df["Status"] == status_value].copy() if "Status" in df.columns else df.iloc[0:0].copy()
        if "Prazo_dt" in subset.columns:
            subset = subset.sort_values(["Prazo_dt"], ascending=True)
        if len(subset) == 0:
            st.markdown(f"<div class='card {css_class}'><div class='card-small'>Sem itens</div></div>", unsafe_allow_html=True)
            return
        for _, r in subset.head(12).iterrows():
            acao = str(r.get("Ação", "")).strip()
            setor = str(r.get("Setor", "")).strip()
            resp = str(r.get("Responsável", "")).strip()
            prazo = str(r.get("Prazo", "")).strip()
            dias = r.get("Dias_para_prazo", None)
            dias_txt = f"{int(dias):+}d" if isinstance(dias, (int, float)) and pd.notna(dias) else ""
            line2 = " • ".join([x for x in [setor, resp, dias_txt] if x and x != "nan"])
            st.markdown(
                f"<div class='card {css_class}' style='margin-top:10px;'>"
                f"<div class='card-title'>{acao or '—'}</div>"
                f"<div class='card-small'>{line2 or '—'}</div>"
                f"<div class='card-small'>Prazo: <b>{prazo or '—'}</b></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

for title, dot, cont, status_value, css_class in board:
    render_col(f, cont, title, dot, status_value, css_class)

st.divider()
st.subheader("Lista completa (filtro aplicado)")
show_cols = [x for x in ["Causa", "Ação", "Indicador", "Setor", "Responsável", "Prazo", "Status", "Dias_para_prazo"] if x in f.columns]
st.dataframe(f[show_cols], use_container_width=True, height=560)

st.subheader("Exportar")
csv = f.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Baixar CSV (filtro aplicado)", data=csv, file_name="pa_filtrado.csv", mime="text/csv")
