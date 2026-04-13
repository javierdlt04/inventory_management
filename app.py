import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Reportería LNG", layout="wide")

st.title("Control de Suministro de Combustible")

# Sidebar para filtros
pais = st.sidebar.selectbox("Selecciona el Activo", ["Panamá", "Chile", "Rep. Dominicana"])

# Simulación de carga de datos
st.subheader(f"Análisis de inventarios - {pais}")
# Aquí llamarías a tus funciones de transformación
st.info("Cargando datos transformados de la base de datos...")

# Gráfica de ejemplo
# fig = px.line(df, x='fecha', y='nivel_tanque')
# st.plotly_chart(fig)