# app.py
import streamlit as st
import os
from funciones_lng import cargar_datos_escenario, graficar_inventario_agentes, preparar_descarga_escenario, cargar_configuracion

st.title("Sistema de Gestión de Inventario GNL")

# Selección de escenario (lo que ya tenías)
DATA_PATH = "DATA"
escenarios = [f for f in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, f))]
escenario_selec = st.sidebar.selectbox("Selecciona un Escenario", escenarios)

if escenario_selec:
    ruta_completa = os.path.join(DATA_PATH, escenario_selec)
    
    # Carga de datos
    df_c, df_e, df_t = cargar_datos_escenario(ruta_completa)

    config = cargar_configuracion(ruta_completa)

    # Generación de gráfica
    if df_c is not None:
        fig = graficar_inventario_agentes(df_c, df_e, df_t, config=config)
        st.pyplot(fig)

    else:
        st.error("No se pudieron cargar los datos de consumo.")

if escenario_selec:
    ruta_completa = os.path.join(DATA_PATH, escenario_selec)
    
    # --- BOTÓN DE DESCARGA ---
    zip_data = preparar_descarga_escenario(ruta_completa)
    
    st.sidebar.download_button(
        label="📥 Descargar Escenario (ZIP)",
        data=zip_data,
        file_name=f"{escenario_selec}.zip",
        mime="application/zip"
    )
    
    # ... (lógica de carga de datos y gráficas que ya tenías)