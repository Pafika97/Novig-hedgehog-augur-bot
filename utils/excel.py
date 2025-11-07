
import os
import pandas as pd
from datetime import datetime

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def to_excel(df, platform: str) -> str:
    ensure_dir("exports")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("exports", f"{platform}_markets_{ts}.xlsx")
    if df is None or df.empty:
        # создадим пустую таблицу с одним столбцом-комментарием
        df = pd.DataFrame([{"note": "no data returned"}])
    df.to_excel(path, index=False)
    return path
