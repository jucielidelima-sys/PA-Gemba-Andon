import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

REL_DATA_PATH = Path("data") / "pa.xlsx"  # fonte fixa

st.set_page_config(page_title="PA • Gemba Board ANDON", layout="wide")

st.markdown("""
<style>
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="stSidebarContent"]{
  background:#000000 !important;
  color: rgba(255,255,255,0.92) !important;
}
[data-testid="stHeader"]{background:transparent !important;}
* { color: rgba(255,255,255,0.92); }

:root{
  --line: rgba(255,255,255,0.12);
  --muted: rgba(255,255,255,0.62);
  --neon:#00e5ff;
  --safety:#ffd60a;
  --good:#00c853;
  --warn:#ff9100;
  --bad:#ff1744;
  --info:#40c4ff;
}

.block-container{padding-top:1.0rem; padding-bottom:2.2rem; max-width: 1700px;}
section[data-testid="stSidebar"]{border-right:1px solid var(--line);}

div[data-testid="stDataFrame"]{
  background: rgba(0,0,0,0.90) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 14px !important;
  padding: 6px !important;
}
div[data-testid="stDataFrame"] .ag-root-wrapper,
div[data-testid="stDataFrame"] .ag-root,
div[data-testid="stDataFrame"] .ag-body-viewport,
div[data-testid="stDataFrame"] .ag-header,
div[data-testid="stDataFrame"] .ag-center-cols-container,
div[data-testid="stDataFrame"] .ag-row{
  background: rgba(0,0,0,0.90) !important;
}
div[data-testid="stDataFrame"] .ag-header-cell,
div[data-testid="stDataFrame"] .ag-cell{
  color: rgba(255,255,255,0.90) !important;
  border-color: rgba(255,255,255,0.10) !important;
}
div[data-testid="stDataFrame"] .ag-row:hover{
  background: rgba(0,229,255,0.08) !important;
}

.titlebar{
  border:1px solid var(--line);
  border-radius:18px;
  padding:16px 18px;
  background:
    radial-gradient(900px 260px at 0% 0%, rgba(0,229,255,0.18), rgba(0,0,0,0)),
    radial-gradient(700px 220px at 100% 0%, rgba(255,214,10,0.14), rgba(0,0,0,0)),
    linear-gradient(180deg, rgba(10,15,34,0.95), rgba(0,0,0,0.92));
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
  background: linear-gradient(90deg, rgba(0,229,255,0), rgba(0,229,255,0.95), rgba(0,229,255,0));
  opacity: 0.85;
}
.big-title{
  font-size:34px;
  font-weight:1000;
  letter-spacing:1.0px;
  text-transform: uppercase;
  text-shadow: 0 0 26px rgba(0,229,255,0.26);
}
.subtitle{ color: var(--muted); font-size:12px; margin-top:4px; }

.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border-radius:999px; font-size:12px;
  border:1px solid var(--line);
  background: rgba(255,255,255,0.03);
  color: var(--muted);
}
.dot{width:9px; height:9px; border-radius:999px; display:inline-block;}
.dot.good{background:var(--good);}
.dot.warn{background:var(--warn);}
.dot.bad{background:var(--bad);}
.dot.info{background:var(--info);}
.dot.safety{background:var(--safety);}
.dot.neon{background:var(--neon); box-shadow: 0 0 12px rgba(0,229,255,0.75);}

.kpi{
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px 16px;
  background:
    radial-gradient(500px 180px at 0% 0%, rgba(0,229,255,0.12), rgba(0,0,0,0)),
    linear-gradient(180deg, rgba(255,214,10,0.06), rgba(0,0,0,0));
}
.kpi .label{color:var(--muted); font-size:12px;}
.kpi .value{font-size:28px; font-weight:1000; margin-top:4px;}
.kpi .sub{color:var(--muted); font-size:12px; margin-top:4px;}

.card{
  border:1px solid rgba(255,255,255,0.12);
  border-radius:16px;
  padding:12px 12px;
  background: rgba(10,15,34,0.62);
  box-shadow: 0 12px 24px rgba(0,0,0,0.55);
}
.card-title{font-weight:900; margin-bottom:6px; color: rgba(255,255,255,0.96);}
.card-small{color:var(--muted); font-size:12px;}

.hud{
  border-radius: 22px;
  border: 1px solid rgba(255,255,255,0.12);
  background:
    radial-gradient(520px 220px at 0% 0%, rgba(0,229,255,0.20), rgba(0,0,0,0)),
    radial-gradient(520px 220px at 100% 100%, rgba(255,214,10,0.10), rgba(0,0,0,0)),
    rgba(255,255,255,0.03);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  position: relative;
  padding: 12px 12px 8px 12px;
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(0,229,255,0.14) inset,
    0 18px 40px rgba(0,0,0,0.65);
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

def resolve_data_path() -> Path:
    app_dir = Path(__file__).parent
    expected = (app_dir / REL_DATA_PATH).resolve()
    data_dir = app_dir / "data"

    if data_dir.exists() and data_dir.is_file():
        raise RuntimeError("Erro: 'data' está como ARQUIVO. Apague o arquivo 'data' e crie a pasta 'data/' com 'pa.xlsx'.")

    if expected.exists() and expected.is_file():
        return expected

    if data_dir.exists() and data_dir.is_dir():
        cands = sorted([x for x in data_dir.glob("*.xlsx") if x.is_file()])
        if cands:
            return cands[0]

    cands = sorted([x for x in app_dir.glob("*.xlsx") if x.is_file()])
    if cands:
        return cands[0]

    listing = [x.name + ("/" if x.is_dir() else "") for x in sorted(app_dir.iterdir(), key=lambda z: z.name.lower())]
    raise FileNotFoundError(
        "Não encontrei o Excel. Esperado: 'data/pa.xlsx'.\n"
        f"Diretório do app: {app_dir}\n"
        f"Conteúdo: {listing}\n"
        "Coloque o arquivo em 'data/pa.xlsx' e faça commit/push."
    )

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
    return dict(total=total, execd=execd, running=running, open=open_, overdue=overdue, completion=completion, penalty=penalty, health=health)

def pill(dot_class: str, text: str) -> str:
    return f'<span class="badge"><span class="dot {dot_class}"></span>{text}</span>'

def _rgba(hex_color: str, alpha: float) -> str:
    c = hex_color.lstrip("#")
    r = int(c[0:2], 16); g = int(c[2:4], 16); b = int(c[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

NEON="#00e5ff"; GOOD="#00c853"; WARN="#ff9100"; BAD="#ff1744"; SAFETY="#ffd60a"

def led_gauge(value: float, label: str, bad_th: float, warn_th: float, segments: int = 26):
    v = float(max(0.0, min(100.0, value)))
    start_deg=210; sweep_deg=240
    width=sweep_deg/segments
    theta=[start_deg-(sweep_deg*i/segments) for i in range(segments)]
    seg_vals=[100.0*i/segments for i in range(segments)]
    active=[sv < v for sv in seg_vals]
    zone_colors=[]
    for sv in seg_vals:
        zone_colors.append(BAD if sv < bad_th else WARN if sv < warn_th else GOOD)

    inactive=[_rgba(c,0.18) for c in zone_colors]
    active_neon=[_rgba(NEON,0.92) if a else "rgba(0,0,0,0)" for a in active]
    active_zone=[_rgba(c,0.35) if a else "rgba(0,0,0,0)" for a,c in zip(active, zone_colors)]

    r_outer=1.0; thickness=0.22; r_inner=r_outer-thickness
    base=[r_inner]*segments

    fig=go.Figure()
    fig.add_trace(go.Barpolar(r=[thickness]*segments, theta=theta, width=[width*0.92]*segments, base=base,
                             marker_color=inactive, marker_line_color="rgba(255,255,255,0.06)", marker_line_width=1,
                             hoverinfo="skip"))
    fig.add_trace(go.Barpolar(r=[thickness*0.98]*segments, theta=theta, width=[width*0.92]*segments, base=base,
                             marker_color=active_zone, marker_line_color="rgba(255,255,255,0.00)", hoverinfo="skip"))
    fig.add_trace(go.Barpolar(r=[thickness*1.06]*segments, theta=theta, width=[width*0.86]*segments, base=[r_inner-0.01]*segments,
                             marker_color=active_neon, marker_line_color=_rgba(NEON,0.22), marker_line_width=1, hoverinfo="skip"))

    needle_deg=start_deg-(v/100.0)*sweep_deg
    fig.add_trace(go.Scatterpolar(r=[0.0, r_inner+thickness*0.85], theta=[needle_deg, needle_deg], mode="lines",
                                  line=dict(color=_rgba(SAFETY,0.95), width=6), hoverinfo="skip"))
    fig.add_trace(go.Scatterpolar(r=[0.0], theta=[0], mode="markers",
                                  marker=dict(size=18, color="rgba(0,0,0,0.65)", line=dict(color=_rgba(NEON,0.35), width=3)),
                                  hoverinfo="skip"))

    fig.add_annotation(x=0.5,y=0.42,xref="paper",yref="paper",
                       text=f"<span style='font-size:58px; font-weight:1000; color:rgba(255,255,255,0.96);'>{v:.0f}%</span>",
                       showarrow=False)
    fig.add_annotation(x=0.5,y=0.29,xref="paper",yref="paper",
                       text=f"<span style='font-size:13px; color:rgba(255,255,255,0.62); letter-spacing:0.6px; text-transform:uppercase;'>{label}</span>",
                       showarrow=False)

    fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                      polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=False, range=[0,1.1]),
                                 angularaxis=dict(visible=False)))
    return fig

def render_hud(fig, title: str, subtitle: str = "", height: int = 455):
    html = fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displayModeBar": False})
    components.html(f"<div class='hud' style='padding:12px 12px 6px 12px;'><div style='font-weight:1000;margin:2px 0 4px 6px;text-transform:uppercase;'>{title}</div><div style='margin:0 0 10px 6px;color:var(--muted);font-size:12px;'>{subtitle}</div><div style='height:{height-88}px;margin-top:-10px;'>{html}</div></div>",
                    height=height, scrolling=False)

@st.cache_data(show_spinner=False)
def load_from_repo() -> dict:
    excel_path = resolve_data_path()
    with open(excel_path, "rb") as f:
        file_bytes = f.read()
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="PA", header=None).dropna(how="all")

    header_row=None
    for i,row in raw.iterrows():
        rs=row.astype(str)
        if rs.str.contains("Ação",case=False,na=False).any() and rs.str.contains("Indicador",case=False,na=False).any():
            header_row=i; break
    if header_row is None:
        raise RuntimeError("Não encontrei o cabeçalho da tabela de ações (Ação/Indicador).")

    table=pd.read_excel(io.BytesIO(file_bytes), sheet_name="PA", header=header_row).dropna(how="all").copy()
    table.columns=[_norm(c) for c in table.columns]

    rename={}
    for c in table.columns:
        cl=c.lower()
        if "causa" in cl: rename[c]="Causa"
        elif "ação" in cl or "acao" in cl: rename[c]="Ação"
        elif "indicador" in cl: rename[c]="Indicador"
        elif "setor" in cl: rename[c]="Setor"
        elif "respons" in cl: rename[c]="Responsável"
        elif "prazo" in cl: rename[c]="Prazo"
        elif "status" in cl: rename[c]="Status"
        elif "observ" in cl: rename[c]="Observações"
    table=table.rename(columns=rename)

    wanted=["Causa","Ação","Indicador","Setor","Responsável","Prazo","Status","Observações"]
    cols=[c for c in wanted if c in table.columns]
    table=table[cols].copy()

    if "Status" in table.columns:
        table["Status"]=table["Status"].map(_norm_status)

    if "Prazo" in table.columns:
        table["Prazo_dt"]=pd.to_datetime(table["Prazo"], errors="coerce", dayfirst=True).dt.date
    else:
        table["Prazo_dt"]=pd.NaT

    today=date.today()
    if "Status" in table.columns:
        table["Atrasada_calc"]=(table["Prazo_dt"].notna()) & (table["Prazo_dt"] < today) & (~table["Status"].isin(CLOSED_STATUSES))
    else:
        table["Atrasada_calc"]=(table["Prazo_dt"].notna()) & (table["Prazo_dt"] < today)

    table["Dias_para_prazo"]=table["Prazo_dt"].apply(lambda d: (d-today).days if pd.notna(d) else None)

    meta={}
    for _,r in raw.head(30).iterrows():
        left=str(r.iloc[1]) if len(r)>1 else ""
        val=str(r.iloc[2]) if len(r)>2 else ""
        if "Data de abertura" in left: meta["Data de abertura"]=val
        if "Data de atualização" in left: meta["Data de atualização"]=val
        if "Assunto" in left: meta["Assunto"]=val
        if "Responsável" in left: meta["Responsável do PA"]=val

    return {"meta": meta, "table": table, "excel_path": str(excel_path)}

payload=load_from_repo()
meta=payload["meta"]; table=payload["table"].copy(); excel_path_used=payload.get("excel_path","—")

with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.markdown(pill("safety","Fonte fixa: data/pa.xlsx"), unsafe_allow_html=True)
    st.caption("Atualize o arquivo no GitHub e o painel lê sempre o último.")
    st.caption(f"📌 Lendo: {excel_path_used}")
    st.divider()

def safe_unique(col):
    if col in table.columns:
        vals=[v for v in table[col].dropna().astype(str).unique().tolist() if v.strip()]
        return sorted(vals)
    return []

status_opts=safe_unique("Status")
setor_opts=safe_unique("Setor")
resp_opts=safe_unique("Responsável")
ind_opts=safe_unique("Indicador")

with st.sidebar:
    f_status=st.multiselect("Status", status_opts, default=status_opts)
    f_setor=st.multiselect("Setor", setor_opts, default=setor_opts)
    f_resp=st.multiselect("Responsável", resp_opts, default=resp_opts)
    f_ind=st.multiselect("Indicador", ind_opts, default=ind_opts)
    only_overdue=st.checkbox("Somente atrasadas (calculado)", value=False)

    has_dates=table["Prazo_dt"].notna().any()
    if has_dates:
        min_d=table["Prazo_dt"].dropna().min()
        max_d=table["Prazo_dt"].dropna().max()
        f_range=st.date_input("Janela de prazos", value=(min_d, max_d))
    else:
        f_range=None

f=table.copy()
if "Status" in f.columns: f=f[f["Status"].isin(f_status)]
if "Setor" in f.columns: f=f[f["Setor"].astype(str).isin(f_setor)]
if "Responsável" in f.columns: f=f[f["Responsável"].astype(str).isin(f_resp)]
if "Indicador" in f.columns: f=f[f["Indicador"].astype(str).isin(f_ind)]
if only_overdue: f=f[f["Atrasada_calc"]==True]
if f_range and isinstance(f_range,(list,tuple)) and len(f_range)==2:
    a,b=f_range
    f=f[(f["Prazo_dt"].isna()) | ((f["Prazo_dt"]>=a)&(f["Prazo_dt"]<=b))]

m=compute_metrics(f)

st.markdown(f"""
<div class="titlebar">
  <div class="big-title">PA • Gemba Board ANDON</div>
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
""", unsafe_allow_html=True)

st.error(f"🔴 ANDON: {m['overdue']} ação(ões) com PRAZO VENCIDO no filtro atual.") if m["overdue"]>0 else st.success("🟢 ANDON: Nenhuma ação com prazo vencido no filtro atual.")

st.divider()
cols=st.columns(6)
def kpi_html(label,value,sub=""):
    return f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{value}</div><div class='sub'>{sub}</div></div>"
cols[0].markdown(kpi_html("Total", m["total"], "Escopo selecionado"), unsafe_allow_html=True)
cols[1].markdown(kpi_html("Executadas", m["execd"], "Fechadas"), unsafe_allow_html=True)
cols[2].markdown(kpi_html("Em execução", m["running"], "Ativas"), unsafe_allow_html=True)
cols[3].markdown(kpi_html("Abertas", m["open"], "Backlog"), unsafe_allow_html=True)
cols[4].markdown(kpi_html("Atrasadas (calc.)", m["overdue"], "Prazo vencido"), unsafe_allow_html=True)
cols[5].markdown(kpi_html("Conclusão", f'{m["completion"]:.1f}%', "Executadas/Total"), unsafe_allow_html=True)
st.progress(min(max(m["completion"]/100,0.0),1.0), text=f'Conclusão do PA: {m["completion"]:.1f}%')

st.divider()
g1,g2=st.columns(2)
with g1:
    render_hud(led_gauge(m["health"], "Saúde do PA", 50, 75, 26), "Velocímetro LED • Saúde do PA", f"Painel digital • Penalidade: {m['penalty']:.1f} pts")
with g2:
    render_hud(led_gauge(m["completion"], "Conclusão do PA", 40, 70, 26), "Velocímetro LED • Conclusão do PA", "Gestão à vista (ANDON)")

st.divider()
st.subheader("Velocímetro por Setor (dropdown)")
setores_current=sorted([s for s in f.get("Setor", pd.Series([],dtype=str)).dropna().astype(str).unique().tolist() if str(s).strip()])
if not setores_current:
    st.info("Não há coluna Setor no arquivo ou não existem setores no filtro atual.")
else:
    sel=st.selectbox("Selecione o Setor", options=setores_current, index=0)
    f_set=f[f["Setor"].astype(str)==str(sel)].copy()
    ms=compute_metrics(f_set)
    s1,s2=st.columns(2)
    with s1:
        render_hud(led_gauge(ms["health"], f"Saúde • {sel}", 50, 75, 26), f"Setor: {sel} • Saúde (LED)", f"Atrasos: {ms['overdue']} • Penalidade: {ms['penalty']:.1f} pts")
    with s2:
        render_hud(led_gauge(ms["completion"], f"Conclusão • {sel}", 40, 70, 26), f"Setor: {sel} • Conclusão (LED)", "Monitoramento turno a turno")

st.divider()
st.subheader("Quadro Kanban (Gestão à vista)")
st.caption("Abertas → Em execução → Executadas. Atrasadas = foco do turno.")
board_cols=st.columns(4)
board=[("Abertas","info",board_cols[0],"Aberta"),("Em execução","warn",board_cols[1],"Em execução"),("Atrasadas","bad",board_cols[2],"Atrasada"),("Executadas","good",board_cols[3],"Executado")]

def render_col(df, container, title, dot, status_value):
    with container:
        st.markdown(pill(dot,title), unsafe_allow_html=True)
        subset=df[df["Status"]==status_value].copy() if "Status" in df.columns else df.iloc[0:0].copy()
        subset=subset.sort_values(["Prazo_dt"], ascending=True) if "Prazo_dt" in subset.columns else subset
        if len(subset)==0:
            st.markdown("<div class='card'><div class='card-small'>Sem itens</div></div>", unsafe_allow_html=True); return
        for _,r in subset.head(10).iterrows():
            acao=str(r.get("Ação","")).strip()
            setor=str(r.get("Setor","")).strip()
            resp=str(r.get("Responsável","")).strip()
            prazo=str(r.get("Prazo","")).strip()
            dias=r.get("Dias_para_prazo", None)
            dias_txt=f"{int(dias):+}d" if isinstance(dias,(int,float)) and pd.notna(dias) else ""
            line2=" • ".join([x for x in [setor, resp, dias_txt] if x and x!="nan"])
            st.markdown(f"<div class='card' style='margin-top:10px;'><div class='card-title'>{acao or '—'}</div><div class='card-small'>{line2 or '—'}</div><div class='card-small'>Prazo: <b>{prazo or '—'}</b></div></div>", unsafe_allow_html=True)

for title,dot,cont,status_value in board:
    render_col(f, cont, title, dot, status_value)

st.divider()
st.subheader("Lista completa (filtro aplicado)")
show_cols=[x for x in ["Causa","Ação","Indicador","Setor","Responsável","Prazo","Status","Dias_para_prazo"] if x in f.columns]
st.dataframe(f[show_cols], use_container_width=True, height=520)

st.subheader("Exportar")
csv=f.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Baixar CSV (filtro aplicado)", data=csv, file_name="pa_filtrado.csv", mime="text/csv")
