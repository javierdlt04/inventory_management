import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import zipfile
import io
import json


def cargar_datos_escenario(ruta_escenario):
    """
    Busca y carga los archivos csv específicos de un escenario.
    """
    # Definimos los nombres exactos que estamos buscando
    file_consumo = "consumo_inventario.csv"
    file_embarque = "resumen_embarques.csv"
    
    # Construimos las rutas completas
    path_consumo = os.path.join(ruta_escenario, file_consumo)
    path_embarque = os.path.join(ruta_escenario, file_embarque)
    
    # Inicializamos las variables como None por si no se encuentran los archivos
    df_consumo = None
    df_embarque = None

    # Validación y carga de Consumo
    if os.path.exists(path_consumo):
        df_consumo = pd.read_csv(path_consumo)
        print(f"✅ {file_consumo} cargado correctamente.")
    else:
        print(f"❌ Error: No se encontró {file_consumo} en la ruta {ruta_escenario}.")

    # Validación y carga de Embarques
    if os.path.exists(path_embarque):
        df_embarque = pd.read_csv(path_embarque)
        print(f"✅ {file_embarque} cargado correctamente.")
    else:
        print(f"❌ Error: No se encontró {file_embarque} en la ruta {ruta_escenario}.")
        
    return df_consumo, df_embarque

def cargar_configuracion(ruta_escenario):
    """
    Lee el archivo run_settings.json de la carpeta del escenario.
    """
    path_config = os.path.join(ruta_escenario, "run_settings.json")
    
    if os.path.exists(path_config):
        with open(path_config, 'r') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"❌ Error al leer el JSON: {e}")
                return None
    return None

def graficar_inventario_agentes(df_inventario, df_embarques=None, config=None):
    # 1. Preparación de datos de inventario
    df_plot = df_inventario.copy()
    df_plot['Date'] = pd.to_datetime(df_plot['Datetext'].astype(str), format='%Y%m%d')
    
    df_pivot = df_plot.pivot(index='Date', columns='Agente', values='Opening')
    df_pivot['TOTAL_SYSTEM'] = df_pivot.sum(axis=1)

    # Definimos la fecha de corte al inicio para que esté disponible en toda la función
    fecha_corte = None
    if config and 'punto_corte_real' in config:
        fecha_corte = pd.to_datetime(config['punto_corte_real'])

    # 2. Configuración de la Gráfica
    fig, ax = plt.subplots(figsize=(16, 8), dpi=100)
    
    # Graficar líneas de agentes
    for agente in df_pivot.columns:
        if agente != 'TOTAL_SYSTEM':
            ax.plot(df_pivot.index, df_pivot[agente], label=agente, alpha=0.5, linewidth=1)
    
    # Graficar el TOTAL
    ax.plot(df_pivot.index, df_pivot['TOTAL_SYSTEM'], label='TOTAL SYSTEM', 
            color='red', linewidth=2.5, zorder=3)

    # --- LÓGICA: ETIQUETAS DE BARCOS ---
    if df_embarques is not None:
        df_embarques['Arrival_Date'] = pd.to_datetime(df_embarques['Arrival Window'])
        y_min, y_max = ax.get_ylim()
        
        for i, row in df_embarques.iterrows():
            fecha_barco = row['Arrival_Date']
            nombre_barco = row['Terminal Code']
            
            # Verificamos que la fecha esté en el rango visible
            if df_pivot.index.min() <= fecha_barco <= df_pivot.index.max():
                ax.axvline(fecha_barco, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)
                
                # Ponemos el texto en el eje X (y_min)
                ax.text(fecha_barco, y_min, f" {nombre_barco}", 
                        rotation=90, 
                        verticalalignment='bottom', 
                        fontsize=8, 
                        color='blue',
                        fontweight='bold',
                        alpha=0.7)

    # --- LÓGICA DE SOMBREADO (HISTÓRICO) ---
    if fecha_corte is not None:
        ax.axvspan(df_pivot.index.min(), fecha_corte, color='gray', alpha=0.12, zorder=0)
        ax.axvline(fecha_corte, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax.text(fecha_corte, ax.get_ylim()[1], '  Inicio Proyección ➔', 
                verticalalignment='top', fontsize=10, color='#444444', alpha=0.8)

    # 3. Estética final
    ax.set_title('Manejo de Inventario - Proyección de Suministro', fontsize=14, fontweight='bold')
    ax.set_ylabel('Nivel de Inventario (Units)', fontsize=12)
    ax.grid(True, which='both', linestyle='--', alpha=0.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.tight_layout()
    
    return fig

def preparar_descarga_escenario(ruta_escenario):
    """
    Comprime todos los archivos de la carpeta del escenario en un archivo ZIP en memoria.
    """
    # Creamos un buffer en memoria para el archivo ZIP
    buf = io.BytesIO()
    
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(ruta_escenario):
            for file in files:
                ruta_completa = os.path.join(root, file)
                # El nombre dentro del zip será solo el nombre del archivo
                z.write(ruta_completa, arcname=file)
    
    return buf.getvalue()