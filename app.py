import streamlit as st
from supabase import create_client
from datetime import datetime

# -------------------------
# CONFIGURACION STREAMLIT
# -------------------------

st.set_page_config(
    page_title="Sistema de Convivencia Escolar",
    page_icon="📘",
    layout="wide"
)

# -------------------------
# CONEXION SUPABASE (SECRETS)
# -------------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# TITULO
# -------------------------

st.title("INSTITUCIÓN EDUCATIVA CIUDAD LA HORMIGA")
st.divider()

# -------------------------
# FUNCIONES
# -------------------------

def cargar_estudiantes():
    try:
        response = supabase.table("estudiantes").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error cargando estudiantes: {e}")
        return []


def cargar_reportes():
    try:
        response = supabase.table("reportes").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error cargando reportes: {e}")
        return []


def guardar_reporte(estudiante, grado, descripcion):

    datos = {
        "estudiante": estudiante,
        "grado": grado,
        "descripcion": descripcion,
        "fecha": datetime.now().strftime("%Y-%m-%d")
    }

    try:
        supabase.table("reportes").insert(datos).execute()
        st.success("Reporte guardado correctamente")
    except Exception as e:
        st.error(f"Error guardando reporte: {e}")


# -------------------------
# CARGAR DATOS
# -------------------------

estudiantes = cargar_estudiantes()

# -------------------------
# FORMULARIO REPORTE
# -------------------------

st.header("Registrar reporte")

if len(estudiantes) == 0:

    st.warning("No hay estudiantes en la base de datos")

else:

    lista_estudiantes = [e["nombre"] for e in estudiantes]
    lista_grados = sorted(list(set([e["grado"] for e in estudiantes])))

    col1, col2 = st.columns(2)

    with col1:
        grado = st.selectbox("Grado", lista_grados)

    with col2:
        estudiante = st.selectbox("Estudiante", lista_estudiantes)

    descripcion = st.text_area(
        "Descripción del reporte",
        height=150
    )

    if st.button("Guardar reporte"):

        if descripcion.strip() == "":
            st.warning("Debe escribir una descripción")
        else:
            guardar_reporte(estudiante, grado, descripcion)

# -------------------------
# HISTORIAL
# -------------------------

st.divider()
st.header("Historial de reportes")

reportes = cargar_reportes()

if len(reportes) == 0:

    st.info("No hay reportes registrados")

else:

    for r in reportes:

        with st.expander(f"{r['fecha']} - {r['estudiante']}"):

            st.write("**Grado:**", r["grado"])
            st.write("**Descripción:**")
            st.write(r["descripcion"])