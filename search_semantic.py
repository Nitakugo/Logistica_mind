#!/usr/bin/env python3
"""
Logistic Mind - Semantic Search v3
Busca en los 4 Cerebros usando embeddings + cosine similarity.
"volatilidad" encuentra "variabilidad", "forecast error", "demand uncertainty".

Usa el índice pre-calculado (embeddings_index.npy + embeddings_metadata.json).
Si no existe, cae a keyword matching (v2).

Modelo: paraphrase-multilingual-MiniLM-L12-v2 (español + inglés)
"""

import json
import sys
import numpy as np
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent

CEREBRO_FILES = {
    "Supply Chain Strategist": "Cerebro_Supply_Chain_Strategist.json",
    "Warehouse Operations Expert": "Cerebro_Warehouse_Operations_Expert.json",
    "Inventory & Planning Expert": "Cerebro_Inventory_&_Planning_Expert.json",
    "Transport & Distribution Expert": "Cerebro_Transport_&_Distribution_Expert.json"
}

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

# Similarity threshold: keys below this are considered irrelevant
SIMILARITY_THRESHOLD = 0.45
# Maximum keys to retrieve per query term
TOP_K_PER_QUERY = 10


def clean_libro_name(raw_name):
    for key, clean in LIBRO_CLEAN_NAMES.items():
        if key.lower() in raw_name.lower():
            return clean
    if "(z-library" in raw_name:
        return raw_name.split("(z-library")[0].strip()
    return raw_name


def is_generic_section(seccion):
    generic = [
        "contenido", "contents", "prefacio", "preface", "parte ", "part ",
        "índice", "index", "apéndice", "appendix", "bibliograf", "bibliography",
        "about the author", "agradecimiento", "acknowledgment", "brief contents",
        "suggested readings", "epílogo"
    ]
    sec_lower = seccion.lower().strip()
    if len(sec_lower) < 5:
        return True
    for g in generic:
        if sec_lower.startswith(g):
            return True
    return False


def load_embeddings_index():
    """Carga el índice de embeddings pre-calculado."""
    embeddings_path = SCRIPT_DIR / "embeddings_index.npy"
    metadata_path = SCRIPT_DIR / "embeddings_metadata.json"

    if not embeddings_path.exists() or not metadata_path.exists():
        return None, None

    embeddings = np.load(embeddings_path)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    return embeddings, metadata


def load_model():
    """Carga el modelo de sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def semantic_search(query_terms, embeddings, metadata, model):
    """
    Busca por similitud semántica.
    Retorna las keys más similares a cada query term.
    """
    # Encode all query terms at once
    query_embeddings = model.encode(query_terms, show_progress_bar=False)

    # Normalize for cosine similarity
    emb_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    q_norm = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)

    # Cosine similarity matrix: (num_queries x num_keys)
    similarities = q_norm @ emb_norm.T

    # Collect top-k matches per query
    matched_keys = {}  # key -> {score, matched_queries}

    for i, query in enumerate(query_terms):
        scores = similarities[i]
        top_indices = np.argsort(scores)[::-1][:TOP_K_PER_QUERY]

        for idx in top_indices:
            score = float(scores[idx])
            if score < SIMILARITY_THRESHOLD:
                break

            key = metadata[idx]["key"]
            category = metadata[idx]["categoria"]

            if key not in matched_keys:
                matched_keys[key] = {
                    "score": 0,
                    "max_score": 0,
                    "matched_queries": [],
                    "categoria": category
                }

            matched_keys[key]["score"] += score
            matched_keys[key]["max_score"] = max(matched_keys[key]["max_score"], score)
            matched_keys[key]["matched_queries"].append({
                "query": query,
                "similarity": round(score, 3)
            })

    return matched_keys


def lookup_references(matched_keys, cerebros):
    """
    Dado un dict de keys matcheadas, busca las referencias en los Cerebros.
    """
    all_refs = []

    for key, info in matched_keys.items():
        for category, cerebro in cerebros.items():
            if key in cerebro:
                for ref in cerebro[key]:
                    all_refs.append({
                        "cerebro_key": key,
                        "libro": ref.get("libro", ""),
                        "seccion": ref.get("seccion", ""),
                        "pagina": ref.get("pagina", ""),
                        "contexto": ref.get("contexto", ""),
                        "score": info["score"],
                        "max_similarity": info["max_score"],
                        "matched_queries": info["matched_queries"],
                        "categoria": category
                    })

    return all_refs


def deduplicate_refs(matches):
    seen = {}
    for m in matches:
        key = (m["libro"], m["seccion"], m["pagina"])
        if key not in seen or m["score"] > seen[key]["score"]:
            seen[key] = m
    return list(seen.values())


def build_output(all_refs, query_terms):
    """Agrupa y formatea el output final."""
    all_refs = deduplicate_refs(all_refs)

    by_libro = defaultdict(lambda: {
        "refs": [], "total_score": 0, "categoria": "",
        "keywords_matched": set(), "max_similarity": 0
    })

    for ref in all_refs:
        libro = ref["libro"]
        by_libro[libro]["refs"].append({
            "seccion": ref["seccion"],
            "pagina": ref["pagina"],
            "contexto": ref.get("contexto", ""),
            "score": ref["score"],
            "similarity": ref["max_similarity"],
            "cerebro_key": ref["cerebro_key"]
        })
        by_libro[libro]["total_score"] += ref["score"]
        by_libro[libro]["max_similarity"] = max(
            by_libro[libro]["max_similarity"], ref["max_similarity"]
        )
        by_libro[libro]["categoria"] = ref["categoria"]
        for mq in ref["matched_queries"]:
            by_libro[libro]["keywords_matched"].add(mq["query"])

    sorted_libros = sorted(
        by_libro.items(),
        key=lambda x: x[1]["total_score"],
        reverse=True
    )

    resultados = []
    for libro_raw, data in sorted_libros[:8]:
        specific_refs = [r for r in data["refs"] if not is_generic_section(r["seccion"])]
        if not specific_refs:
            specific_refs = data["refs"]
        sorted_refs = sorted(specific_refs, key=lambda r: (-r["score"], r["pagina"]))
        top_refs = sorted_refs[:5]

        resultados.append({
            "libro": clean_libro_name(libro_raw),
            "libro_original": libro_raw,
            "categoria": data["categoria"],
            "score_total": round(data["total_score"], 2),
            "max_similarity": round(data["max_similarity"], 3),
            "keywords_matched": list(data["keywords_matched"]),
            "referencias": [
                {
                    "seccion": r["seccion"],
                    "pagina": r["pagina"],
                    "contexto": r.get("contexto", ""),
                    "similarity": round(r["similarity"], 3)
                }
                for r in top_refs
            ]
        })

    return {
        "modo": "semantic",
        "modelo": "paraphrase-multilingual-MiniLM-L12-v2",
        "keywords_buscados": query_terms,
        "threshold": SIMILARITY_THRESHOLD,
        "cerebros_consultados": 4,
        "total_matches": len(all_refs),
        "resultados": resultados
    }


def main():
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    else:
        raw_input = "tengo demanda variable y quiebre de stock"

    # Parse: comma-separated or natural language
    if "," in raw_input:
        query_terms = [t.strip() for t in raw_input.split(",") if t.strip()]
    else:
        # Natural language: use the whole phrase as primary query
        query_terms = [raw_input]
        # Add meaningful bigrams (pairs of consecutive words) as secondary queries
        stopwords = {
            "el", "la", "los", "las", "un", "una", "de", "del", "en", "con",
            "por", "para", "como", "cómo", "qué", "que", "mi", "mis", "su",
            "sus", "al", "y", "o", "a", "es", "son", "se", "no", "si", "más",
            "muy", "the", "a", "an", "in", "on", "for", "to", "of", "and",
            "is", "my", "how", "what", "this", "that"
        }
        words = [w for w in raw_input.lower().split() if w not in stopwords and len(w) > 2]
        if len(words) >= 2:
            for i in range(len(words) - 1):
                query_terms.append(f"{words[i]} {words[i+1]}")

    # Load embeddings
    embeddings, metadata = load_embeddings_index()
    if embeddings is None:
        print(json.dumps({
            "error": "Índice de embeddings no encontrado. Ejecutá build_embeddings.py primero.",
            "modo": "error"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    # Load model
    model = load_model()

    # Semantic search
    matched_keys = semantic_search(query_terms, embeddings, metadata, model)

    # Load cerebros for reference lookup
    cerebros = {}
    for category, filename in CEREBRO_FILES.items():
        filepath = SCRIPT_DIR / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                cerebros[category] = json.load(f)

    # Lookup references
    all_refs = lookup_references(matched_keys, cerebros)

    # Build output
    output = build_output(all_refs, query_terms)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
