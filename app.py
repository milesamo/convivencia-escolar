import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
from supabase import create_client

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors

from PIL import Image as PILImage

# ----------------------------
# SUPABASE
# ----------------------------

url = "https://sbxbxksbztvzebybtzxj.supabase.co"
key = "sb_publishable_AaFkMAv5YaK2AfcZkL5cDg_JgqvWABw"

supabase = create_client(url, key)

# ----------------------------
# CONFIG APP
# ----------------------------

st.set_page_config(
    page_title="Convivencia Escolar",
    layout="centered"
)

# ----------------------------
# ESTILO
# ----------------------------

st.markdown("""
<style>

.block-container{
padding-top:3rem;
padding-bottom:2rem;
}

button{
height:55px;
font-size:18px;
border-radius:8px;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# CARPETAS
# ----------------------------

os.makedirs("firmas", exist_ok=True)
os.makedirs("pdf", exist_ok=True)

# ----------------------------
# CARGAR DATOS
# ----------------------------

@st.cache_data
def cargar_estudiantes():

    df = pd.read_excel("estudiantes.xlsx")
    df.columns = df.columns.str.lower().str.strip()

    return df


@st.cache_data
def cargar_faltas():

    df = pd.read_excel("faltas.xlsx")
    df.columns = df.columns.str.lower().str.strip()

    return df


def cargar_reportes():

    try:

        res = supabase.table("reportes").select("*").execute()

        return pd.DataFrame(res.data)

    except:

        return pd.DataFrame(columns=[
            "fecha","grado","estudiante",
            "docente","area","tipo",
            "descripcion","observaciones","firma"
        ])


df_estudiantes = cargar_estudiantes()
df_faltas = cargar_faltas()
df_reportes = cargar_reportes()

# ----------------------------
# ENCABEZADO
# ----------------------------

col1,col2 = st.columns([1,5])

with col1:
    st.image("escudo_iech.png", width=45)

with col2:
    st.markdown("""
    <div style="font-size:20px;font-weight:700">
    INSTITUCION EDUCATIVA CIUDAD LA HORMIGA
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ----------------------------
# SELECCION ESTUDIANTE
# ----------------------------

st.subheader("Seleccionar estudiante")

grados = sorted(df_estudiantes["grado"].unique())

grado = st.selectbox("Grado", grados)

estudiantes = df_estudiantes[df_estudiantes["grado"] == grado]

estudiante = st.selectbox("Estudiante", estudiantes["estudiante"])

# ----------------------------
# HISTORIAL
# ----------------------------

historial = df_reportes[df_reportes["estudiante"] == estudiante]

if len(historial) > 0:

    st.warning(f"⚠ Este estudiante tiene {len(historial)} faltas registradas")

# ----------------------------
# REGISTRAR FALTA
# ----------------------------

st.subheader("Registrar falta")

col1,col2 = st.columns(2)

with col1:
    docente = st.text_input("Docente")

with col2:
    area = st.text_input("Área")

tipo = st.selectbox(
    "Tipo de falta",
    df_faltas["tipo"].unique()
)

faltas_tipo = df_faltas[df_faltas["tipo"] == tipo]

descripcion = st.selectbox(
    "Descripción",
    faltas_tipo["descripcion"]
)

observaciones = st.text_area("Observaciones")

# ----------------------------
# FIRMA
# ----------------------------

st.subheader("Firma del estudiante")

canvas = st_canvas(
    stroke_width=2,
    stroke_color="black",
    background_color="white",
    height=170,
    width=420,
    drawing_mode="freedraw",
    key="canvas"
)

# ----------------------------
# GUARDAR
# ----------------------------

if st.button("Registrar falta", type="primary"):

    firma_path = ""

    if canvas.image_data is not None:

        firma_path = f"firmas/{estudiante.replace(' ','_')}.png"

        img = PILImage.fromarray(canvas.image_data.astype("uint8"))

        img.save(firma_path)

    data = {

        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "grado": grado,
        "estudiante": estudiante,
        "docente": docente,
        "area": area,
        "tipo": tipo,
        "descripcion": descripcion,
        "observaciones": observaciones,
        "firma": firma_path

    }

    try:

        supabase.table("reportes").insert(data).execute()

        st.success("Falta registrada correctamente")

        st.cache_data.clear()
        st.rerun()

    except:

        st.error("Error guardando en Supabase")

# ----------------------------
# GENERAR PDF
# ----------------------------

def generar_pdf(estudiante, grado, historial):

    archivo = f"pdf/{estudiante.replace(' ','_')}.pdf"

    styles = getSampleStyleSheet()

    style_text = ParagraphStyle('texto',fontSize=9,leading=11)

    elementos = []

    encabezado = Table([
        [
            Image("escudo_iech.png",2.5*cm,2.5*cm),
            Paragraph(
                "<b>INSTITUCION EDUCATIVA CIUDAD LA HORMIGA</b>",
                styles["Heading2"]
            )
        ]
    ], colWidths=[3*cm,14*cm])

    elementos.append(encabezado)

    elementos.append(Spacer(1,20))

    info = [
        ["Estudiante:", estudiante],
        ["Grado:", grado],
        ["Total faltas:", str(len(historial))]
    ]

    tabla_info = Table(info, colWidths=[120,300])

    elementos.append(tabla_info)

    elementos.append(Spacer(1,20))

    data = [["Fecha","Docente","Área","Tipo","Descripción","Observaciones"]]

    for _, r in historial.iterrows():

        data.append([
            Paragraph(str(r["fecha"]),style_text),
            Paragraph(str(r["docente"]),style_text),
            Paragraph(str(r["area"]),style_text),
            Paragraph(str(r["tipo"]),style_text),
            Paragraph(str(r["descripcion"]),style_text),
            Paragraph(str(r["observaciones"]),style_text)
        ])

    tabla = Table(data,colWidths=[55,90,70,70,150,140])

    tabla.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.black),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white)

    ]))

    elementos.append(tabla)

    doc = SimpleDocTemplate(archivo,pagesize=letter)

    doc.build(elementos)

    return archivo

# ----------------------------
# BOTON PDF
# ----------------------------

if st.button("Generar PDF"):

    historial = cargar_reportes()
    historial = historial[historial["estudiante"] == estudiante]

    archivo = generar_pdf(estudiante, grado, historial)

    with open(archivo,"rb") as f:

        st.download_button(
            "Descargar PDF",
            f,
            file_name=os.path.basename(archivo)
        )