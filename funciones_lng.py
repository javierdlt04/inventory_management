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

    # Definimos la fecha de corte para el sombreado
    fecha_corte = None
    if config and 'punto_corte_real' in config:
        fecha_corte = pd.to_datetime(config['punto_corte_real'])

    # 2. Configuración de la Gráfica
    # Aumentamos el margen superior e inferior para acomodar las etiquetas
    fig, ax = plt.subplots(figsize=(16, 8), dpi=100)
    plt.subplots_adjust(bottom=0.25, top=0.85) # Ajuste manual de márgenes
    
    # Graficar líneas de agentes
    for agente in df_pivot.columns:
        if agente != 'TOTAL_SYSTEM':
            ax.plot(df_pivot.index, df_pivot[agente], label=agente, alpha=0.5, linewidth=1)
    
    # Graficar el TOTAL destacado
    ax.plot(df_pivot.index, df_pivot['TOTAL_SYSTEM'], label='TOTAL SYSTEM', 
            color='red', linewidth=2.5, zorder=3)

    # --- LÓGICA DE SOMBREADO (HISTÓRICO) ---
    if fecha_corte is not None:
        inicio_grafica = df_pivot.index.min()
        ax.axvspan(inicio_grafica, fecha_corte, color='gray', alpha=0.10, zorder=0)
        ax.axvline(fecha_corte, color='black', linestyle='--', linewidth=1, alpha=0.4, zorder=1)
        # Ajustamos el texto del punto de corte para que esté alineado abajo
        ax.text(fecha_corte, ax.get_ylim()[0], '  Inicio Proyección ➔', 
                verticalalignment='bottom', fontsize=10, color='#444444', alpha=0.7)

    # 3. Estética de los Ejes
    ax.set_title('Manejo de Inventario - Proyección de Suministro', fontsize=14, fontweight='bold')
    ax.set_ylabel('Nivel de Inventario (Units)', fontsize=12)
    
    ax.grid(True, which='both', linestyle='--', alpha=0.2, zorder=0)
    
    # --- AJUSTE EJE X PRINCIPAL (FECHAS ARRIBA) ---
    # Colocamos las fechas en la parte superior
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.set_xlabel('Fecha', fontsize=12)
    
    # Formatear el eje X principal
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    # Rotar fechas hacia arriba y centrarlas
    plt.xticks(rotation=45, ha='left')
    
    # --- NUEVA LÓGICA: ETIQUETAS BARCOS (ABAJO) ---
    if df_embarques is not None:
        df_embarques['Arrival_Date'] = pd.to_datetime(df_embarques['Arrival Window'])
        
        # Obtenemos los límites de la gráfica para el posicionamiento
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        
        # Calculamos un 'piso' visual para las etiquetas por debajo del 0
        y_label_pos = y_min - (y_max - y_min) * 0.05
        
        for i, row in df_embarques.iterrows():
            fecha_barco = row['Arrival_Date']
            nombre_barco = row['Terminal Code']
            
            # Verificamos que la fecha esté en el rango visible
            if x_min <= mdates.date2num(fecha_barco) <= x_max:
                # Línea vertical punteada sutil
                ax.axvline(fecha_barco, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)
                
                # Texto en vertical, azul y alineado arriba-centro
                # Lo posicionamos 'y_label_pos' para que cuelgue del eje X inferior
                ax.text(fecha_barco, y_min, f" {nombre_barco}", 
                        rotation=90, 
                        verticalalignment='top', # Importante: alinea la parte superior del texto
                        horizontalalignment='center',
                        fontsize=8, 
                        color='blue',
                        fontweight='bold',
                        alpha=0.7)
                
        # Limpiamos las marcas del eje X inferior, solo dejamos la línea y los textos
        ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)

    # Leyenda fuera del gráfico
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    
    # plt.tight_layout() # tight_layout puede resetear los márgenes manuales, mejor no usarlo aquí
    
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