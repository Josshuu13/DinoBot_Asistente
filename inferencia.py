import re
import unicodedata
from analisis import *
from grafos import *
from tokenizacion import similitud_semantica, STOP_WORDS

def extraer_proposiciones(tema, prompt, kb):

    if tema == "medicina":
        proposiciones = extraer_medico(kb,False)
    if tema == "metro":
        proposiciones = extraer_metro(kb,False)
    if tema == "musica":
        proposiciones = extraer_musica(kb,False)
    if tema == "tema general":
        proposiciones = extraer_conversacion_general(kb)

    proposiciones_obetenidas = []

    for proposicion in proposiciones:
        if proposicion in prompt:
            proposiciones_obetenidas.append(proposicion)

    return proposiciones_obetenidas

def inferir_recomendacion_musica(prompt, kb):
    prompt = prompt.lower()

    lista_generos = cargar_kb_musica(kb)
    proposiciones = extraer_proposiciones("musica",prompt,kb)

    inferencias = []

    #Inferir Por silogismo hipotetico
    #buscar por genero: Si Rock -> Artistas de Rock, Artista Rock -> cancion_Artista Rock: Rock -> CancionesRock,ArtistasRock
    for genero in lista_generos:
        if genero.nombre in proposiciones:
            for artista in genero.artistas:
                if not(artista.nombre in proposiciones or artista.nombre in inferencias):
                    print(f"{genero.nombre} -> {artista.nombre}\n")
                    for cancion in artista.canciones:
                        if not(cancion.nombre in proposiciones or cancion.nombre in inferencias):
                            print(f"{genero.nombre} -> {artista.nombre} -> {cancion.nombre}")
                            print(f"{genero.nombre} -> {cancion.nombre}\n")
                            inferencias.append(cancion.nombre + " de " + artista.nombre)

    #Inferir por Artista
    #Si Artista -> Genero_Artista, Del Genero -> Artistas, Artista -> Canciones: Artista -> Canciones_Similares,Artistas_similares
        for Artista in genero.artistas:
            if Artista.nombre in prompt:
                for artista in genero.artistas:
                    if not(artista.nombre in prompt or artista.nombre in inferencias): 
                        print(f"{Artista.nombre} -> {artista.nombre}\n")

                    for cancion in artista.canciones:
                        if not(cancion.nombre in prompt or cancion.nombre in inferencias): 
                            inferencias.append(cancion.nombre + " de " + artista.nombre)
                            print(f"{Artista.nombre} -> {artista.nombre} -> {cancion.nombre}")
                            print(f"{Artista.nombre} -> {cancion.nombre}\n")

    #Similra para Canciones
            for cancion in Artista.canciones:
                if cancion.nombre in prompt:
                    for artista in genero.artistas:
                        if not(artista.nombre in prompt or artista.nombre in inferencias): 
                            print(f"{cancion.nombre} -> {genero.nombre}")                            
                            print(f"{genero.nombre} -> {artista.nombre}")
                            print(f"{cancion.nombre} -> {artista.nombre}\n")

                        for cancion in artista.canciones:
                            if not(cancion.nombre in prompt or cancion.nombre in inferencias): 
                                inferencias.append(cancion.nombre + " de " + artista.nombre)
                                print(f"{Artista.nombre} -> {artista.nombre} -> {cancion.nombre}")
                                print(f"{Artista.nombre} -> {cancion.nombre}\n")
    return inferencias
    

def inferir_enfermedad(prompt, kb_path):
    sintomas_usuario = inferir_sintomas(prompt, kb_path)
    print(f"\nsintomas inferidos: {sintomas_usuario}\n")

    if not sintomas_usuario:
        return -1

    enfermedades = cargar_kb_medicina(kb_path)

    enfermedades_probables = []  # tuplas (enfermedad, probabilidad, coincidencias)

    for enf in enfermedades:
            sintomas_enf = [s.nombre for s in enf.sintomas]

            coincidencias = 0
            for s in sintomas_usuario:
                if s in sintomas_enf:
                    coincidencias += 1
                    print(f"{s} -> {enf.nombre}\n")

            if coincidencias == 0:
                continue

            prob = coincidencias / len(sintomas_enf)

            enfermedades_probables.append((enf.nombre, prob, coincidencias))
            print(f"{enf.nombre} con un {prob} de probabilidad\n")

    if not enfermedades_probables:
        return -1

    # Ordenamos por probabilidad y, en empate, por número de síntomas que coinciden
    enfermedades_probables.sort(key=lambda x: (x[1], x[2]), reverse=True)
    print(f"{enfermedades_probables}\n")

    # Devolvemos solo las 3 más probables, con su porcentaje
    return [f"{nombre} ({round(prob * 100)}% de coincidencia)"
            for nombre, prob, _ in enfermedades_probables[:3]]


def inferir_sintomas(prompt, kb):

    with open(kb, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultados = []
    sintomas = data.get("sintomas", {})

    prompt_norm = _normalizar(prompt)
    # Partimos el mensaje en fragmentos ("tengo fiebre", "tos seca", ...) para comparar
    # cada síntoma contra una idea a la vez y no contra toda la oración.
    fragmentos = [f.strip() for f in re.split(r",|;|\.|\by\b|\be\b|\bpero\b|\btambien\b", prompt_norm) if f.strip()]
    # Ignoramos fragmentos negados ("no tengo fiebre", "sin tos")
    fragmentos = [f for f in fragmentos if not re.match(r"^(no tengo|no siento|sin)\b", f)]
    raices_fragmentos = [_raices(f) for f in fragmentos]

    for sintoma, descripciones in sintomas.items():
        for frase in descripciones:
            frase_norm = _normalizar(frase)

            # 1. Coincidencia exacta de la frase dentro de algún fragmento
            if any(re.search(r"\b" + re.escape(frase_norm) + r"\b", f) for f in fragmentos):
                print(f"{frase} -> {sintoma} (coincidencia exacta)\n")
                resultados.append(sintoma)
                break

            # 2. Coincidencia por palabras clave: todas las raíces importantes de la frase
            #    aparecen en un mismo fragmento ("me duele el estomago" ~ "dolor de estomago")
            raices_frase = _raices(frase_norm)
            if not raices_frase or raices_frase == {"dolor"}:
                continue  # frases demasiado genéricas como "me duele todo"
            if any(raices_frase <= rf for rf in raices_fragmentos):
                print(f"{frase} -> {sintoma} (palabras clave)\n")
                resultados.append(sintoma)
                break

    return resultados


# Sinónimos que se tratan como la misma palabra antes de comparar
SINONIMOS = {"duele": "dolor", "duelen": "dolor", "dolores": "dolor", "adolorido": "dolor",
             "panza": "estomago", "barriga": "estomago", "calentura": "fiebre"}

def _raices(texto):
    """Palabras importantes del texto, sin stopwords, reducidas a sus primeras 5 letras."""
    raices = set()
    for palabra in re.findall(r"[a-zñ]+", texto):
        if palabra in STOP_WORDS:
            continue
        palabra = SINONIMOS.get(palabra, palabra)
        raices.add(palabra[:5])
    return raices


def _normalizar(texto):
    """Minúsculas, sin acentos y sin signos de puntuación (excepto comas y puntos)."""
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                    if unicodedata.category(c) != 'Mn')
    texto = re.sub(r"[^a-z0-9ñ ,.;]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()
