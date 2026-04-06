import fitz  # PyMuPDF
import os
import sys

def search_logistics(term):
    pillars = [
        "1. Supply Chain Strategist",
        "2. Warehouse Operations Expert",
        "3. Inventory & Planning Expert",
        "4. Transport & Distribution Expert"
    ]
    
    results = []
    
    for pillar in pillars:
        pillar_path = os.path.join(".", pillar)
        if not os.path.exists(pillar_path):
            continue
            
        for file in os.listdir(pillar_path):
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(pillar_path, file)
                print(f"Buscando en: {file}...")
                
                try:
                    doc = fitz.open(pdf_path)
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        # Usamos bloques de texto para obtener párrafos completos
                        blocks = page.get_text("blocks")
                        for block in blocks:
                            text = block[4]
                            if term.lower() in text.lower():
                                results.append({
                                    "pillar": pillar,
                                    "book": file,
                                    "page": page_num + 1,
                                    "paragraph": text.strip()
                                })
                    doc.close()
                except Exception as e:
                    print(f"Error procesando {file}: {e}")

    return results

def save_results(results, term, output_file="search_results.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"RESULTADOS DE BÚSQUEDA PARA: '{term}'\n")
        f.write("="*50 + "\n\n")
        
        if not results:
            f.write("No se encontraron coincidencias.\n")
            return

        current_pillar = ""
        current_book = ""
        
        for res in results:
            if res["pillar"] != current_pillar:
                current_pillar = res["pillar"]
                f.write(f"\n### PILLAR: {current_pillar} ###\n")
                f.write("-" * 30 + "\n")
                
            if res["book"] != current_book:
                current_book = res["book"]
                f.write(f"\nLibro: {current_book}\n")
                
            f.write(f"\n[Página {res['page']}]\n")
            f.write(f"{res['paragraph']}\n")
            f.write("-" * 10 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
    else:
        search_term = input("Ingrese el término logístico a buscar: ")
        
    print(f"Iniciando búsqueda de '{search_term}'...")
    matches = search_logistics(search_term)
    save_results(matches, search_term)
    print(f"\nBúsqueda completada. se encontraron {len(matches)} coincidencias.")
    print(f"Resultados guardados en 'search_results.txt'.")
