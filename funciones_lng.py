# funciones_lng.py
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
    
    # Diccionario para guardar los resultados
    dataframes = {}

    # Validación y carga de Consumo
    if os.path.exists(path_consumo):
        dataframes['consumo'] = pd.read_csv(path_consumo)
        print(f"✅ {file_consumo} cargado correctamente.")
    else:
        print(f"❌ Error: No se encontró {file_consumo} en la ruta.")

    # Validación y carga de Embarques
    if os.path.exists(path_embarque):
        dataframes['embarque'] = pd.read_csv(path_embarque)
        print(f"✅ {file_embarque} cargado correctamente.")
    else:
        print(f"❌ Error: No se encontró {file_embarque} en la ruta.")
        
    return df_consumo, df_embarque

def graficar_inventario_agentes(df):
    # 1. Preparación de datos
    df_plot = df.copy()
    
    # Convertir Datetext (20260101) a formato datetime real
    df_plot['Date'] = pd.to_datetime(df_plot['Datetext'].astype(str), format='%Y%m%d')
    
    # Crear un pivote para tener una columna por cada Agente
    # Esto facilita graficar cada uno como una línea independiente
    df_pivot = df_plot.pivot(index='Date', columns='Agente', values='Opening')
    
    # Calcular la línea de TOTAL (Suma de todos los agentes por día)
    df_pivot['TOTAL_SYSTEM'] = df_pivot.sum(axis=1)

    # 2. Configuración de la Gráfica (Estilo Ingeniería)
    fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
    
    # Graficar cada Agente con líneas delgadas
    for agente in df_pivot.columns:
        if agente != 'TOTAL_SYSTEM':
            ax.plot(df_pivot.index, df_pivot[agente], label=agente, alpha=0.6, linewidth=1.5)
    
    # Graficar el TOTAL con una línea gruesa y destacada (como la roja de tu imagen)
    ax.plot(df_pivot.index, df_pivot['TOTAL_SYSTEM'], label='TOTAL SYSTEM', 
            color='red', linewidth=3, linestyle='-')

    # 3. Estética de los Ejes
    ax.set_title('Niveles de Apertura de Inventario por Agente y Total', fontsize=14, fontweight='bold')
    ax.set_ylabel('Opening Level (Units)', fontsize=12)
    ax.set_xlabel('Fecha', fontsize=12)
    
    # Cuadrícula (Grid) similar a la de Mejillones
    ax.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Formatear el eje X para que muestre meses/días correctamente
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    # Leyenda fuera del gráfico para que no tape los datos
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Agentes")
    
    return fig