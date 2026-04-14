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

def graficar_inventario_agentes(df, config=None):
    # 1. Preparación de datos
    df_plot = df.copy()
    
    # Convertir Datetext (20260101) a formato datetime real
    df_plot['Date'] = pd.to_datetime(df_plot['Datetext'].astype(str), format='%Y%m%d')
    
    # Crear un pivote para tener una columna por cada Agente
    df_pivot = df_plot.pivot(index='Date', columns='Agente', values='Opening')
    
    # Calcular la línea de TOTAL (Suma de todos los agentes por día)
    df_pivot['TOTAL_SYSTEM'] = df_pivot.sum(axis=1)

    # 2. Configuración de la Gráfica (Estilo Ingeniería)
    fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
    
    # Graficar cada Agente con líneas delgadas
    for agente in df_pivot.columns:
        if agente != 'TOTAL_SYSTEM':
            ax.plot(df_pivot.index, df_pivot[agente], label=agente, alpha=0.6, linewidth=1.5)
    
    # Graficar el TOTAL con una línea gruesa y destacada
    ax.plot(df_pivot.index, df_pivot['TOTAL_SYSTEM'], label='TOTAL SYSTEM', 
            color='red', linewidth=3, linestyle='-')

    # --- LÓGICA DE SOMBREADO (ÁREA HISTÓRICA) ---
    if config and 'punto_corte_real' in config:
        try:
            fecha_corte = pd.to_datetime(config['punto_corte_real'])
            inicio_grafica = df_pivot.index.min()
            
            # Sombreado gris tenue para el pasado (Histórico)
            # zorder=0 lo mantiene al fondo de las líneas
            ax.axvspan(inicio_grafica, fecha_corte, color='gray', alpha=0.15, zorder=0, label='Histórico')
            
            # Línea vertical divisoria sutil
            ax.axvline(fecha_corte, color='black', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
            
            # Etiqueta indicativa
            ax.text(fecha_corte, ax.get_ylim()[1], '  Inicio Proyección ➔', 
                    verticalalignment='top', fontsize=10, color='#444444', alpha=0.8)
        except Exception as e:
            print(f"Error procesando sombreado: {e}")

    # 3. Estética de los Ejes
    ax.set_title('Niveles de Apertura de Inventario: Histórico vs Proyectado', fontsize=14, fontweight='bold')
    ax.set_ylabel('Opening Level (Units)', fontsize=12)
    ax.set_xlabel('Fecha', fontsize=12)
    
    # Cuadrícula (Grid) limpia
    ax.grid(True, which='both', linestyle='--', alpha=0.3, zorder=0)
    
    # Formatear el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    # Leyenda fuera del gráfico
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Leyenda")
    
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