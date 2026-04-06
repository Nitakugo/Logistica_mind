import fitz
import os
from collections import Counter

def analyze_fonts(pdf_path, max_pages=20):
    """
    Analiza los tamaños y nombres de fuente para identificar el texto base 
    y potenciales encabezados.
    """
    doc = fitz.open(pdf_path)
    font_stats = Counter()
    
    # Muestrear algunas páginas para encontrar los estilos predominantes
    for i in range(min(max_pages, len(doc))):
        page = doc.load_page(i)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b["type"] == 0:  # de texto
                for line in b["lines"]:
                    for span in line["spans"]:
                        font_stats[(round(span["size"], 2), span["font"])] += 1
    
    doc.close()
    
    # Ordenar por frecuencia (el más frecuente suele ser el cuerpo del texto)
    most_common = font_stats.most_common(10)
    print(f"\nAnálisis de estilos para: {os.path.basename(pdf_path)}")
    print(f"{'Tamaño':<10} | {'Fuente':<30} | {'Frecuencia'}")
    print("-" * 55)
    for style, count in most_common:
        print(f"{style[0]:<10} | {style[1]:<30} | {count}")
    
    return most_common

if __name__ == "__main__":
    # Probar con un libro que no tenía TOC
    test_pdf = "1. Supply Chain Strategist/Logistics  Supply Chain Management (Martin Christopher) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
    if os.path.exists(test_pdf):
        analyze_fonts(test_pdf)
    else:
        print("El archivo de prueba no existe.")
