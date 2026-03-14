import streamlit as st
from supabase import create_client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
import base64
from datetime import date

# -----------------------------
# CONFIGURACION SUPABASE
# -----------------------------

url = "sb_publishable_AaFkMAv5YaK2AfcZkL5cDg_JgqvWABw"
key = "https://sbxbxksbztvzebybtzxj.supabase.co"

supabase = create_client(url, key)

st.title("Sistema de Convivencia Escolar")

# -----------------------------
# CARGAR ESTUDIANTES
# -----------------------------

estudiantes = supabase.table("estudiantes").select("*").execute().data

lista_estudiantes = {
    f"{e['estudiante']} ({e['grado']})": e["id"]
    for e in estudiantes
}

estudiante_nombre = st.selectbox(
    "Seleccionar estudiante",
    list(lista_estudiantes.keys())
)

estudiante_id = lista_estudiantes[estudiante_nombre]

# -----------------------------
# CARGAR FALTAS
# -----------------------------

faltas = supabase.table("faltas").select("*").execute().data

lista_faltas = {
    f"{f['tipo']} - {f['descripcion']}": f["id"]
    for f in faltas
}

falta_nombre = st.selectbox(
    "Tipo de falta",
    list(lista_faltas.keys())
)

falta_id = lista_faltas[falta_nombre]

# -----------------------------
# OBSERVACION
# -----------------------------

observacion = st.text_area("Observación")

# -----------------------------
# FIRMA DEL ESTUDIANTE
# -----------------------------

st.subheader("Firma del estudiante")

canvas_result = st_canvas(
    stroke_width=2,
    stroke_color="black",
    background_color="white",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="firma",
)

firma_base64 = None

if canvas_result.image_data is not None:

    img = Image.fromarray(canvas_result.image_data.astype("uint8"))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    firma_base64 = base64.b64encode(buffer.getvalue()).decode()

# -----------------------------
# GUARDAR REPORTE
# -----------------------------

if st.button("Guardar reporte"):

    supabase.table("reportes").insert({

        "estudiante_id": estudiante_id,
        "falta_id": falta_id,
        "fecha": str(date.today()),
        "observacion": observacion,
        "firma_estudiante": firma_base64

    }).execute()

    st.success("Reporte guardado correctamente")

# -----------------------------
# GENERAR PDF
# -----------------------------

def generar_pdf():

    historial = supabase.table("reportes")\
        .select("*")\
        .eq("estudiante_id", estudiante_id)\
        .execute().data

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter

    # Escudo (si tienes archivo escudo.png)
    try:
        pdf.drawImage("escudo.png", 40, height - 100, width=60, height=60)
    except:
        pass

    # TITULO

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(120, height - 60,
                   "INSTITUCION EDUCATIVA CIUDAD LA HORMIGA")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(200, height - 90,
                   "REPORTE DE SITUACIONES DE CONVIVENCIA")

    # DATOS ESTUDIANTE

    pdf.setFont("Helvetica", 11)

    pdf.drawString(50, height - 130,
                   f"Estudiante: {estudiante_nombre}")

    pdf.drawString(50, height - 150,
                   f"Fecha del reporte: {date.today()}")

    # -----------------------------
    # TABLA HISTORIAL
    # -----------------------------

    data = [["Fecha", "Tipo", "Descripción", "Observación"]]

    for r in historial:

        falta = supabase.table("faltas")\
            .select("*")\
            .eq("id", r["falta_id"])\
            .execute().data[0]

        data.append([
            r["fecha"],
            falta["tipo"],
            falta["descripcion"],
            r["observacion"]
        ])

    table = Table(data, colWidths=[70, 60, 180, 180])

    style = TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),

        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("FONTSIZE", (0, 0), (-1, -1), 9)

    ])

    table.setStyle(style)

    table.wrapOn(pdf, width, height)

    table.drawOn(pdf, 50, height - 350)

    # -----------------------------
    # FIRMA ESTUDIANTE
    # -----------------------------

    if historial and historial[0]["firma_estudiante"]:

        firma_bytes = base64.b64decode(
            historial[0]["firma_estudiante"]
        )

        with open("firma_temp.png", "wb") as f:
            f.write(firma_bytes)

        pdf.drawImage("firma_temp.png",
                      150, 200,
                      width=200,
                      height=60)

        pdf.drawString(200, 180, "Firma del estudiante")

    # -----------------------------
    # FIRMA DOCENTE
    # -----------------------------

    pdf.line(350, 200, 500, 200)

    pdf.drawString(390, 180, "Firma del docente")

    pdf.save()

    buffer.seek(0)

    return buffer


# -----------------------------
# BOTON PDF
# -----------------------------

if st.button("Generar PDF"):

    pdf = generar_pdf()

    st.download_button(

        "Descargar reporte PDF",

        pdf,

        "reporte_convivencia.pdf",

        "application/pdf"

    )