import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data.config import CANDIDATE_KEYS
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

results =[]

for filename, key_col in CANDIDATE_KEYS.items():
    file_path = RAW_DATA_DIR / filename

    df = pd.read_csv(file_path, low_memory=False)

    # Identificamos valores nulos y duplicados
    null_keys = df[key_col].isna().any(axis=1).sum()
    duplicate_keys = df.duplicated(
        subset=key_col
    ).sum()

    status = (
        "OK" if null_keys == 0 and duplicate_keys == 0
        else "REVISAR"
    )

    results.append(
        {
            "archivo": filename,
            "clave": " + ".join(key_col),
            "claves_nulas": int(null_keys),
            "claves_duplicadas": int(duplicate_keys),
            "estado": status,
        }
    )

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))