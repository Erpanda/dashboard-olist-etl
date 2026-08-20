import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Identificamos los atributos PK/FK
candidate_keys = {
    "olist_customers_dataset.csv": ["customer_id"],
    "olist_orders_dataset.csv": ["order_id", "customer_id"],
    "olist_order_items_dataset.csv": ["order_id", "order_item_id", "product_id", "seller_id"],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
    "olist_order_payments_dataset.csv": [
        "order_id",
        "payment_sequential",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id",
        "order_id",
    ],
    "product_category_name_translation.csv": [
        "product_category_name"
    ],
}

results =[]

for filename, key_col in candidate_keys.items():
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