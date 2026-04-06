import json
import os

def extract_topics_recursive(node, book_title, topics_dict):
    """Extrae micro_temas de un nodo y sus subsecciones, añadiéndolos al índice invertido."""
    micro_temas = node.get("micro_temas", [])
    title = node.get("title", "Sin título")
    page = node.get("page", 0)
    
    for tema in micro_temas:
        tema_key = tema.lower().strip()
        if not tema_key:
            continue
            
        entry = {
            "libro": book_title,
            "seccion": title,
            "pagina": page
        }
        
        if tema_key not in topics_dict:
            topics_dict[tema_key] = []
        
        # Evitar duplicados exactos en la misma sección/página
        if entry not in topics_dict[tema_key]:
            topics_dict[tema_key].append(entry)
            
    # Procesar subsecciones
    for sub in node.get("subsections", []):
        extract_topics_recursive(sub, book_title, topics_dict)

def build_pillar_brains():
    """Genera un índice invertido (Cerebro) por cada pilar logístico."""
    pillars = [
        "1. Supply Chain Strategist",
        "2. Warehouse Operations Expert",
        "3. Inventory & Planning Expert",
        "4. Transport & Distribution Expert"
    ]
    
    print("="*50)
    print("CONSTRUYENDO CEREBROS DE CARPETA (ÍNDICE INVERTIDO)")
    print("="*50 + "\n")
    
    for pillar in pillars:
        if not os.path.exists(pillar):
            print(f"[!] Advertencia: No existe la carpeta {pillar}")
            continue
            
        print(f">>> Procesando Pilar: {pillar}")
        pillar_brain = {}
        json_files = [f for f in os.listdir(pillar) if f.endswith(".json") and not f.startswith("Cerebro_")]
        
        for j_file in json_files:
            file_path = os.path.join(pillar, j_file)
            book_title = j_file.replace(".json", "")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Procesar cada nodo raíz del libro
                for root_node in data:
                    extract_topics_recursive(root_node, book_title, pillar_brain)
                    
            except Exception as e:
                print(f"    [Error] No se pudo leer {j_file}: {str(e)}")
        
        # Guardar el Cerebro del Pilar
        # Limpiamos el nombre del pilar para el archivo (ej: "1. Supply Chain Strategist" -> "Supply_Chain_Strategist")
        clean_name = pillar.split(". ", 1)[-1].replace(" ", "_")
        output_name = f"Cerebro_{clean_name}.json"
        output_path = os.path.join(pillar, output_name)
        
        # Ordenar el diccionario por orden alfabético de temas
        sorted_brain = dict(sorted(pillar_brain.items()))
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_brain, f, indent=4, ensure_ascii=False)
            
        print(f"    [Éxito] Generado: {output_name} ({len(sorted_brain)} temas únicos)")
        
    print(f"\n" + "="*50)
    print("CONSOLIDACIÓN FINALIZADA")
    print("="*50)

if __name__ == "__main__":
    build_pillar_brains()
