import json
import heapq
import unicodedata
import difflib
from collections import defaultdict
import re

# 1. CARGA DE DATOS
# ==========================================
def cargar_datos_json(ruta_json="kb/kb_metro.json"):
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    lineas = []
    segmentos_por_linea = []
    
    costo_transbordo_global = data.get("costo_transbordo", 350)

    diccionario_lineas = data.get("lineas", {})
    
    for nombre_linea, info in diccionario_lineas.items():
        estaciones_dict = info.get("estaciones", {})
        nombres_estaciones = list(estaciones_dict.keys())
        distancias = []
        
        claves = list(estaciones_dict.keys())
        for i in range(len(claves) - 1):
            est_actual = claves[i]
            datos = estaciones_dict[est_actual] 
            dist_sig = datos[1] 
            if dist_sig is None: dist_sig = 0 
            distancias.append(int(dist_sig))

        lineas.append(nombres_estaciones)
        segmentos_por_linea.append(distancias)

    return lineas, segmentos_por_linea, costo_transbordo_global

# ==========================================
# 2. UTILIDADES Y GRAFOS
# ==========================================

def metros_a_minutos(distancia_m, velocidad_m_por_min = 350):
    return distancia_m / velocidad_m_por_min

def tiempo_total(min_en_float):
    total_seg = int(round(min_en_float * 60))
    minutos = total_seg // 60
    segundos = total_seg % 60
    texto = []
    if minutos > 0: texto.append(f"{minutos} min")
    if segundos > 0: texto.append(f"{segundos} s")
    return " ".join(texto) if texto else "0 s"

def nombre_linea_bonito(idx):
    if idx == 9: return "LA"
    if idx == 10: return "LB"
    return f"L{idx+1}"

def construccion_grafo(lineas, segmentos_por_linea, costo_transbordo_global):
    grafo = {}
    
    # Conexiones lineales
    for idx, linea in enumerate(lineas):
        linea_nombre = nombre_linea_bonito(idx)
        segmentos = segmentos_por_linea[idx]
        
        for i in range(len(linea)-1):
            est_A = linea[i]
            est_B = linea[i+1]
            nodo_A = f"{est_A}_{linea_nombre}"
            nodo_B = f"{est_B}_{linea_nombre}"
            
            if i < len(segmentos):
                tiempo = metros_a_minutos(segmentos[i])
                grafo.setdefault(nodo_A, []).append((nodo_B, tiempo))
                grafo.setdefault(nodo_B, []).append((nodo_A, tiempo))
    
    # Transbordos
    estaciones_lineas = defaultdict(list)
    for idx, linea in enumerate(lineas):
        nombre_linea = nombre_linea_bonito(idx)
        for estacion in linea:
            estaciones_lineas[estacion].append(nombre_linea)
            
    tiempo_t = metros_a_minutos(costo_transbordo_global)

    for est, lista_lineas in estaciones_lineas.items():
        if len(lista_lineas) > 1:
            for i in range(len(lista_lineas)):
                for j in range(i+1, len(lista_lineas)):
                    l1 = lista_lineas[i]
                    l2 = lista_lineas[j]
                    grafo[f"{est}_{l1}"].append((f"{est}_{l2}", tiempo_t))
                    grafo[f"{est}_{l2}"].append((f"{est}_{l1}", tiempo_t))
    return grafo

def generar_heuristica(grafo, objetivo):
    grafo_inv = {nodo: [] for nodo in grafo}
    for origen, vecinos in grafo.items():
        for destino, costo in vecinos:
            grafo_inv[destino].append((origen, costo))
    
    heuristica = {nodo: float("inf") for nodo in grafo}
    heuristica[objetivo] = 0
    heap = [(0, objetivo)]

    while heap:
        costo_actual, nodo = heapq.heappop(heap)
        if costo_actual > heuristica[nodo]:
            continue
        for vecino, costo in grafo_inv[nodo]:
            nuevo = costo_actual+costo
            if nuevo < heuristica[vecino]:
                heuristica[vecino] = nuevo
                heapq.heappush(heap, (nuevo, vecino))
    return heuristica

# ==========================================
# 3. ALGORITMO A* 

def a_star_search(grafo, inicio, objetivo, heuristica):

    h_inicial = heuristica.get(inicio, 0)
    # Inicializamos con f = h (porque g=0)
    cola = [(h_inicial, 0, inicio, [])]
    
    visited = {} 

    while cola:
        f, g, nodo, camino = heapq.heappop(cola)
        
        # Si ya llegamos a este nodo con un costo menor o igual, lo saltamos
        if nodo in visited and visited[nodo] <= g:
            continue
        visited[nodo] = g
        
        camino_actualizado = camino + [nodo]

        if nodo == objetivo:
            return camino_actualizado, g # Devolvemos el costo acumulado real

        for vecino, peso in grafo.get(nodo, []):
            nuevo_g = g + peso
            nuevo_f = nuevo_g + heuristica.get(vecino, 0)
            
            # Guardamos explícitamente 'nuevo_g' en la tupla
            heapq.heappush(cola, (nuevo_f, nuevo_g, vecino, camino_actualizado))
            
    return None

# ==========================================
# 4. INICIALIZACIÓN Y BÚSQUEDA
# ==========================================

try:
    MIS_LINEAS, MIS_SEGMENTOS, COSTO_T = cargar_datos_json("kb/kb_metro.json")
    GRAFO_GLOBAL = construccion_grafo(MIS_LINEAS, MIS_SEGMENTOS, COSTO_T)
    
    MAPA_NODOS = defaultdict(list)
    for nodo in GRAFO_GLOBAL.keys():
        est = nodo.split("_")[0]
        MAPA_NODOS[est.lower()].append(nodo)
        
    LISTA_NOMBRES = list(MAPA_NODOS.keys())
    
except Exception as e:
    print(f"Error cargando JSON: {e}")
    MIS_LINEAS, MIS_SEGMENTOS, GRAFO_GLOBAL, MAPA_NODOS, LISTA_NOMBRES = [], [], {}, {}, []

def normalizar(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')

def detectar_estaciones(prompt):
    """
    Detecta estaciones en el orden en que aparecen en el texto.
    1) Primero busca nombres exactos como palabras completas (de más largo a más corto),
       así 'pino suarez' gana sobre 'juarez' y 'tacubaya' no se confunde con 'tacuba'.
    2) Luego, en las palabras que sobran, busca nombres parecidos (errores de dedo).
    """
    prompt_norm = re.sub(r"[^a-z0-9 ]", " ", normalizar(prompt))
    prompt_norm = re.sub(r"\s+", " ", prompt_norm).strip()
    ocupado = [False] * len(prompt_norm)
    encontradas = []  # (posicion, nombre)

    # 1. Coincidencias exactas (palabra completa), nombres largos primero
    for nombre in sorted(LISTA_NOMBRES, key=len, reverse=True):
        patron = r"\b" + re.escape(normalizar(nombre)) + r"\b"
        for m in re.finditer(patron, prompt_norm):
            if not any(ocupado[m.start():m.end()]):
                encontradas.append((m.start(), nombre))
                for i in range(m.start(), m.end()):
                    ocupado[i] = True

    # 2. Coincidencias aproximadas en las palabras que no se usaron
    for m in re.finditer(r"[a-z0-9]+", prompt_norm):
        palabra = m.group()
        if len(palabra) < 4 or any(ocupado[m.start():m.end()]):
            continue
        matches = difflib.get_close_matches(palabra, LISTA_NOMBRES, n=1, cutoff=0.8)
        if matches:
            encontradas.append((m.start(), matches[0]))

    encontradas.sort()

    unicas = []
    for _, x in encontradas:
        if x not in unicas: unicas.append(x)

    return unicas

def formatear_salida(camino, costo):
    salida = ["🚇 **Ruta Sugerida:**"]
    
    nodo_inicio = camino[0]
    est_inicio = nodo_inicio.split("_")[0]
    linea_inicio = nodo_inicio.split("_")[1]
    
    salida.append(f"📍Inicio: {est_inicio.title()} ({linea_inicio})")

    linea_actual = linea_inicio
    
    for i in range(1, len(camino)):
        nodo = camino[i]
        est_nombre = nodo.split("_")[0]
        linea_nodo = nodo.split("_")[1]

        if linea_nodo != linea_actual:
            salida.append(f"🔄 **Transbordo en {est_nombre.title()}:** Cambia a {linea_nodo}")
            linea_actual = linea_nodo 

    nodo_fin = camino[-1]
    est_fin = nodo_fin.split("_")[0]
    
    salida.append(f"🏁Llegada: {est_fin.title()}")

    tiempo_texto = tiempo_total(costo)
    salida.append(f"\n⏱️Tiempo estimado: {tiempo_texto}")
    
    salida.append("\n⚠️Nota: Los tiempos son aproximados. Revisa la app oficial del Metro o las pantallas de la estación para avisos en tiempo real.")

    return "\n".join(salida)

def resolver_ruta_metro(prompt):
    estaciones = detectar_estaciones(prompt)
    
    if len(estaciones) < 2:
        return f"Entendí que hablas del metro, pero necesito saber origen y destino. Solo detecté: {estaciones}"

    origen = estaciones[0] 
    destino = estaciones[1] 

    if origen not in MAPA_NODOS or destino not in MAPA_NODOS:
        return f"No encontré las estaciones '{origen}' o '{destino}' en mi base de datos."

    nodos_origen = MAPA_NODOS[origen]
    nodos_destino = MAPA_NODOS[destino]

    mejor_ruta = None
    menor_costo = float('inf')

    for start_node in nodos_origen:
        for end_node in nodos_destino:
            h = generar_heuristica(GRAFO_GLOBAL, end_node)
            res = a_star_search(GRAFO_GLOBAL, start_node, end_node, h)
            if res:
                camino, costo = res
                if costo < menor_costo:
                    menor_costo = costo
                    mejor_ruta = camino

    if mejor_ruta:
        return formatear_salida(mejor_ruta, menor_costo)
    
    return f"No se encontró una ruta válida entre {origen} y {destino}."