import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import zipfile
import io


def cargar_datos_escenario(ruta_escenario):
    """
    Busca y carga los archivos csv específicos de un escenario.
    """
    # Definimos los nombres exactos que estamos buscando
    file_consumo = "consumo_inventario.csv"
    file_embarque = "resumen_embarque.csv"
    
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

def graficar_inventario_agentes(df, config=None):
    # 1. Preparación de datos
    df_plot = df.copy()
    
    # Aseguramos que la fecha del CSV sea datetime (formato 20260414)
    df_plot['Date'] = pd.to_datetime(df_plot['Datetext'].astype(str), format='%Y%m%d')
    
    df_pivot = df_plot.pivot(index='Date', columns='Agente', values='Opening')
    df_pivot['TOTAL_SYSTEM'] = df_pivot.sum(axis=1)

    # 2. Configuración de la Gráfica
    fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
    
    # Graficar cada Agente
    for agente in df_pivot.columns:
        if agente != 'TOTAL_SYSTEM':
            ax.plot(df_pivot.index, df_pivot[agente], label=agente, alpha=0.6, linewidth=1.5)
    
    # Graficar el TOTAL destacado
    ax.plot(df_pivot.index, df_pivot['TOTAL_SYSTEM'], label='TOTAL SYSTEM', 
            color='red', linewidth=3, linestyle='-')

    # --- LÓGICA DE SOMBREADO REFORZADA ---
    if config and 'punto_corte_real' in config:
        try:
            # Convertimos la fecha del JSON (2026-04-14) a datetime
            # pd.to_datetime es inteligente y detecta los guiones automáticamente
            fecha_corte = pd.to_datetime(config['punto_corte_real'])
            
            # Definimos el inicio y fin del sombreado basados en los datos
            limite_izquierdo = df_pivot.index.min()
            
            # Validamos que la fecha de corte esté dentro del rango de la gráfica
            if limite_izquierdo <= fecha_corte <= df_pivot.index.max():
                # Dibujamos el área sombreada
                ax.axvspan(limite_izquierdo, fecha_corte, 
                           color='gray', alpha=0.2, zorder=0, label='Histórico')
                
                # Línea divisoria
                ax.axvline(fecha_corte, color='black', linestyle='--', linewidth=1.2, alpha=0.8, zorder=2)
                
                # Etiqueta
                ax.text(fecha_corte, ax.get_ylim()[1] * 0.95, '  PROYECCIÓN ➔', 
                        fontsize=10, fontweight='bold', alpha=0.6)
        except Exception as e:
            print(f"Error al procesar el sombreado: {e}")

    # 3. Estética
    ax.set_title('Niveles de Inventario: Histórico vs Proyectado', fontsize=14, fontweight='bold')
    ax.set_ylabel('Opening Level (Units)', fontsize=12)
    ax.set_xlabel('Fecha', fontsize=12)
    
    ax.grid(True, which='both', linestyle='--', alpha=0.3, zorder=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Agentes")
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