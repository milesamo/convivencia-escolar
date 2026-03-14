import streamlit as st
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import base64
from datetime import date

# ----------------------------------
# CONFIGURACION SUPABASE
# ----------------------------------

SUPABASE_URL = "https://sbxbxksbztvzebybtzxj.supabase.co"
SUPABASE_KEY = "sb_publishable_AaFkMAv5YaK2AfcZkL5cDg_JgqvWABw"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("No se pudo conectar con Supabase")
    st.stop()

st.title("Sistema de Convivencia Escolar")

# ----------------------------------
# CARGAR ESTUDIANTES
# ----------------------------------

try:
    response = supabase.table("estudiantes").select("*").execute()
    estudiantes = response.data
except:
    st.error("Error leyendo tabla estudiantes")
    st.stop()

if not estudiantes:
    st.warning("No hay estudiantes registrados")
    st.stop()

lista_estudiantes = {
    f"{e['estudiante']} ({e['grado']})": e["id"]
    for e in estudiantes
}

estudiante_nombre = st.selectbox(
    "Seleccionar estudiante",
    list(lista_estudiantes.keys())
)

estudiante_id = lista_estudiantes[estudiante_nombre]

# ----------------------------------
# CARGAR FALTAS
# ----------------------------------

response_faltas = supabase.table("faltas").select("*").execute()
faltas = response_faltas.data

if not faltas:
    st.warning("No hay faltas registradas")
    st.stop()

lista_faltas = {
    f"{f['tipo']} - {f['descripcion']}": f["id"]
    for f in faltas
}

falta_nombre = st.selectbox(
    "Tipo de falta",
    list(lista_faltas.keys())
)

falta_id = lista_faltas[falta_nombre]

# ----------------------------------
# OBSERVACION
# ----------------------------------

observacion = st.text_area("Observación")

# ----------------------------------
# FIRMA ESTUDIANTE
# ----------------------------------

st.subheader("Firma del estudiante")

canvas_result = st_canvas(
    stroke_width=2,
    stroke_color="black",
    background_color="white",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="firma"
)

firma_base64 = None

if canvas_result.image_data is not None:

    img = Image.fromarray(canvas_result.image_data.astype("uint8"))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    firma_base64 = base64.b64encode(buffer.getvalue()).decode()

# ----------------------------------
# GUARDAR REPORTE
# ----------------------------------

if st.button("Guardar reporte"):

    try:

        supabase.table("reportes").insert({

            "estudiante_id": estudiante_id,
            "falta_id": falta_id,
            "fecha": str(date.today()),
            "observacion": observacion,
            "firma_estudiante": firma_base64

        }).execute()

        st.success("Reporte guardado correctamente")

    except:
        st.error("Error guardando el reporte")

# ----------------------------------
# GENERAR PDF
# ----------------------------------

def generar_pdf():

    historial = supabase.table("reportes") \
        .select("*") \
        .eq("estudiante_id", estudiante_id) \
        .execute().data

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(120, height - 60,
                   "INSTITUCION EDUCATIVA CIUDAD LA HORMIGA")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(180, height - 90,
                   "REPORTE DE CONVIVENCIA ESCOLAR")

    pdf.setFont("Helvetica", 11)

    pdf.drawString(50, height - 130,
                   f"Estudiante: {estudiante_nombre}")

    pdf.drawString(50, height - 150,
                   f"Fecha: {date.today()}")

    data = [["Fecha", "Tipo", "Descripción", "Observación"]]

    for r in historial:

        falta = supabase.table("faltas") \
            .select("*") \
            .eq("id", r["falta_id"]) \
            .execute().data[0]

        data.append([
            r["fecha"],
            falta["tipo"],
            falta["descripcion"],
            r["observacion"]
        ])

    table = Table(data, colWidths=[70, 70, 200, 180])

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9)
    ])

    table.setStyle(style)

    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 50, height - 380)

    if len(historial) > 0 and historial[0].get("firma_estudiante"):

        firma_bytes = base64.b64decode(historial[0]["firma_estudiante"])

        with open("firma_temp.png", "wb") as f:
            f.write(firma_bytes)

        pdf.drawImage("firma_temp.png", 120, 200, width=200, height=60)
        pdf.drawString(170, 180, "Firma del estudiante")

    pdf.line(360, 200, 520, 200)
    pdf.drawString(400, 180, "Firma del docente")

    pdf.save()

    buffer.seek(0)

    return buffer


# ----------------------------------
# BOTON PDF
# ----------------------------------

if st.button("Generar PDF"):

    pdf = generar_pdf()

    st.download_button(
        "Descargar reporte PDF",
        pdf,
        "reporte_convivencia.pdf",
        "application/pdf"
    )