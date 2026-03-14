import streamlit as st
from supabase import create_client
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import os

st.set_page_config(page_title="Convivencia Escolar", layout="wide")

st.title("Sistema de Convivencia Escolar")

# -----------------------------
# CONEXION SUPABASE
# -----------------------------

supabase = None

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    st.success("Conexión a Supabase establecida correctamente")

except Exception:
    st.error("Error conectando con Supabase")

# -----------------------------
# FUNCION GENERAR PDF
# -----------------------------

def generar_pdf(nombre, grado, historial):

    archivo = f"reporte_{nombre}.pdf"

    styles = getSampleStyleSheet()

    elementos = []

    if os.path.exists("escudo.png"):
        escudo = Image("escudo.png", width=2*cm, height=2*cm)
    else:
        escudo = ""

    titulo = Paragraph(
        "<b>INSTITUCION EDUCATIVA CIUDAD LA HORMIGA</b>",
        styles["Title"]
    )

    encabezado = Table([[escudo, titulo]])

    encabezado.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE")
    ]))

    elementos.append(encabezado)

    elementos.append(Spacer(1,20))

    subtitulo = Paragraph(
        "<b>REPORTE DE SITUACIONES DE CONVIVENCIA</b>",
        styles["Heading2"]
    )

    elementos.append(subtitulo)

    elementos.append(Spacer(1,20))

    fecha = datetime.today().strftime("%d/%m/%Y")

    info = [
        ["Nombre del estudiante", nombre],
        ["Grado", grado],
        ["Fecha del reporte", fecha]
    ]

    tabla_info = Table(info, colWidths=[200,300])

    tabla_info.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))

    elementos.append(tabla_info)

    elementos.append(Spacer(1,20))

    datos = [["Fecha","Situación","Acción tomada"]]

    for h in historial:
        datos.append([h["fecha"], h["situacion"], h["accion"]])

    tabla = Table(datos, colWidths=[100,220,180])

    tabla.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey)
    ]))

    elementos.append(tabla)

    elementos.append(Spacer(1,60))

    firmas = Table([
        ["______________________","______________________"],
        ["Firma del estudiante","Firma del docente"]
    ])

    firmas.setStyle(TableStyle([
        ("ALIGN",(0,0),(-1,-1),"CENTER")
    ]))

    elementos.append(firmas)

    doc = SimpleDocTemplate(archivo, pagesize=letter)

    doc.build(elementos)

    return archivo

# -----------------------------
# CONSULTA ESTUDIANTES
# -----------------------------

if supabase:

    try:

        estudiantes = supabase.table("estudiantes").select("*").execute().data

        if estudiantes:

            nombres = [e["nombre"] for e in estudiantes]

            estudiante_seleccionado = st.selectbox(
                "Seleccionar estudiante",
                nombres
            )

            estudiante = next(
                e for e in estudiantes if e["nombre"] == estudiante_seleccionado
            )

            st.write("Grado:", estudiante["grado"])

            historial_db = supabase.table("convivencia")\
                .select("*")\
                .eq("estudiante_id", estudiante["id"])\
                .execute().data

            historial = []

            for h in historial_db:

                historial.append({
                    "fecha": h["fecha"],
                    "situacion": h["situacion"],
                    "accion": h["accion"]
                })

            st.subheader("Historial")

            st.dataframe(historial_db)

            if st.button("Generar reporte PDF"):

                pdf = generar_pdf(
                    estudiante["nombre"],
                    estudiante["grado"],
                    historial
                )

                with open(pdf, "rb") as file:

                    st.download_button(
                        "Descargar reporte",
                        file,
                        file_name=pdf
                    )

        else:

            st.warning("No hay estudiantes registrados")

    except Exception as e:

        st.error("Error consultando datos")