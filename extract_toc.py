import fitz  # PyMuPDF
import os
import json

def get_nested_toc(toc_list):
    """
    Convierte una lista plana de TOC [[lvl, title, page], ...] 
    en una estructura anidada de diccionarios.
    """
    root = []
    stack = [(0, root)]
    
    for entry in toc_list:
        lvl, title, page = entry[0], entry[1], entry[2]
        node = {
            "title": title, 
            "page": page, 
            "subsections": []
        }
        
        # Retroceder en el stack hasta encontrar el padre correcto
        while lvl <= stack[-1][0]:
            stack.pop()
            
        # Añadir al nivel actual
        stack[-1][1].append(node)
        # Bajar un nivel
        stack.append((lvl, node["subsections"]))
        
    return root

def process_pdfs():
    pillars = [
        "1. Supply Chain Strategist",
        "2. Warehouse Operations Expert",
        "3. Inventory & Planning Expert",
        "4. Transport & Distribution Expert"
    ]
    
    found_count = 0
    processed_count = 0
    
    for pillar in pillars:
        pillar_path = os.path.join(".", pillar)
        if not os.path.exists(pillar_path):
            continue
            
        for file in os.listdir(pillar_path):
            if file.lower().endswith(".pdf"):
                found_count += 1
                pdf_path = os.path.join(pillar_path, file)
                json_path = os.path.join(pillar_path, os.path.splitext(file)[0] + ".json")
                
                print(f"Procesando TOC de: {file}...")
                
                try:
                    doc = fitz.open(pdf_path)
                    toc = doc.get_toc()
                    
                    if toc:
                        nested_toc = get_nested_toc(toc)
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(nested_toc, f, indent=4, ensure_ascii=False)
                        processed_count += 1
                    else:
                        print(f"  Advertencia: No se encontró TOC en {file}")
                        # Crear un JSON vacío o con info básica si se prefiere
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump({"error": "No TOC found"}, f)
                    
                    doc.close()
                except Exception as e:
                    print(f"  Error procesando {file}: {e}")

    print(f"\nResumen: Se encontraron {found_count} PDFs, se generaron {processed_count} archivos JSON con TOC.")

if __name__ == "__main__":
    process_pdfs()
