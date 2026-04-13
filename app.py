# app.py
import streamlit as st
import os
from funciones_lng import cargar_datos_escenario, graficar_inventario_agentes

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
        st.subheader("Análisis de Inventario")
        
        # Llamamos a tu función de gráfica
        figura = graficar_inventario_agentes(df_consumo)
        
        # MOSTRAR EN STREAMLIT
        st.pyplot(figura)
    else:
        st.error("No se pudieron cargar los datos de consumo.")