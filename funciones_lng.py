import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import zipfile
import io
import json


def cargar_datos_escenario(ruta_escenario):
    """Carga los tres archivos CSV principales del escenario."""
    try:
        df_consumo = pd.read_csv(os.path.join(ruta_escenario, "consumo_inventario.csv"))
        df_embarque = pd.read_csv(os.path.join(ruta_escenario, "resumen_embarques.csv"))
        # Nuevo: Carga de configuración de terminal
        df_terminal = pd.read_csv(os.path.join(ruta_escenario, "terminal_configuration.csv"))
        
        return df_consumo, df_embarque, df_terminal
    except Exception as e:
        print(f"Error al cargar archivos CSV: {e}")
        return None, None, None

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

def graficar_inventario_agentes(df_inventario, df_embarques, df_config, config=None):
    """
    Genera la gráfica de inventario con:
    - Fechas arriba y rotadas.
    - Nombres de barcos abajo en vertical.
    - Sombreado de área histórica vs proyectada.
    - Líneas horizontales de Capacidad Máxima y Mínimo Operativo.
    """
    # 1. Preparación de datos de inventario
    df_plot = df_inventario.copy()
    df_plot['Date'] = pd.to_datetime(df_plot['Datetext'].astype(str), format='%Y%m%d')
    
    # Pivotar para tener agentes en columnas
    df_pivot = df_plot.pivot(index='Date', columns='Agente', values='Opening')
    df_pivot['TOTAL_SYSTEM'] = df_pivot.sum(axis=1)

    # Definir la fecha de corte para el sombreado desde el JSON
    fecha_corte = None
    if config and 'punto_corte_real' in config:
        fecha_corte = pd.to_datetime(config['punto_corte_real'])

    # 2. Configuración de la Figura
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    # Ajustamos márgenes: mucho espacio abajo para barcos y arriba para fechas
    plt.subplots_adjust(bottom=0.25, top=0.82) 
    
    # --- LÓGICA DE LÍNEAS DE LÍMITE (TERMINAL CONFIG) ---
    if df_config is not None:
        for var_name, color, label_prefix in [
            ('Capacidad_Max', 'red', 'Cap. Máxima'),
            ('Minimo_Operativo', 'darkorange', 'Mín. Operativo')
        ]:
            # Buscamos el valor en el CSV de configuración
            val_serie = df_config[df_config['Variable'] == var_name]['Value']
            if not val_serie.empty:
                v = val_serie.values[0]
                ax.axhline(v, color=color, linestyle='--', linewidth=2, alpha=0.6, 
                           label=f'{label_prefix} ({v:,.0f})', zorder=1)

    # 3. Graficar Datos
    # Líneas de cada Agente (más finas y transparentes)
    for agente in df_pivot.columns:
        if agente != 'TOTAL_SYSTEM':
            ax.plot(df_pivot.index, df_pivot[agente], label=agente, alpha=0.4, linewidth=1.2)
    
    # Línea del Sistema Total (gruesa y roja)
    ax.plot(df_pivot.index, df_pivot['TOTAL_SYSTEM'], label='TOTAL SYSTEM', 
            color='red', linewidth=3, zorder=3)

    # 4. Sombreado Histórico (Área izquierda)
    if fecha_corte is not None:
        inicio_grafica = df_pivot.index.min()
        # Sombreado gris muy suave
        ax.axvspan(inicio_grafica, fecha_corte, color='gray', alpha=0.10, zorder=0)
        # Línea divisoria negra punteada
        ax.axvline(fecha_corte, color='black', linestyle='--', linewidth=1.2, alpha=0.5, zorder=2)
        # Etiqueta de inicio de proyección en la base
        ax.text(fecha_corte, ax.get_ylim()[0], '  Inicio Proyección ➔', 
                verticalalignment='bottom', fontsize=10, color='#444444', alpha=0.8, fontweight='bold')

    # 5. Configuración de Ejes (Estilo Mejillones)
    ax.set_title('Manejo de Inventario - Proyección de Suministro', fontsize=15, fontweight='bold', pad=30)
    ax.set_ylabel('Nivel de Inventario (Units)', fontsize=12)
    ax.grid(True, which='both', linestyle='--', alpha=0.2, zorder=0)
    
    # Mover Eje X a la parte superior
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45, ha='left', fontsize=9)
    
    # 6. Etiquetas de Barcos (Eje inferior)
    if df_embarques is not None:
        df_embarques['Arrival_Date'] = pd.to_datetime(df_embarques['Arrival Window'])
        x_min_lim, x_max_lim = ax.get_xlim()
        y_min_lim, y_max_lim = ax.get_ylim()
        
        for _, row in df_embarques.iterrows():
            f_barco = row['Arrival_Date']
            n_barco = row['Terminal Code']
            
            # Solo graficar si cae dentro del rango de fechas mostrado
            if x_min_lim <= mdates.date2num(f_barco) <= x_max_lim:
                # Línea guía vertical punteada
                ax.axvline(f_barco, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)
                
                # Nombre del barco colgando hacia abajo desde el fondo de la gráfica
                ax.text(f_barco, y_min_lim, f" {n_barco}", 
                        rotation=90, verticalalignment='top', horizontalalignment='center',
                        fontsize=8, color='blue', fontweight='bold', alpha=0.7)
        
        # Desactivar los números del eje X inferior para que solo se vean los barcos
        ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)

    # 7. Leyenda
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=10, title="Agentes y Límites")
    
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