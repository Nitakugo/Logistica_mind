#!/usr/bin/env python3
"""
Logistic Mind - Local Search v2
Busca en los 4 Cerebros locales con scoring mejorado.
Acepta keywords separados por comas.
Devuelve JSON estructurado para consumo por Claude.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CEREBRO_FILES = {
    "Supply Chain Strategist": "Cerebro_Supply_Chain_Strategist.json",
    "Warehouse Operations Expert": "Cerebro_Warehouse_Operations_Expert.json",
    "Inventory & Planning Expert": "Cerebro_Inventory_&_Planning_Expert.json",
    "Transport & Distribution Expert": "Cerebro_Transport_&_Distribution_Expert.json"
}

# Nombres limpios de libros (sin tags de z-library)
LIBRO_CLEAN_NAMES = {
    "Administración y logística en la cadena de suministros": "Administración y logística en la cadena de suministros",
    "Logistics  Supply Chain Management": "Logistics & Supply Chain Management (Christopher)",
    "Strategic Supply Chain Management": "Strategic Supply Chain Management (Cohen, Roussel)",
    "Supply Chain Management Strategy, Planning, and Operation": "Supply Chain Management (Chopra, Meindl)",
    "The Resilient Enterprise": "The Resilient Enterprise (Sheffi)",
    "Cadena de suministros y logística": "Cadena de suministros y logística (Carreño Solís)",
    "Warehouse  Distribution Science": "Warehouse & Distribution Science (Bartholdi et al.)",
    "Basics of Inventory Management": "Basics of Inventory Management (Viale, Carrigan)",
    "Demand Driven Material Requirements Planning": "DDMRP v3 (Ptak, Smith)",
    "Inventory and Production Management": "Inventory and Production Management (Silver, Pyke et al.)",
    "Lean Thinking": "Lean Thinking (Jones, Womack)",
    "Logística Administración de la Cadena de Suministro": "Logística: Adm. Cadena de Suministro (Ballou)",
    "Transportation - a global supply chain perspective": "Transportation (Coyle, Gibson et al.)",
    "Transportation：A Global Supply Chain Perspective": "Transportation (Novack, Gibson, Suzuki et al.)"
}


def clean_libro_name(raw_name):
    """Limpia el nombre del libro quitando tags de z-library."""
    for key, clean in LIBRO_CLEAN_NAMES.items():
        if key.lower() in raw_name.lower():
            return clean
    # Fallback: quitar el tag de z-library
    if "(z-library" in raw_name:
        return raw_name.split("(z-library")[0].strip()
    return raw_name


def load_cerebro(filename):
    """Carga un Cerebro desde archivo local."""
    try:
        script_dir = Path(__file__).parent
        filepath = script_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}


def search_keywords(keywords, cerebro):
    """Busca keywords en un Cerebro con scoring mejorado."""
    matches = []
    keywords_lower = [k.lower().strip() for k in keywords if k.strip()]

    for cerebro_key, references in cerebro.items():
        key_lower = cerebro_key.lower()
        matched_keywords = []
        score = 0

        for kw in keywords_lower:
            # Match exacto (keyword del usuario == key del cerebro)
            if kw == key_lower:
                score += 5
                matched_keywords.append(kw)
            # Key del cerebro contiene el keyword del usuario
            elif kw in key_lower:
                score += 3
                matched_keywords.append(kw)
            # Keyword del usuario contiene la key del cerebro (key corta dentro de frase)
            elif key_lower in kw and len(key_lower) > 3:
                score += 2
                matched_keywords.append(kw)

        if score > 0:
            for ref in references:
                matches.append({
                    "cerebro_key": cerebro_key,
                    "matched_keywords": matched_keywords,
                    "libro": ref.get("libro", ""),
                    "seccion": ref.get("seccion", ""),
                    "pagina": ref.get("pagina", ""),
                    "contexto": ref.get("contexto", ""),
                    "score": score
                })

    return matches


def is_generic_section(seccion):
    """Filtra secciones genéricas que no aportan valor (TOC, prefacios, etc.)."""
    generic = [
        "contenido", "contents", "prefacio", "preface", "parte ", "part ",
        "índice", "index", "apéndice", "appendix", "bibliograf", "bibliography",
        "about the author", "agradecimiento", "acknowledgment", "brief contents",
        "suggested readings", "epílogo"
    ]
    sec_lower = seccion.lower().strip()
    # Secciones muy cortas (ej: "1.1", "PART I", "12.2")
    if len(sec_lower) < 5:
        return True
    for g in generic:
        if sec_lower.startswith(g):
            return True
    return False


def deduplicate_refs(matches):
    """Elimina duplicados por libro+seccion+pagina, quedándose con el mejor score."""
    seen = {}
    for m in matches:
        key = (m["libro"], m["seccion"], m["pagina"])
        if key not in seen or m["score"] > seen[key]["score"]:
            seen[key] = m
    return list(seen.values())


def search_cerebros(keywords_str):
    """Búsqueda principal. Recibe keywords separados por comas."""
    # Parsear keywords
    if "," in keywords_str:
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    else:
        keywords = [k.strip() for k in keywords_str.split() if len(k.strip()) > 3]

    all_matches = []
    cerebros_consultados = 0
    cerebros_con_resultados = 0

    for category, filename in CEREBRO_FILES.items():
        cerebro = load_cerebro(filename)
        if not cerebro:
            continue

        cerebros_consultados += 1
        matches = search_keywords(keywords, cerebro)

        if matches:
            cerebros_con_resultados += 1

        for match in matches:
            match["categoria"] = category
        all_matches.extend(matches)

    # Deduplicar
    all_matches = deduplicate_refs(all_matches)

    # Agrupar por libro y calcular score total
    by_libro = defaultdict(lambda: {"refs": [], "total_score": 0, "categoria": "", "keywords_matched": set()})

    for match in all_matches:
        libro = match["libro"]
        by_libro[libro]["refs"].append({
            "seccion": match["seccion"],
            "pagina": match["pagina"],
            "contexto": match.get("contexto", ""),
            "score": match["score"],
            "cerebro_key": match["cerebro_key"]
        })
        by_libro[libro]["total_score"] += match["score"]
        by_libro[libro]["categoria"] = match["categoria"]
        for kw in match["matched_keywords"]:
            by_libro[libro]["keywords_matched"].add(kw)

    # Ordenar por score total
    sorted_libros = sorted(by_libro.items(), key=lambda x: x[1]["total_score"], reverse=True)

    # Construir resultado
    resultados = []
    for libro_raw, data in sorted_libros[:8]:
        # Filtrar secciones genéricas, luego ordenar por score descendente
        specific_refs = [r for r in data["refs"] if not is_generic_section(r["seccion"])]
        # Si no quedan refs específicas, usar todas
        if not specific_refs:
            specific_refs = data["refs"]
        sorted_refs = sorted(specific_refs, key=lambda r: (-r["score"], r["pagina"]))
        # Top 5 refs por libro
        top_refs = sorted_refs[:5]

        resultados.append({
            "libro": clean_libro_name(libro_raw),
            "libro_original": libro_raw,
            "categoria": data["categoria"],
            "score_total": data["total_score"],
            "keywords_matched": list(data["keywords_matched"]),
            "referencias": [
                {
                    "seccion": r["seccion"],
                    "pagina": r["pagina"],
                    "contexto": r.get("contexto", ""),
                    "score": r["score"]
                }
                for r in top_refs
            ]
        })

    output = {
        "keywords_buscados": keywords,
        "cerebros_consultados": cerebros_consultados,
        "cerebros_con_resultados": cerebros_con_resultados,
        "total_matches": len(all_matches),
        "resultados": resultados
    }

    return output


if __name__ == "__main__":
    if len(sys.argv) > 1:
        keywords_input = " ".join(sys.argv[1:])
    else:
        keywords_input = "quiebre,stock,inventario,demanda"

    result = search_cerebros(keywords_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))
