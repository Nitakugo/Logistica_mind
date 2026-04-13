# Logistic Mind — Monitoring & Optimization

## KPIs en Producción

### Búsqueda Semántica

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Keywords indexados | 1,863 | ≥1,800 | ✓ 1,863 |
| Referencias totales | 17,153 | ≥15,000 | ✓ 17,153 |
| Embeddings dimensión | 384 | - | ✓ 384-dim |
| Similitud threshold | 0.45 | 0.40-0.50 | ✓ 0.45 |
| Top-K por query | 10 | 8-12 | ✓ 10 |
| Embeddings size | 2.7 MB | <5 MB | ✓ 2.7 MB |

### Respuesta del Sistema

| Métrica | Medición | Meta |
|---------|----------|------|
| Queries procesadas/día | Monitorear | >100 |
| Tiempo medio búsqueda | ~2-3 seg | <5 seg |
| Matches encontrados/query | 3-8 libros | ≥3 |
| Referencia exactitud | 100% | 100% |
| Formato respuesta | 5-secciones | Consistente |

---

## Health Checks Mensuales

### 1. Validar Integridad de Datos

```bash
# Verificar que todos los Cerebros son JSON válidos
for f in Cerebro_*.json; do
  python -c "import json; json.load(open('$f'))" && echo "[OK] $f" || echo "[ERROR] $f"
done

# Verificar conteo de keywords
python -c "
import json
for f in ['Cerebro_Supply_Chain_Strategist.json', ...]:
  with open(f) as fh:
    data = json.load(fh)
    total_refs = sum(len(v) for v in data.values())
    print(f'{f}: {len(data)} keywords, {total_refs} refs')
"
```

### 2. Validar Embeddings

```bash
# Verificar que embeddings_index.npy existe y es accesible
python -c "
import numpy as np
embeddings = np.load('embeddings_index.npy')
print(f'Shape: {embeddings.shape}')
print(f'Size: {embeddings.nbytes / 1024 / 1024:.1f} MB')
print(f'Data type: {embeddings.dtype}')
"
```

### 3. Test de Búsqueda Manual

```bash
# Ejecutar una búsqueda de prueba
python search_semantic.py "lead time,safety stock,buffer"

# Verificar que:
# - JSON output válido
# - Al menos 3 libros en resultados
# - Cada referencia tiene: libro, seccion, pagina, contexto
# - Similitud >= 0.45
```

### 4. Validar Sincronización

```bash
# Verificar que skill/ tiene los mismos Cerebros que proyecto/
# Si NO coinciden, ejecutar:
bash sync_cerebros_to_skill.sh
git add Cerebro_*.json
git commit -m "sync: monthly Cerebro validation"
git push
```

---

## Métricas de Calidad de Búsqueda

### Por Tipo de Query

**Operacionales** (palabras exactas del usuario):
- Esperado: 90%+ match rate
- Ejemplo: "quiebre stock", "lead time", "picking"

**Técnicos** (sinónimos y variantes):
- Esperado: 70%+ match rate
- Ejemplo: "demanda variable" → "volatility", "variability", "forecast error"

**Lenguaje Natural** (frases completas):
- Esperado: 60%+ match rate
- Ejemplo: "cómo optimizo el picking en mi almacén"

---

## Troubleshooting

### Problema: 0 matches encontrados

**Causas posibles**:
1. Threshold muy alto (>0.60) — bajá a 0.45
2. Keyword no está indexado — verificá en Cerebro directamente
3. Embeddings desactualizados — ejecutá `build_embeddings.py`

**Solución**:
```bash
python search_cerebros_local.py "tu_keyword"  # Test fallback
python search_semantic.py "tu_keyword"  # Test semántico
```

### Problema: Matches irrelevantes

**Causas posibles**:
1. Threshold muy bajo (<0.35)
2. Query ambigua o con stopwords
3. Keyword genérico en multiple Cerebros

**Solución**:
```bash
# Aumentá threshold en search_semantic.py
SIMILARITY_THRESHOLD = 0.50  # Era 0.45

# O usa búsqueda local con scoring mejorado
python search_cerebros_local.py "keyword exacto"
```

### Problema: Embeddings corrupto

**Síntomas**: Error al cargar embeddings_index.npy

**Solución**:
```bash
# Regenerar índices
cd skill_folder/
python build_embeddings.py

# Validar
ls -lh embeddings_*.* 
# Debe haber 2 archivos: .npy y .json
```

---

## Optimizaciones Futuras

### 1. Fine-tuning de Threshold
Monitorear queries en producción y ajustar threshold según:
- % de queries con 0 matches → bajá threshold
- % de queries con resultados irrelevantes → subí threshold
- Meta: >90% de queries devuelven 3+ resultados relevantes

### 2. Expansión de Keywords
Cada 3 meses, revisar:
- Nuevos temas en problemas de usuarios
- Keywords que no tienen suficientes matches (<2 libros)
- Proponer agregar keywords a los Cerebros

### 3. Monitoreo de Relevancia
Implementar feedback loop:
- Usuario indica: "Esta respuesta fue útil" / "No fue útil"
- Registrar qué query → qué libros → qué feedback
- Usar para refinar similarity threshold y TOP_K

### 4. Actualización de Modelos
Evaluar cada 6 meses:
- ¿paraphrase-multilingual-MiniLM-L12-v2 sigue siendo óptimo?
- ¿Hay modelos más nuevos que entiendan mejor contexto logístico?
- Benchmark de dimensionalidad vs calidad

---

## Comandos Útiles

```bash
# Ver stats de Cerebros
for f in Cerebro_*.json; do
  echo -n "$f: "
  python -c "import json; d=json.load(open('$f')); print(f'{len(d)} keys, {sum(len(v) for v in d.values())} refs')"
done

# Buscar un keyword específico
grep -r "safety stock" Cerebro_*.json | wc -l

# Validar JSON integrity
python -c "
import json, glob
for f in glob.glob('Cerebro_*.json'):
  json.load(open(f))
  print(f'[OK] {f}')
"

# Tamaño total del sistema
du -sh embeddings_* Cerebro_*.json

# Sincronizar y commitear cambios
bash sync_cerebros_to_skill.sh
git add -A && git commit -m "chore: monthly sync and validation"
git push
```

---

## Status Badge

```
Logistic Mind v1.0.0
- Keywords: 1,863 ✓
- Embeddings: 2.7 MB ✓
- Cerebros: 4/4 ✓
- Tests: 16/16 ✓
- Status: PRODUCTION-READY
```
