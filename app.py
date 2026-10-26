"""FAEPO | Sistema piloto de demanda académica.

Todos los datos son FICTICIOS. La información solo vive en la sesión abierta.
No introducir documentos ni información institucional real en servicios públicos.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
import html
import re
import requests

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="FAEPO | Gestión de solicitudes", page_icon="📘", layout="wide", initial_sidebar_state="expanded")

# Datos artificiales. No son comunicaciones oficiales reales.
DEMO = [
    dict(gs="GS-DEMO-0001", fecha="2026-10-05", unidad="ESCUELA ALFA", vigencia=2027, programa="Curso Instructor Policial", cupos=8, asignados=3, estado="Parcialmente atendida", nota="Ejemplo de demanda para planeación."),
    dict(gs="GS-DEMO-0001", fecha="2026-10-05", unidad="ESCUELA ALFA", vigencia=2027, programa="Curso Instructor Sistema Táctico Básico Policial", cupos=6, asignados=0, estado="Pendiente de programación", nota="Convocatoria por confirmar."),
    dict(gs="GS-DEMO-0002", fecha="2026-10-08", unidad="UNIDAD BRAVO", vigencia=2027, programa="Curso Instructor Policial", cupos=4, asignados=0, estado="Pendiente de programación", nota="Solicitud de cupos, sin nombres individuales."),
    dict(gs="GS-DEMO-0002", fecha="2026-10-08", unidad="UNIDAD BRAVO", vigencia=2027, programa="Curso Instructor de Tiro", cupos=10, asignados=2, estado="Parcialmente atendida", nota="Pendiente de nueva convocatoria."),
    dict(gs="GS-DEMO-0003", fecha="2026-10-15", unidad="ESCUELA CHARLIE", vigencia=2027, programa="Curso Instructor de Tiro", cupos=5, asignados=0, estado="Pendiente de programación", nota="Demostración."),
    dict(gs="GS-DEMO-0003", fecha="2026-10-15", unidad="ESCUELA CHARLIE", vigencia=2027, programa="Diplomado en Actualización para el Desempeño Docente", cupos=6, asignados=6, estado="Atendida", nota="Demostración de solicitud atendida."),
    dict(gs="GS-DEMO-0004", fecha="2026-10-19", unidad="UNIDAD DELTA", vigencia=2027, programa="Curso Instructor Policial", cupos=5, asignados=0, estado="Pendiente de programación", nota="Ejemplo ficticio."),
]
ESTADOS = ["Pendiente de programación", "Convocatoria disponible", "Parcialmente atendida", "Atendida", "Sin viabilidad"]
SCHEMA = list(DEMO[0].keys())
if "registros" not in st.session_state:
    st.session_state.registros = [dict(x) for x in DEMO]
if "catalogo" not in st.session_state:
    st.session_state.catalogo = sorted({x["programa"] for x in DEMO})
if "seccion" not in st.session_state:
    st.session_state.seccion = "Inicio"


# El piloto remoto consulta datos de demostración con la clave publicable.
# NO almacena credenciales en GitHub y NO autoriza escrituras públicas.
@st.cache_data(ttl=45, show_spinner=False)
def cargar_desde_supabase(url: str, clave: str):
    url = url.rstrip("/")
    headers = {"apikey": clave, "Accept": "application/json"}
    def leer(tabla):
        respuesta = requests.get(
            f"{url}/rest/v1/{tabla}",
            params={"select": "*", "limit": 1000},
            headers=headers, timeout=15,
        )
        respuesta.raise_for_status()
        return respuesta.json()
    comunicaciones = pd.DataFrame(leer("comunicaciones"))
    programas = pd.DataFrame(leer("programas"))
    solicitudes = pd.DataFrame(leer("solicitudes"))
    if any(frame.empty for frame in [comunicaciones, programas, solicitudes]):
        return []
    joined = solicitudes.merge(
        comunicaciones, left_on="comunicacion_id", right_on="id", suffixes=("_sol", "_com")
    ).merge(programas, left_on="programa_id", right_on="id", suffixes=("", "_prog"))
    rows = []
    for _, row in joined.iterrows():
        rows.append(dict(
            gs=str(row["numero_gs"]), fecha=str(row["fecha_solicitud"]),
            unidad=str(row["unidad_solicitante"]), vigencia=int(row["vigencia"]),
            programa=str(row["nombre"]), cupos=int(row["cupos_solicitados"]),
            asignados=int(row["cupos_asignados"]), estado=str(row["estado"]),
            nota=str(row.get("observaciones_sol", row.get("observaciones", "")) or ""),
        ))
    return rows

remote_enabled = False
remote_error = None
try:
    remote_url = st.secrets.get("SUPABASE_URL", "")
    remote_key = st.secrets.get("SUPABASE_PUBLISHABLE_KEY", "")
    if remote_url and remote_key:
        remote_enabled = True
        remote_rows = cargar_desde_supabase(remote_url, remote_key)
        st.session_state.registros = remote_rows
        st.session_state.catalogo = sorted({r["programa"] for r in remote_rows})
except Exception as error:
    remote_error = str(error)

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
.stApp { background:#F3F6FA; }
.block-container { padding-top:1.15rem; padding-bottom:2rem; max-width:1500px; }
header[data-testid="stHeader"] { background:rgba(243,246,250,.86); }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#112C49,#10395C 58%,#0A2845); }
section[data-testid="stSidebar"] * { color:#ECF4FD; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:6px 5px;border-radius:9px;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:#204E73;}
section[data-testid="stSidebar"] div[data-testid="stAlert"] {background:#193F5C;}
section[data-testid="stSidebar"] hr {border-color:#325575;}
div[data-testid="stMetric"] {background:white; padding:18px 20px;border-radius:13px; border:1px solid #DFE7F0;box-shadow:0px 3px 10px rgba(15,43,74,.035);}
div[data-testid="stMetricLabel"] {font-weight:600;color:#50667D;}
div[data-testid="stMetricValue"] {color:#12365A;font-size:1.8rem;}
h1,h2,h3 {color:#193C5D!important;letter-spacing:-.025em;}
h1 {font-size:1.62rem!important;font-weight:800!important;}
h2 {font-size:1.24rem!important;} h3 {font-size:1.05rem!important;}
.stButton button[kind="primary"], button[data-testid="stBaseButton-primary"] {background:#075D89; border-color:#075D89; color:white; border-radius:9px; font-weight:700;}
.stButton button[kind="secondary"] {border:1px solid #B9CADA;border-radius:9px;}
[data-testid="stDataFrame"] {border:1px solid #DFE7F0;border-radius:12px;overflow:hidden;}
[data-testid="stForm"] {background:white;border:1px solid #DCE6F0;border-radius:13px;padding:17px;}
[data-testid="stTabs"] button {font-weight:600;}
.faepo-head {background:linear-gradient(105deg,#102E4E,#105B80);color:white; padding:22px 26px;border-radius:13px;margin:0 0 14px;box-shadow:0 8px 24px rgba(9,42,73,.12);}
.faepo-head small{font-weight:700;letter-spacing:.11em;color:#B6DCEC;font-size:.69rem;}
.faepo-head strong{color:white;display:block;font-size:1.45rem;line-height:1.35;margin-top:5px;}
.faepo-head span{color:#D8E9F2;font-size:.82rem;}
.pill {display:inline-block;border-radius:999px;padding:4px 10px;font-size:11px;font-weight:700;background:#DFF1E6;color:#176143;}
.section-h {display:flex;justify-content:space-between;align-items:center;margin:12px 0 8px;font-weight:750;color:#183E60;font-size:1.02rem;}
.side-brand{padding:12px 8px 18px;border-bottom:1px solid #3A5A73;margin-bottom:14px;}
.side-brand b{font-size:1.17rem;color:white;}
.side-brand small{color:#BBD5E6;font-size:.75rem;}
.demo {background:#FFF9E9;border:1px solid #F1DDA4;border-radius:10px;padding:9px 14px;color:#76501A;font-size:.79rem;margin:7px 0 14px;}
.stPlotlyChart{background:white;border:1px solid #E0E8F1;border-radius:13px; padding:9px;}
</style>"""
st.markdown(STYLE, unsafe_allow_html=True)

def esc(s):
    return html.escape(str(s))

def df_all():
    return pd.DataFrame(st.session_state.registros, columns=SCHEMA)

def filtered(df: pd.DataFrame, term: str = "", year="Todas", status="Todos"):
    view = df.copy()
    if year != "Todas":
        view = view[view.vigencia == int(year)]
    if status != "Todos":
        view = view[view.estado == status]
    if term.strip():
        mask = view[["gs","unidad","programa"]].astype(str).apply(lambda c:c.str.contains(re.escape(term.strip()),case=False,regex=True)).any(axis=1)
        view = view[mask]
    return view

def table(view, cols=None):
    st.dataframe(view[cols or SCHEMA],hide_index=True,use_container_width=True,
                 column_config={"gs":"Comunicación GS","fecha":"Fecha","unidad":"Unidad solicitante","vigencia":"Vigencia","programa":"Programa académico", "cupos":st.column_config.NumberColumn("Cupos solicitados",format="%d"),"asignados":st.column_config.NumberColumn("Cupos asignados",format="%d"),"estado":"Estado","nota":"Observaciones"})

def export_excel(frame:pd.DataFrame):
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as writer:
        frame.rename(columns={"gs":"Comunicación GS","fecha":"Fecha","unidad":"Unidad","vigencia":"Vigencia","programa":"Programa","cupos":"Cupos solicitados","asignados":"Cupos asignados","estado":"Estado","nota":"Observaciones"}).to_excel(writer,index=False,sheet_name="Solicitudes")
        frame.groupby("programa",as_index=False).agg(cupos_solicitados=("cupos","sum"),cupos_asignados=("asignados","sum"),comunicaciones=("gs","nunique")).to_excel(writer,index=False,sheet_name="Resumen por programa")
        frame.groupby("gs",as_index=False).agg(programas=("programa","count"),cupos_solicitados=("cupos","sum"),cupos_asignados=("asignados","sum")).to_excel(writer,index=False,sheet_name="Resumen por GS")
        for ws in writer.book.worksheets:
            ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
            for col in ws.columns:
                letter=col[0].column_letter
                ws.column_dimensions[letter].width=min(48,max(14,max(len(str(c.value or "")) for c in col[:60])+3))
    return buf.getvalue()

def plot_bar(data, x, y, horizontal=False):
    fig=px.bar(data,x=x,y=y,orientation="h" if horizontal else "v",color_discrete_sequence=["#137BA5"],text_auto=True)
    fig.update_traces(marker_line_width=0,textposition="outside")
    fig.update_layout(paper_bgcolor="white",plot_bgcolor="white",font_color="#2A4A63",margin=dict(l=8,r=12,t=17,b=10),height=315,
                      xaxis_title=None,yaxis_title=None,showlegend=False)
    fig.update_yaxes(showgrid=True,gridcolor="#E8EEF5",zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig

with st.sidebar:
    st.markdown('<div class="side-brand"><b>▣ DIEPO | FAEPO</b><br><small>Control de solicitudes académicas</small></div>',unsafe_allow_html=True)
    sections=["Inicio","Comunicaciones GS","Programas académicos","Registrar solicitud","Gestionar cupos","Reportes y catálogo"]
    icons={"Inicio":"▦","Comunicaciones GS":"▤","Programas académicos":"▥","Registrar solicitud":"＋","Gestionar cupos":"✎","Reportes y catálogo":"▧"}
    current=st.radio("NAVEGACIÓN",sections,index=sections.index(st.session_state.seccion),format_func=lambda x:f'{icons[x]}   {x}')
    st.session_state.seccion=current
    st.divider()
    st.caption("PILOTO 3.0 · SOLO DATOS FICTICIOS")
    st.caption("Lectura compartida · registro y edición aún no habilitados.")

st.markdown('''<div class="faepo-head"><small>POLICÍA NACIONAL · DIRECCIÓN DE EDUCACIÓN POLICIAL</small><strong>FAEPO | Control de solicitudes académicas</strong><span>Demanda de cupos · Comunicaciones oficiales · Seguimiento de programas</span></div>''',unsafe_allow_html=True)
if remote_enabled:
    st.info("🔗 Datos de prueba obtenidos de PostgreSQL (Supabase). Lectura compartida; edición deshabilitada. No introducir datos institucionales reales.")
    if remote_error:
        st.error("No fue posible consultar Supabase. Revise los secretos, los permisos SELECT y la conexión. Detalle técnico: " + remote_error)
else:
    st.warning("🧪 Modo local sin conexión a Supabase: se muestran datos ficticios temporales. No introducir información institucional real.")
    if remote_error:
        st.error("Error de configuración: " + remote_error)


df=df_all()
unique_gs=df.gs.nunique()

if df.empty:
    st.warning("La base de datos no devolvió registros visibles. Verifique las políticas RLS y los permisos SELECT.")
    st.stop()

if current=="Inicio":
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Comunicaciones registradas",unique_gs)
    m2.metric("Programas diferentes",df.programa.nunique())
    m3.metric("Cupos solicitados",int(df.cupos.sum()))
    m4.metric("Cupos pendientes",int((df.cupos-df.asignados).sum()))
    st.write("")
    left,right=st.columns([1.3,1])
    with left:
        st.markdown('<div class="section-h">Programas con mayor demanda</div>',unsafe_allow_html=True)
        s=df.groupby("programa",as_index=False)["cupos"].sum().sort_values("cupos",ascending=False).head(7).sort_values("cupos")
        st.plotly_chart(plot_bar(s,"cupos","programa",True),use_container_width=True)
    with right:
        st.markdown('<div class="section-h">Estado de las solicitudes</div>',unsafe_allow_html=True)
        s=df.groupby("estado",as_index=False).size().rename(columns={"size":"registros"})
        fig=px.pie(s,names="estado",values="registros",hole=.60,color_discrete_sequence=["#12688D","#45A6AF","#E0B75B","#59A979","#A6B7C8"])
        fig.update_layout(margin=dict(l=5,r=5,t=10,b=10),height=315,paper_bgcolor="white",legend=dict(orientation="h",y=-.16,font_size=10))
        st.plotly_chart(fig,use_container_width=True)
    st.markdown('<div class="section-h">Buscar solicitudes</div>',unsafe_allow_html=True)
    term=st.text_input("Buscar por comunicación, unidad o programa",placeholder="Escriba número GS, unidad o programa...")
    year=st.selectbox("Vigencia",["Todas"]+sorted(df.vigencia.unique().tolist()),index=0)
    table(filtered(df,term,year))

elif current=="Comunicaciones GS":
    st.subheader("Seguimiento por comunicación oficial")
    st.caption("Cada comunicación agrupa los programas solicitados por una unidad.")
    q=st.text_input("Filtrar comunicaciones",placeholder="Buscar número GS o unidad...")
    gs_list=df[["gs","unidad","fecha"]].drop_duplicates().sort_values("gs")
    if q:
        gs_list=gs_list[gs_list.gs.str.contains(re.escape(q),case=False,regex=True)|gs_list.unidad.str.contains(re.escape(q),case=False,regex=True)]
    if gs_list.empty:
        st.warning("No se encontraron comunicaciones.")
    else:
        l,r=st.columns([1,2.3],gap="large")
        with l:
            chosen=st.radio("COMUNICACIONES RECIBIDAS",gs_list.gs.tolist(),format_func=lambda g:f"▤  {g} · {df[df.gs==g].iloc[0].unidad}")
        subset=df[df.gs==chosen]
        with r:
            st.markdown(f"### {esc(chosen)}")
            st.caption(f"Unidad: {subset.iloc[0].unidad}   •   Fecha: {subset.iloc[0].fecha}   •   Vigencia: {subset.iloc[0].vigencia}")
            c1,c2,c3=st.columns(3)
            c1.metric("Programas",len(subset));c2.metric("Cupos solicitados",int(subset.cupos.sum()));c3.metric("Cupos asignados",int(subset.asignados.sum()))
            st.markdown("**Programas asociados**")
            table(subset,["programa","cupos","asignados","estado","nota"])
            st.download_button("Descargar detalle de esta comunicación",subset.to_csv(index=False).encode("utf-8-sig"),f"{chosen}.csv",mime="text/csv")

elif current=="Programas académicos":
    st.subheader("Consulta por programa académico")
    st.caption("Seleccione un programa para consultar qué comunicaciones solicitaron cupos y cuántos están pendientes.")
    p=st.selectbox("Programa académico",sorted(df.programa.unique()))
    subset=df[df.programa==p]
    a,b,c,d=st.columns(4)
    a.metric("Comunicaciones",subset.gs.nunique());b.metric("Unidades solicitantes",subset.unidad.nunique())
    c.metric("Cupos solicitados",int(subset.cupos.sum()));d.metric("Cupos pendientes",int((subset.cupos-subset.asignados).sum()))
    table(subset,["gs","unidad","fecha","vigencia","cupos","asignados","estado","nota"])
    st.markdown("#### Demanda por unidad")
    s=subset.groupby("unidad",as_index=False)["cupos"].sum().sort_values("cupos",ascending=False)
    st.plotly_chart(plot_bar(s,"unidad","cupos"),use_container_width=True)

elif current=="Registrar solicitud" and remote_enabled:
    st.subheader("Registrar nueva solicitud")
    st.warning("Registro temporalmente inhabilitado en la versión compartida. La escritura se habilitará tras implementar autenticación y autorización por usuario.")

elif current=="Registrar solicitud":
    st.subheader("Registrar nueva solicitud")
    st.caption("Un número GS puede tener varios programas. Registre primero los datos de la comunicación y luego cada programa solicitado.")
    with st.form("alta",clear_on_submit=False):
        a,b,c=st.columns([1.3,1,1])
        gs=a.text_input("Número de comunicación *",placeholder="GS-DEMO-0005")
        unidad=b.text_input("Unidad solicitante *",placeholder="UNIDAD ECO")
        fecha=c.date_input("Fecha de la comunicación",value=date.today())
        vigencia=st.number_input("Vigencia",min_value=2025,max_value=2040,value=2027)
        p=st.selectbox("Programa académico *",st.session_state.catalogo)
        a,b=st.columns(2)
        cupos=a.number_input("Cupos solicitados *",min_value=1,value=1)
        asignados=b.number_input("Cupos asignados",min_value=0,value=0)
        estado=st.selectbox("Estado",ESTADOS)
        nota=st.text_area("Observación opcional (sin nombres ni datos personales)")
        submit=st.form_submit_button("＋ Registrar programa asociado al GS",type="primary",use_container_width=True)
    if submit:
        gs=gs.strip().upper();unidad=unidad.strip().upper()
        existing=df[df.gs==gs]
        if not gs or not unidad or len(gs)<5:
            st.error("Indique una comunicación y una unidad válidas.")
        elif not existing.empty and (existing.iloc[0].unidad != unidad or existing.iloc[0].fecha != str(fecha)):
            st.error("Este GS ya está registrado con otra unidad o fecha. Revise la comunicación antes de guardar.")
        elif any(x["gs"]==gs and x["programa"]==p for x in st.session_state.registros):
            st.error("El programa ya fue registrado bajo ese número GS. Puede actualizarlo en 'Gestionar cupos'.")
        elif asignados>cupos:
            st.error("Los cupos asignados no pueden superar los solicitados.")
        else:
            st.session_state.registros.append(dict(gs=gs,fecha=str(fecha),unidad=unidad,vigencia=int(vigencia),programa=p,cupos=int(cupos),asignados=int(asignados),estado=estado,nota=nota.strip()))
            st.success("Solicitud registrada en esta sesión de demostración.")
    with st.expander("Agregar un nuevo programa al catálogo"):
        new=st.text_input("Denominación del programa nuevo")
        if st.button("Agregar programa"):
            if not new.strip():st.warning("Digite una denominación.")
            elif new.strip().casefold() in {x.casefold() for x in st.session_state.catalogo}:st.warning("El programa ya existe.")
            else:
                st.session_state.catalogo.append(new.strip());st.session_state.catalogo.sort();st.success("Programa agregado temporalmente.")

elif current=="Gestionar cupos" and remote_enabled:
    st.subheader("Gestionar cupos")
    st.warning("Edición temporalmente inhabilitada en la versión compartida. Aquí implementaremos actualizaciones con trazabilidad una vez exista autenticación.")

elif current=="Gestionar cupos":
    st.subheader("Actualizar seguimiento de una solicitud")
    st.caption("Seleccione una comunicación y uno de sus programas. Puede cambiar cupos, estado y observaciones.")
    gs=st.selectbox("Comunicación GS",sorted(df.gs.unique()),key="edit_gs")
    subset=df[df.gs==gs]
    p=st.selectbox("Programa dentro de esta comunicación",subset.programa.tolist(),key="edit_programa")
    idx=next(i for i,x in enumerate(st.session_state.registros) if x["gs"]==gs and x["programa"]==p)
    record=st.session_state.registros[idx]
    with st.form(f"edit_{idx}"):
        a,b=st.columns(2)
        cupos=a.number_input("Cupos solicitados",min_value=0,value=int(record["cupos"]))
        asignados=b.number_input("Cupos asignados",min_value=0,value=int(record["asignados"]))
        estado=st.selectbox("Estado de la solicitud",ESTADOS,index=ESTADOS.index(record["estado"]))
        note=st.text_area("Observaciones",value=record["nota"])
        saved=st.form_submit_button("Guardar cambios",type="primary")
    if saved:
        if asignados>cupos: st.error("Cupos asignados no puede superar cupos solicitados.")
        else:
            st.session_state.registros[idx].update(cupos=int(cupos),asignados=int(asignados),estado=estado,nota=note)
            st.success("Cambios aplicados a esta sesión de demostración.")
            st.rerun()

elif current=="Reportes y catálogo":
    st.subheader("Reportes y catálogo")
    a,b,c=st.columns(3)
    a.metric("Comunicaciones",df.gs.nunique())
    b.metric("Solicitudes de programas",len(df))
    c.metric("Cupos solicitados",int(df.cupos.sum()))
    st.markdown("#### Reporte por programa")
    program_summary=df.groupby("programa",as_index=False).agg(comunicaciones=("gs","nunique"),cupos_solicitados=("cupos","sum"),cupos_asignados=("asignados","sum"))
    program_summary["pendientes"]=program_summary.cupos_solicitados-program_summary.cupos_asignados
    st.dataframe(program_summary,hide_index=True,use_container_width=True)
    st.markdown("#### Reporte por comunicación")
    gs_summary=df.groupby(["gs","unidad"],as_index=False).agg(programas=("programa","count"),cupos_solicitados=("cupos","sum"),cupos_asignados=("asignados","sum"))
    st.dataframe(gs_summary,hide_index=True,use_container_width=True)
    st.download_button("⬇ Exportar libro Excel (3 hojas)",export_excel(df),"FAEPO_DEMO_Reporte.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary")
    st.download_button("⬇ Exportar registros CSV",df.to_csv(index=False).encode("utf-8-sig"),"FAEPO_DEMO_Registros.csv",mime="text/csv")
    with st.expander("Catálogo de programas"):
        st.dataframe(pd.DataFrame({"Denominación":st.session_state.catalogo}),hide_index=True,use_container_width=True)
    if not remote_enabled:
      with st.expander("Reiniciar todos los datos ficticios"):
          st.warning("Solo afecta a la demostración de esta pestaña.")
          if st.button("Restaurar datos de ejemplo"):
              st.session_state.registros=[dict(x) for x in DEMO]
              st.session_state.catalogo=sorted({x["programa"] for x in DEMO})
              st.rerun()

st.caption("FAEPO · Piloto 3.0 | Conexión de demostración Supabase, sin acceso a GEPol o SIGAC. No habilitado para datos institucionales reales.")
