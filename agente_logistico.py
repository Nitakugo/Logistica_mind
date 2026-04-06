import json
import os
import sys

def load_brains():
    """Carga los 4 cerebros de los pilares en un diccionario unificado."""
    pillars = {
        "1. Supply Chain Strategist": "Cerebro_Supply_Chain_Strategist.json",
        "2. Warehouse Operations Expert": "Cerebro_Warehouse_Operations_Expert.json",
        "3. Inventory & Planning Expert": "Cerebro_Inventory_&_Planning_Expert.json",
        "4. Transport & Distribution Expert": "Cerebro_Transport_&_Distribution_Expert.json"
    }
    
    loaded_brains = {}
    for p_name, b_file in pillars.items():
        path = os.path.join(p_name, b_file)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                loaded_brains[p_name] = json.load(f)
        else:
            print(f"[!] Advertencia: No se encontró {path}")
            loaded_brains[p_name] = {}
            
    return loaded_brains

def search_term(query, brains):
    """Busca el término en todos los cerebros (coincidencia parcial)."""
    query = query.lower().strip()
    results = {} # {Pilar: {Libro: [{"seccion": ..., "pagina": ...}]}}
    
    for pillar, index in brains.items():
        pillar_matches = {}
        
        for topic, occurrences in index.items():
            if query in topic: # Coincidencia parcial
                for occ in occurrences:
                    libro = occ["libro"]
                    if libro not in pillar_matches:
                        pillar_matches[libro] = []
                    
                    # Evitar duplicados de sección en el mismo libro
                    entry = {"seccion": occ["seccion"], "pagina": occ["pagina"]}
                    if entry not in pillar_matches[libro]:
                        pillar_matches[libro].append(entry)
        
        if pillar_matches:
            results[pillar] = pillar_matches
            
    return results

def print_executive_report(query, results):
    """Imprime los resultados con formato de Reporte Ejecutivo."""
    # Intentar forzar UTF-8 en la salida de terminal para evitar errores en Windows
    try:
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

    print("\n" + "="*80)
    print(f" REPORTE EJECUTIVO : MATRIZ LOGISTICA")
    print(f" TERMINO BUSCADO: '{query.upper()}'")
    print("="*80 + "\n")
    
    if not results:
        print(f" >>> No se encontraron hallazgos para '{query}' en la matriz de conocimiento.")
        print("\n" + "="*80)
        return

    for pillar, libros in results.items():
        print(f" [PILLAR LOGISTICO]: {pillar.upper()}")
        print("-" * len(f" [PILLAR LOGISTICO]: {pillar.upper()}"))
        
        for libro, hallazgos in libros.items():
            print(f"   - LIBRO: {libro}")
            # Ordenar hallazgos por página
            for h in sorted(hallazgos, key=lambda x: x["pagina"]):
                print(f"     > [Pag {h['pagina']:03d}] {h['seccion']}")
            print()
    
    print("="*80)
    print(f" FIN DEL REPORTE UNIFICADO")
    print("="*80 + "\n")

def main():
    if len(sys.argv) < 2:
        print("\nUso: python agente_logistico.py \"térimo a buscar\"")
        print("Ejemplo: python agente_logistico.py \"lead time\"\n")
        return

    query = sys.argv[1]
    
    # 1. Cargar datos
    brains = load_brains()
    
    # 2. Buscar
    results = search_term(query, brains)
    
    # 3. Presentar reporte
    print_executive_report(query, results)

if __name__ == "__main__":
    main()
