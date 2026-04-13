# app.py
import streamlit as st
import os
from funciones_lng import cargar_datos_escenario, graficar_inventario_agentes, preparar_descarga_escenario

st.title("Sistema de Gestión de Inventario GNL")

# Selección de escenario (lo que ya tenías)
DATA_PATH = "DATA"
escenarios = [f for f in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, f))]
escenario_selec = st.sidebar.selectbox("Selecciona un Escenario", escenarios)

if escenario_selec:
    ruta_completa = os.path.join(DATA_PATH, escenario_selec)
    
    # Llamamos a tu función
    df_consumo, df_embarque = cargar_datos_escenario(ruta_completa)
    
    if df_consumo is not None:
        st.subheader("Inventario Full Year")
        
        # Llamamos a tu función de gráfica
        figura = graficar_inventario_agentes(df_consumo)
        
        # MOSTRAR EN STREAMLIT
        st.pyplot(figura)
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