import json
import string
import unicodedata
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

def cargar_datos_musicales(ruta_json):
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data["canciones"])

def recomendar_canciones(input_texto, ruta_json):
    df = cargar_datos_musicales(ruta_json)
    # Minúsculas y sin acentos, para que "melancólico" coincida con "melancolico"
    input_texto = ''.join(c for c in unicodedata.normalize('NFD', input_texto.lower())
                          if unicodedata.category(c) != 'Mn')
    
    # 1. FILTRADO POR GÉNERO 
    generos_disponibles = df['genero'].unique()
    for genero in generos_disponibles:
        if genero in input_texto:
            df = df[df['genero'] == genero].copy()
            break 
    
    if len(df) < 1:
        df = cargar_datos_musicales(ruta_json)

    # 2. DICCIONARIO DE EMOCIONES
    # (Energía, Valencia)
    emociones = {
        # Tristeza / Calma
        "triste": (0.2, 0.1), "deprimente": (0.2, 0.0), "llorar": (0.3, 0.1),
        "melancolico": (0.3, 0.3), "nostalgico": (0.4, 0.4), "soledad": (0.2, 0.2),
        "relajarme": (0.1, 0.6), "dormir": (0.05, 0.5), "calmado": (0.2, 0.7),
        "suave": (0.3, 0.6), "paz": (0.2, 0.8), "lento": (0.3, 0.5),
        
        # Felicidad / Fiesta
        "feliz": (0.7, 0.9), "alegre": (0.8, 0.95), "contento": (0.6, 0.8),
        "fiesta": (0.95, 0.9), "bailar": (0.9, 0.9), "animado": (0.8, 0.8),
        "motivacion": (0.8, 0.7), "arriba": (0.9, 0.8), "rapido": (0.9, 0.6),
        
        # Intensidad / Ira
        "intensa": (0.9, 0.5), "rock": (0.8, 0.5), "enojado": (0.9, 0.2),
        "furia": (1.0, 0.1), "ejercicio": (0.9, 0.6), "gym": (0.95, 0.7),
        "intenso": (0.9, 0.5), "entrenar": (0.9, 0.6), "correr": (0.85, 0.65),

        # Concentración / Tranquilidad
        "tranquilo": (0.2, 0.7), "tranquila": (0.2, 0.7), "estudiar": (0.3, 0.6),
        "concentrarme": (0.3, 0.6), "relajante": (0.15, 0.65)
    }

    negaciones = ["no", "sin", "nada", "ni", "nunca", "menos", "tampoco"]

    # Valores por defecto (Neutro)
    target_energia = 0.5
    target_valencia = 0.5
    encontro_emocion = False
    fue_negado = False

    # 3. LÓGICA DE NEGACIÓN Y ASIGNACIÓN
    # Tokenizamos manualmente simple para poder ver índices
    palabras = input_texto.split()

    for i, palabra in enumerate(palabras):
        palabra_clean = palabra.strip(".,!¡?¿")

        if palabra_clean in emociones:
            base_e, base_v = emociones[palabra_clean]
            encontro_emocion = True
            
            negacion_activa = False

            # --- CORRECCIÓN: MIRAR MÁS ATRÁS ---
            # Miramos hasta 4 palabras hacia atrás buscando un "no"
            ventana_atras = 4 
            start_index = max(0, i - ventana_atras)
            
            # Obtenemos las palabras previas al índice actual
            palabras_previas = palabras[start_index : i]
            
            for prev in palabras_previas:
                if prev.strip(".,!¡?¿") in negaciones:
                    negacion_activa = True
                    fue_negado = True
                    break # Encontramos una negación, dejamos de buscar

            if negacion_activa:
                # Invertir valores
                target_energia = 1.0 - base_e
                target_valencia = 1.0 - base_v
            else:
                target_energia = base_e
                target_valencia = base_v

    vector_usuario = [target_energia, target_valencia]

    # 4. CÁLCULO VECTORIAL
    features = df[['energia', 'valencia']].to_numpy()

    # Usamos distancia euclidiana en el plano Energía-Valencia.
    # (La similitud coseno solo compara la dirección del vector, así que una canción
    #  triste (0.2, 0.1) y una intensa (0.8, 0.4) le parecían iguales.)
    distancias = euclidean_distances(features, [vector_usuario]).ravel()
    distancia_maxima = np.sqrt(2)  # distancia entre (0,0) y (1,1)
    df['similitud'] = 1 - distancias / distancia_maxima

    # Ordenamos
    recomendaciones = df.sort_values(by='similitud', ascending=False).head(3)
    
    respuesta = []
    
    # Mensaje de depuración amable para el usuario
    if fue_negado:
        respuesta.append("(Entendido, buscaremos lo opuesto a eso...)")
    elif not encontro_emocion:
        respuesta.append("(Te daré algo balanceado)")
    
    for _, row in recomendaciones.iterrows():
        match_score = int(row['similitud']*100)
        texto = f"- {string.capwords(row['nombre'])} de {string.capwords(row['artista'])} ({row['genero']}, Match: {match_score}%)"
        respuesta.append(texto)
        
    return respuesta