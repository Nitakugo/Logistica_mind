import fitz
import json
import os
import re
from collections import Counter

# --- CONFIGURACIÓN DE NLP PARA LOGÍSTICA ---

# Corrección de errores de lectura de PDF (Ligaduras)
LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
}

# Stopwords extendidas (Ruido detectado y fragmentos de palabras rotas)
STOPWORDS = set([
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o", "no", "si", "para", "por", "con", "en", 
    "su", "sus", "al", "lo", "como", "más", "pero", "este", "esta", "estos", "estas", "que", "es", "son", "fue", "era", "se",
    "también", "entre", "cómo", "debe", "cuál", "cuando", "donde", "quien", "quienes", "todo", "toda", "todos", "todas",
    "hacer", "hacia", "desde", "hasta", "cada", "mismo", "misma", "otro", "otra", "otros", "otras", "está", "están",
    "además", "según", "través", "parte", "puede", "pueden", "ser", "muy", "tan", "bien", "solo", "sólo",
    "cacion", "ficacion", "cion", "idat", "ment"
])

# Glosario Logístico (Prioridad alta para N-gramas)
LOGISTICS_GLOSSARY = [
    "cadena de suministro", "supply chain", "just in time", "cross docking", "lead time",
    "gestión de inventarios", "transporte y distribución", "almacenamiento", "logística integral",
    "operaciones", "proveedores", "demanda", "stock", "eficiencia", "costos logísticos",
    "planificación", "distribución", "outsourcing", "incoterms", "comercio exterior",
    "última milla", "valor agregado", "competitividad", "productividad", "sistema de gestión",
    "red de distribución", "modelo de negocio", "transformación digital", "caja maestra",
    "manejo de materiales", "almacén", "inventario", "transporte", "abastecimiento"
]

def clean_text(text):
    """Limpia el texto, corrige ligaduras y normaliza espacios."""
    # 1. Corregir ligaduras
    for lig, corr in LIGATURES.items():
        text = text.replace(lig, corr)
    
    # 2. Unir palabras cortadas por guion al final de línea
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # 3. Normalizar todos los espacios y saltos de línea a un espacio simple
    text = re.sub(r'\s+', ' ', text).lower()
    
    # 4. Heurística para unir sufijos rotos (ej: "clasi fi cación" -> "clasificación")
    text = re.sub(r'\b(\w+)\s+(fi\s+)?(cacion|ficacion|izacion|idad|mente)\b', r'\1\2\3', text)
    text = text.replace("fi cacion", "ficacion")
    
    # 5. Limpieza final de caracteres no deseados
    text = re.sub(r'[^a-záéíóúüñ\s]', '', text)
    return text

def lemmatize_simple(word):
    """Lemmatización básica para español."""
    if len(word) < 4: return word
    if word.endswith("es"): 
        if word.endswith("ces"): return word[:-3] + "z"
        return word[:-2]
    if word.endswith("s") and not word.endswith("is"):
        return word[:-1]
    return word

def extract_semantic_concepts(text, num=5):
    """Motor de extracción semántica con N-gramas dinámicos y Glosario."""
    text = clean_text(text)
    found_concepts = []
    
    # 1. Buscar términos del glosario (Basado en el texto normalizado)
    for term in LOGISTICS_GLOSSARY:
        count = text.count(term)
        if count > 0:
            weight = 5 if " " in term else 3
            found_concepts.extend([term] * (count * weight))
            
    # 2. Análisis de tokens individuales y bi-gramas automáticos
    words = [w for w in text.split() if len(w) >= 3 and w not in STOPWORDS]
    lemmas = [lemmatize_simple(w) for w in words if lemmatize_simple(w) not in STOPWORDS]
    found_concepts.extend(lemmas)
    
    # Bi-gramas espontáneos
    for i in range(len(lemmas) - 1):
        bigram = f"{lemmas[i]} {lemmas[i+1]}"
        found_concepts.append(bigram)

    # 3. Contar y filtrar por relevancia
    counts = Counter(found_concepts)
    sorted_items = [item[0] for item in counts.most_common(50)]
    final_selection = []
    
    for item in sorted_items:
        is_subpart = any(item in selected for selected in final_selection)
        is_extension = False
        for i, selected in enumerate(final_selection):
            if selected in item and selected != item:
                final_selection[i] = item 
                is_extension = True
                break
        
        if not is_subpart and not is_extension:
            final_selection.append(item)
            
        if len(final_selection) >= num * 3: break 
            
    return list(final_selection)[:num]

def enrich_node_v2(node, doc):
    """Proceso recursivo optimizado."""
    page_num = node.get("page", 1) - 1
    if 0 <= page_num < len(doc):
        text = ""
        # Extraer ventana de 2 páginas para contexto semántico
        for i in range(page_num, min(page_num + 2, len(doc))):
            text += doc.load_page(i).get_text()
        
        node["micro_temas"] = extract_semantic_concepts(text)
    else:
        node["micro_temas"] = []

    for sub in node.get("subsections", []):
        enrich_node_v2(sub, doc)

def run_batch_enrichment():
    """Procesa todos los JSONs en las 4 carpetas de pilares."""
    pillars = [
        "1. Supply Chain Strategist",
        "2. Warehouse Operations Expert",
        "3. Inventory & Planning Expert",
        "4. Transport & Distribution Expert"
    ]
    
    success_count = 0
    total_files = 0
    
    print("="*50)
    print("INICIANDO PROCESAMIENTO POR LOTE (SEMANTIC V2)")
    print("="*50 + "\n")
    
    for pillar in pillars:
        if not os.path.exists(pillar):
            print(f"[!] Advertencia: No existe la carpeta {pillar}")
            continue
            
        print(f"\n>>> Pilar: {pillar}")
        files = [f for f in os.listdir(pillar) if f.endswith(".json")]
        
        for json_file in files:
            total_files += 1
            json_path = os.path.join(pillar, json_file)
            pdf_path = json_path.replace(".json", ".pdf")
            
            if not os.path.exists(pdf_path):
                print(f"    [Error] Sin PDF para: {json_file}")
                continue
                
            try:
                print(f"    -> Procesando: {json_file}")
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                doc = fitz.open(pdf_path)
                for node in data:
                    enrich_node_v2(node, doc)
                doc.close()
                
                # Sobreescribir archivo original
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                success_count += 1
            except Exception as e:
                print(f"    [Error] Falló {json_file}: {str(e)}")
                
    print(f"\n" + "="*50)
    print(f"RESUMEN FINAL")
    print(f"Archivos encontrados: {total_files}")
    print(f"Archivos completados con éxito: {success_count}")
    print(f"="*50)

if __name__ == "__main__":
    run_batch_enrichment()
