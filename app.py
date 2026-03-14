import streamlit as st
from supabase import create_client

# -----------------------------
# CONFIGURACION SUPABASE
# -----------------------------

SUPABASE_URL = "https://sbxbxksbztvzebybtzxj.supabase.co"
SUPABASE_KEY = "sb_publishable_AaFkMAv5YaK2AfcZkL5cDg_JgqvWABw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# TITULO
# -----------------------------

st.title("Sistema de Convivencia Escolar")

st.write("Conexión a Supabase establecida correctamente.")

# -----------------------------
# PRUEBA DE CONEXION
# -----------------------------

try:
    response = supabase.table("estudiantes").select("*").execute()
    st.success("Conexión exitosa con Supabase")
    st.write(response.data)

except Exception as e:
    st.error("Error conectando con Supabase")
    st.write(e)