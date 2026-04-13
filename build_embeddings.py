#!/usr/bin/env python3
"""
Logistic Mind - Build Embeddings Index
Genera embeddings para todas las keys de los 4 Cerebros.
Se ejecuta UNA SOLA VEZ (o cuando se regeneran los Cerebros).

Modelo: paraphrase-multilingual-MiniLM-L12-v2
  - Soporta español e inglés
  - Ligero (~400MB)
  - 384 dimensiones por embedding
"""

import json
import sys
import numpy as np
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CEREBRO_FILES = {
    "Supply Chain Strategist": "Cerebro_Supply_Chain_Strategist.json",
    "Warehouse Operations Expert": "Cerebro_Warehouse_Operations_Expert.json",
    "Inventory & Planning Expert": "Cerebro_Inventory_&_Planning_Expert.json",
    "Transport & Distribution Expert": "Cerebro_Transport_&_Distribution_Expert.json"
}

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    script_dir = Path(__file__).parent

    print("[1/3] Cargando keys de los 4 Cerebros...")

    all_keys = []       # Lista de strings (las keys)
    key_metadata = []   # Metadata: qué cerebro y cuántas refs tiene cada key

    for category, filename in CEREBRO_FILES.items():
        filepath = script_dir / filename
        if not filepath.exists():
            print(f"  [SKIP] {filename} no encontrado")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            cerebro = json.load(f)

        for key, refs in cerebro.items():
            all_keys.append(key)
            key_metadata.append({
                "key": key,
                "categoria": category,
                "num_refs": len(refs)
            })

        print(f"  [OK] {category}: {len(cerebro)} keys")

    print(f"\n  Total: {len(all_keys)} keys únicas a indexar")

    print(f"\n[2/3] Generando embeddings con {MODEL_NAME}...")
    print("  (Primera vez descarga el modelo ~400MB, luego se cachea)")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(all_keys, show_progress_bar=True, batch_size=64)
    embeddings_np = np.array(embeddings, dtype=np.float32)

    print(f"  [OK] Shape: {embeddings_np.shape}")

    print("\n[3/3] Guardando índice...")

    # Guardar embeddings como numpy
    embeddings_path = script_dir / "embeddings_index.npy"
    np.save(embeddings_path, embeddings_np)
    print(f"  [OK] {embeddings_path.name} ({embeddings_np.nbytes / 1024 / 1024:.1f} MB)")

    # Guardar metadata como JSON
    metadata_path = script_dir / "embeddings_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(key_metadata, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {metadata_path.name} ({len(key_metadata)} entries)")

    print("\n[DONE] Índice de embeddings generado exitosamente.")
    print(f"  Keys indexadas: {len(all_keys)}")
    print(f"  Dimensiones: {embeddings_np.shape[1]}")
    print(f"  Modelo: {MODEL_NAME}")


if __name__ == "__main__":
    main()
