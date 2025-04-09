import folium
from folium.plugins import Draw
import tkinter as tk
from tkinter import messagebox, Menu
import webbrowser
import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2

# Función para calcular la distancia haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distancia_km = R * c
    distancia_metros = distancia_km * 1000
    return distancia_metros

# Función para crear un mapa
def crear_mapa():
    try:
        mapa = folium.Map(location=[19.274528609523216, -98.95378718298933], zoom_start=15)
        Draw(
            export=True,
            filename="postes.geojson",
            draw_options={
                "polyline": False,
                "rectangle": False,
                "circle": False,
                "marker": True,
            }
        ).add_to(mapa)
        mapa.save("mapa_postes.html")
        messagebox.showinfo("Éxito", "Mapa generado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el mapa: {e}")

# Función para abrir el mapa
def abrir_mapa():
    try:
        if os.path.exists("mapa_postes.html"):
            webbrowser.open("mapa_postes.html")
        else:
            messagebox.showwarning("Advertencia", "Primero genera el mapa.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el mapa: {e}")

# Función para determinar el tipo de fibra
def determinar_tipo_fibra(distancia):
    tipos_fibra = [5, 50, 80, 100, 120, 150, 200, 250, 300, 350, 600]
    for tipo in tipos_fibra:
        if distancia <= tipo:
            return f"Fibra {tipo}m"
    return f"Fibra {tipos_fibra[-1]}m"

# Función para calcular costos
def calcular_costos(distancias):
    # Costos unitarios (pueden ser modificados por el usuario)
    costos = {
        "fibra": {
            "Fibra 5m": 0.50,  # Costo por metro de fibra de 5m
            "Fibra 50m": 0.45,
            "Fibra 80m": 0.40,
            "Fibra 100m": 0.35,
            "Fibra 120m": 0.30,
            "Fibra 150m": 0.25,
            "Fibra 200m": 0.20,
            "Fibra 250m": 0.15,
            "Fibra 300m": 0.10,
            "Fibra 350m": 0.08,
            "Fibra 600m": 0.05,
        },
        "instalacion": {
            "Aérea": 1.00,  # Costo por metro de instalación aérea
            "Subterránea": 2.50,  # Costo por metro de instalación subterránea
        },
        "poste": 100.00,  # Costo por poste
    }

    costo_total = 0
    detalles_costos = []  # Lista para almacenar los detalles de los costos
    for i, j, distancia, tipo_fibra, tipo_instalacion in distancias:
        # Costo de la fibra
        costo_fibra = costos["fibra"][tipo_fibra] * distancia
        # Costo de instalación
        costo_instalacion = costos["instalacion"][tipo_instalacion] * distancia
        # Sumar al costo total
        costo_total += costo_fibra + costo_instalacion
        # Guardar detalles de los costos
        detalles_costos.append((i, j, distancia, tipo_fibra, tipo_instalacion, costo_fibra, costo_instalacion))
    # Costo de los postes
    costo_total += costos["poste"] * (len(distancias) + 1)  # +1 porque hay n+1 postes para n conexiones
    return costo_total, detalles_costos

# Función para procesar los postes
def procesar_postes():
    try:
        if os.path.exists("postes.geojson"):
            with open("postes.geojson", "r") as file:
                data = json.load(file)
            postes = []
            for feature in data["features"]:
                if feature["geometry"]["type"] == "Point":
                    lon, lat = feature["geometry"]["coordinates"]
                    postes.append((lat, lon))
            G = nx.Graph()
            for i, (lat, lon) in enumerate(postes, start=1):
                G.add_node(i, pos=(lon, lat))
            distancias = []
            for i in range(1, len(postes)):
                lat1, lon1 = postes[i - 1]
                lat2, lon2 = postes[i]
                distancia = haversine(lat1, lon1, lat2, lon2)
                tipo_fibra = determinar_tipo_fibra(distancia)
                # Pedir al usuario que seleccione el tipo de instalación para esta conexión
                tipo_instalacion = messagebox.askquestion(
                    "Tipo de Instalación",
                    f"¿La conexión entre Poste {i} y Poste {i + 1} será Aérea? (Sí para Aérea, No para Subterránea)"
                )
                tipo_instalacion = "Aérea" if tipo_instalacion == "yes" else "Subterránea"
                G.add_edge(i, i + 1, weight=distancia, tipo_fibra=tipo_fibra, tipo_instalacion=tipo_instalacion)
                distancias.append((i, i + 1, distancia, tipo_fibra, tipo_instalacion))
            pos = nx.get_node_attributes(G, 'pos')
            labels = nx.get_edge_attributes(G, 'weight')
            tipos_fibra = nx.get_edge_attributes(G, 'tipo_fibra')
            tipos_instalacion = nx.get_edge_attributes(G, 'tipo_instalacion')
            plt.figure(figsize=(12, 10))  # Aumentamos el tamaño de la figura para la tabla
            nx.draw_networkx_nodes(G, pos, node_shape='^', node_size=500, node_color='lightblue')
            
            # Mapa de colores para los tipos de fibra
            colores_fibra = {
                "Fibra 5m": "red",
                "Fibra 50m": "orange",
                "Fibra 80m": "yellow",
                "Fibra 100m": "green",
                "Fibra 120m": "blue",
                "Fibra 150m": "purple",
                "Fibra 200m": "brown",
                "Fibra 250m": "pink",
                "Fibra 300m": "gray",
                "Fibra 350m": "cyan",
                "Fibra 600m": "magenta"
            }
            
            # Dibujar aristas con colores según el tipo de fibra
            for edge in G.edges(data=True):
                i, j, data = edge
                color = colores_fibra.get(data["tipo_fibra"], "black")  # Color predeterminado si no se encuentra
                if data["tipo_instalacion"] == "Aérea":
                    # Línea punteada para fibra aérea
                    nx.draw_networkx_edges(G, pos, edgelist=[(i, j)], edge_color=color, width=2, style="dashed")
                else:
                    # Línea sólida para fibra subterránea
                    nx.draw_networkx_edges(G, pos, edgelist=[(i, j)], edge_color=color, width=2, style="solid")
            
            nx.draw_networkx_labels(G, pos, font_size=10, font_color='darkred')
            edge_labels = {(i, j): f"{labels[(i, j)]:.2f} m\n{tipos_fibra[(i, j)]}" for i, j in labels}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
            
            # Crear una leyenda personalizada
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color=color, linestyle='--' if tipo == "Aérea" else '-', lw=2, label=f"{tipo}: {fibra}")
                for fibra, color in colores_fibra.items() for tipo in ["Aérea", "Subterránea"]
            ]
            
            # Mostrar la leyenda de tipos de instalación
            plt.legend(handles=legend_elements, loc='upper right', title="Tipo de Instalación y Fibra", bbox_to_anchor=(1.25, 1))
            
            # Agregar un recuadro con los tipos de fibra óptica posibles
            tipos_fibra_posibles = list(colores_fibra.keys())
            texto_leyenda = "Tipos de Fibra Óptica:\n" + "\n".join(tipos_fibra_posibles)
            
            # Calcular el costo total y los detalles de los costos
            costo_total, detalles_costos = calcular_costos(distancias)
            
            # Agregar el texto al gráfico (tipos de fibra y costo total)
            plt.text(
                1.05,  # Posición X (fuera del gráfico)
                0.2,   # Posición Y (más abajo para evitar superposición)
                f"{texto_leyenda}\n\nCosto Total: ${costo_total:.2f}",
                transform=plt.gca().transAxes,  # Usar coordenadas relativas al gráfico
                fontsize=10,
                verticalalignment='center',
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5')
            )
            
            # Crear una tabla con los detalles de los costos
            tabla_data = [["Poste Inicial", "Poste Final", "Distancia (m)", "Tipo Fibra", "Instalación", "Costo Fibra ($)", "Costo Instalación ($)"]]
            for i, j, distancia, tipo_fibra, tipo_instalacion, costo_fibra, costo_instalacion in detalles_costos:
                tabla_data.append([i, j, f"{distancia:.2f}", tipo_fibra, tipo_instalacion, f"{costo_fibra:.2f}", f"{costo_instalacion:.2f}"])
            
            # Dibujar la tabla en la parte inferior del gráfico
            tabla = plt.table(
                cellText=tabla_data,
                colLabels=None,
                loc='bottom',
                bbox=[0.1, -0.5, 0.8, 0.4]  # Ajustar la posición y tamaño de la tabla
            )
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(10)
            tabla.scale(1, 1.5)
            
            plt.title("Grafo de Postes con Distancias y Tipo de Fibra")
            plt.axis('off')
            plt.tight_layout()  # Ajustar el layout para que la leyenda no se corte
            plt.show()
            
            print("Distancias entre postes y tipo de fibra:")
            for i, j, distancia, tipo_fibra, tipo_instalacion in distancias:
                print(f"Distancia entre Poste {i} y Poste {j}: {distancia:.2f} m, Tipo de fibra: {tipo_fibra}, Instalación: {tipo_instalacion}")
            messagebox.showinfo("Éxito", f"Se generó el grafo con {len(postes)} postes.")
        else:
            messagebox.showwarning("Advertencia", "No se encontraron postes marcados.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron procesar los postes: {e}")

# Función para mostrar ayuda
def mostrar_ayuda():
    ayuda_texto = """
    Instrucciones:
    1. Genera un mapa y marca los postes.
    2. Procesa los postes para generar el grafo.
    3. Selecciona el tipo de instalación (Aérea o Subterránea) para cada conexión.
    4. Visualiza y exporta los resultados.
    """
    messagebox.showinfo("Ayuda", ayuda_texto)

# Crear la ventana principal
root = tk.Tk()
root.title("Colocar Postes Geográficamente")
root.geometry("400x400")  # Tamaño de la ventana
root.resizable(False, False)  # Evitar que se redimensione

# Estilo de la interfaz
root.configure(bg="#f0f0f0")  # Color de fondo

# Título de la aplicación
titulo = tk.Label(
    root,
    text="Herramienta de Planificación de Postes",
    font=("Arial", 16, "bold"),
    bg="#f0f0f0",
    fg="#333333"
)
titulo.pack(pady=10)

# Descripción
descripcion = tk.Label(
    root,
    text="Selecciona una opción para comenzar:",
    font=("Arial", 12),
    bg="#f0f0f0",
    fg="#555555"
)
descripcion.pack(pady=5)

# Botón para generar el mapa
boton_generar_mapa = tk.Button(
    root,
    text="Generar Mapa",
    command=crear_mapa,
    font=("Arial", 12),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10
)
boton_generar_mapa.pack(pady=10)

# Botón para abrir el mapa
boton_abrir_mapa = tk.Button(
    root,
    text="Abrir Mapa",
    command=abrir_mapa,
    font=("Arial", 12),
    bg="#2196F3",
    fg="white",
    padx=20,
    pady=10
)
boton_abrir_mapa.pack(pady=10)

# Botón para procesar los postes
boton_procesar_postes = tk.Button(
    root,
    text="Procesar Postes y Generar Grafo",
    command=procesar_postes,
    font=("Arial", 12),
    bg="#FF9800",
    fg="white",
    padx=20,
    pady=10
)
boton_procesar_postes.pack(pady=10)

# Menú de Ayuda
menu_bar = Menu(root)
root.config(menu=menu_bar)
menu_ayuda = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Ayuda", menu=menu_ayuda)
menu_ayuda.add_command(label="Instrucciones", command=mostrar_ayuda)

# Ejecutar la interfaz
root.mainloop()