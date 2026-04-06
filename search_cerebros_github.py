#!/usr/bin/env python3
"""
Logistic Mind - Search Cerebros from GitHub
Busca en los 4 Cerebros alojados en GitHub
"""

import json
import urllib.request
import urllib.error
from collections import defaultdict

# URLs de los Cerebros en GitHub (raw content)
GITHUB_URLS = {
    "Supply Chain": "https://raw.githubusercontent.com/Nitakugo/Logistica_mind/main/1.%20Supply%20Chain%20Strategist/Cerebro_Supply_Chain_Strategist.json",
    "Warehouse": "https://raw.githubusercontent.com/Nitakugo/Logistica_mind/main/2.%20Warehouse%20Operations%20Expert/Cerebro_Warehouse_Operations_Expert.json",
    "Inventory": "https://raw.githubusercontent.com/Nitakugo/Logistica_mind/main/3.%20Inventory%20%26%20Planning%20Expert/Cerebro_Inventory_%26_Planning_Expert.json",
    "Transport": "https://raw.githubusercontent.com/Nitakugo/Logistica_mind/main/4.%20Transport%20%26%20Distribution%20Expert/Cerebro_Transport_%26_Distribution_Expert.json"
}

# URLs base para PDFs en GitHub
PDF_URLS_BASE = {
    "Supply Chain": "https://github.com/Nitakugo/Logistica_mind/blob/main/1.%20Supply%20Chain%20Strategist/",
    "Warehouse": "https://github.com/Nitakugo/Logistica_mind/blob/main/2.%20Warehouse%20Operations%20Expert/",
    "Inventory": "https://github.com/Nitakugo/Logistica_mind/blob/main/3.%20Inventory%20%26%20Planning%20Expert/",
    "Transport": "https://github.com/Nitakugo/Logistica_mind/blob/main/4.%20Transport%20%26%20Distribution%20Expert/"
}

def fetch_cerebro(url):
    """Descarga un Cerebro desde GitHub"""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return {}

def search_keywords(keywords, cerebro):
    """Busca keywords en un Cerebro y retorna matches"""
    matches = []
    keywords_lower = [k.lower() for k in keywords]

    for keyword_original, references in cerebro.items():
        keyword_lower = keyword_original.lower()
        score = 0

        # Match exacto
        if keyword_lower in keywords_lower:
            score += 3
        # Match parcial
        else:
            for kw in keywords_lower:
                if kw in keyword_lower or keyword_lower in kw:
                    score += 1

        if score > 0:
            for ref in references:
                matches.append({
                    "keyword": keyword_original,
                    "libro": ref.get("libro", ""),
                    "seccion": ref.get("seccion", ""),
                    "pagina": ref.get("pagina", ""),
                    "score": score
                })

    return matches

def extract_pdf_name(libro_name):
    """Extrae el nombre del PDF del nombre del libro"""
    # Intenta encontrar un PDF que coincida
    return f"{libro_name}.pdf"

def format_results(all_matches):
    """Formatea los resultados para presentación"""
    if not all_matches:
        return "No se encontraron referencias relevantes."

    # Agrupa por libro y calcula score total
    by_libro = defaultdict(lambda: {"refs": [], "total_score": 0, "category": ""})

    for match in all_matches:
        libro = match["libro"]
        by_libro[libro]["refs"].append(match)
        by_libro[libro]["total_score"] += match["score"]
        by_libro[libro]["category"] = match.get("category", "")

    # Ordena por score
    sorted_libros = sorted(by_libro.items(), key=lambda x: x[1]["total_score"], reverse=True)

    result = []
    for rank, (libro, data) in enumerate(sorted_libros[:5], 1):
        medals = ["[1]", "[2]", "[3]", "[4]", "[5]"]
        medal = medals[rank-1] if rank <= len(medals) else "[*]"

        ref = data["refs"][0]
        result.append(f"{medal} {libro}")
        result.append(f"   Seccion: {ref['seccion']}")
        result.append(f"   Pagina: {ref['pagina']}")
        result.append(f"   Relevancia: {data['total_score']} puntos")
        result.append("")

    return "\n".join(result)

def search_cerebros(problem_description):
    """Búsqueda principal"""
    print("\n[*] Buscando en tus Cerebros Logísticos...")
    print(f"[PROBLEMA] {problem_description}\n")

    # Extrae keywords
    keywords = problem_description.lower().split()
    keywords = [k.strip('.,!?;:') for k in keywords if len(k) > 3]

    print(f"Keywords extraídos: {', '.join(keywords)}\n")

    all_matches = []

    # Busca en cada Cerebro
    for category, url in GITHUB_URLS.items():
        print(f"[BUSCANDO] {category}...")
        cerebro = fetch_cerebro(url)

        if cerebro:
            matches = search_keywords(keywords, cerebro)
            for match in matches:
                match["category"] = category
            all_matches.extend(matches)
            print(f"   [OK] {len(matches)} referencias encontradas")
        else:
            print(f"   [ERROR] No se pudo acceder")

    print("\n" + "="*60)
    print("RESULTADOS")
    print("="*60 + "\n")

    print(format_results(all_matches))

    return all_matches

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    else:
        problem = "Tengo quiebre de stock en múltiples depósitos"

    search_cerebros(problem)
