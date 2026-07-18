import requests, warnings, time
warnings.filterwarnings("ignore")

BASE = "http://localhost:8000/api/predict"
tests = [
    ("auto",          1,  1,  7),
    ("xgboost",       1,  1, 30),
    ("lightgbm",      2,  5, 14),
    ("random_forest", 3, 10, 30),
    ("lstm",          1,  1, 30),
]

for model, store, item, horizon in tests:
    t = time.time()
    r = requests.post(BASE, json={"store": store, "item": item, "horizon": horizon, "model": model}, timeout=300)
    elapsed = round(time.time() - t, 1)
    if r.status_code == 200:
        d = r.json()
        used = d["model_used"]
        preds = d["predicted_sales"][:3]
        print(f"[OK]  requested={model:14s}  used={used:14s}  s={store} i={item} h={horizon}d  preds={preds}  ({elapsed}s)")
    else:
        print(f"[ERR] model={model} s={store} i={item}: {r.json()}")
