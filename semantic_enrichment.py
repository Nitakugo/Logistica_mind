import fitz
import json
import os
import re
from collections import Counter

# Lista básica de stopwords en español para filtrar ruido
STOPWORDS = set([
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o", "no", "si", "para", "por", "con", "en", 
    "su", "sus", "al", "lo", "como", "más", "pero", "este", "esta", "estos", "estas", "que", "es", "son", "fue", "era", "se"
])

# Términos que queremos evitar porque son demasiado genéricos o ruido de PDF
NOISE = set(["pág", "página", "figura", "cuadro", "capítulo", "sección", "edición", "editorial", "isbn", "derechos"])

def extract_keywords(text, num=5):
    """Extrae palabras clave simples basadas en frecuencia."""
    # Limpiar texto: solo letras, pasar a minúsculas
    words = re.findall(r'\b[a-záéíóúüñ]{4,}\b', text.lower())
    # Filtrar stopwords y ruido
    filtered_words = [w for w in words if w not in STOPWORDS and w not in NOISE]
    
    # Contar y devolver los más comunes
    counts = Counter(filtered_words)
    return [item[0] for item in counts.most_common(num)]

def enrich_node(node, doc):
    """Procesa un nodo del JSON de forma recursiva."""
    page_num = node.get("page", 1) - 1
    if 0 <= page_num < len(doc):
        # Extraer texto de la página actual y la siguiente para contexto
        text = ""
        for i in range(page_num, min(page_num + 2, len(doc))):
            text += doc.load_page(i).get_text()
        
        # Extraer micro temas
        node["micro_temas"] = extract_keywords(text)
        print(f"  Procesado: {node['title'][:40]}... -> {node['micro_temas']}")
    else:
        node["micro_temas"] = []

    # Procesar subsecciones
    for sub in node.get("subsections", []):
        enrich_node(sub, doc)

def semantic_pilot():
    pillar_dir = "1. Supply Chain Strategist"
    json_name = "Administración y logística en la cadena de suministros ( etc.) (z-library.sk, 1lib.sk, z-lib.sk).json"
    pdf_name = "Administración y logística en la cadena de suministros ( etc.) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
    
    json_path = os.path.join(pillar_dir, json_name)
    pdf_path = os.path.join(pillar_dir, pdf_name)
    output_path = "prueba_piloto.json"
    
    if not os.path.exists(json_path) or not os.path.exists(pdf_path):
        print("Error: No se encuentran los archivos fuente en '1. Supply Chain Strategist'")
        return

    print(f"Iniciando enriquecimiento semántico de: {json_name}")
    
    # Cargar datos
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Abrir PDF
    doc = fitz.open(pdf_path)
    
    # Enriquecer cada nodo en la raíz
    for node in data:
        enrich_node(node, doc)
        
    doc.close()
    
    # Guardar resultado
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"\nFinalizado. Resultado guardado en: {output_path}")

if __name__ == "__main__":
    semantic_pilot()
