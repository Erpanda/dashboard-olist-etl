from pathlib import Path
import pandas as pd

# Convertimos cada csv en un dataframe para almacenarlo en un dataset respectivo
FILES_CONFIG = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "translations": "product_category_name_translation.csv",
}

def extract_data(raw_data_dir):
    datasets = {}

    for dataset_name, filename in FILES_CONFIG.items():
        file_path = raw_data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo no encotrado en la ruta: {file_path}"
            )

        dataframe = pd.read_csv(
            file_path, low_memory=False
        )
        datasets[dataset_name] = dataframe

        print(
            f"[OK] {dataset_name}: "
            f"{dataframe.shape[0]:,} filas y "
            f"{dataframe.shape[1]} columnas"
        )

    return datasets

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

    extracted_data = extract_data(RAW_DATA_DIR)
    print(
        f"\n=> Extracción finalizada: "
        f"{len(extracted_data)} datasets cargados."
    )
    for i,e in extracted_data.items(): print(e.info())

