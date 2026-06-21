import json, sys

nb_file = sys.argv[1]
keywords = ['sdc_model', 'predict', 'recommend', 'joblib', 'pickle', 'artifacts', 'save', 'dump']

with open(nb_file, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = [c for c in nb['cells'] if c['cell_type'] == 'code']

for i, c in enumerate(cells):
    src = ''.join(c['source'])
    if any(kw in src.lower() for kw in keywords):
        safe = src[:2000].encode('ascii', 'replace').decode('ascii')
        print(f"=== Cell {i} ===")
        print(safe)
        print()
