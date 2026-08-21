import sys
from pathlib import Path
import pandas as pd

PROJECT_ROT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROT) not in sys.path:
    sys.path.append(str(PROJECT_ROT))

from data.config import FILES_CONFIG_RELATIONS
RAW_DATA_DIR = PROJECT_ROT / "data" / "raw"
OUTPUT_TXT = PROJECT_ROT / "relaciones.txt"

def read_columns(filename, columns):
    # Carganmos unicamente las columnas necesarias (variable "columns")
    return pd.read_csv(
        RAW_DATA_DIR / filename,
        usecols=columns,
        low_memory=False
    )

dfs = {name: read_columns(file, cols) for name, (file, cols) in FILES_CONFIG_RELATIONS.items()}
customers, orders, items, products, sellers, payments, reviews, translations = dfs.values()

keys_check_data = []

def validate_foreign_key(relation_name, child_df, foreign_key, parent_df, primary_key):
    # Verificamos las claves nulas entre las columnas
    child_values = child_df[foreign_key]
    non_null_values = child_values.dropna() # Eliminar fila con un valor nulo en por lo menos una columna (creano una copia)

    # Comparamos claves hija innexistentes en la tabla padre
    orphan_mask = ~non_null_values.isin(parent_df[primary_key])

    # Conservamos todas las filas afectadas (valores TRUE - inexistentes en la tabla padre).
    orphan_values = non_null_values.loc[orphan_mask]

    # Por defectos siemrpe sumimos la bsuqueda de True
    # Alineación por indice (fila)

    unique_orphan_keys = (
        orphan_values
        .drop_duplicates()
        .tolist()
    )

    orphan_rows_count = len(orphan_values)
    unique_keys_count = len(unique_orphan_keys)

    if unique_orphan_keys:
        keys_check_data.append({
            "dataframe": relation_name.split(maxsplit=1)[0],
            "keys": unique_orphan_keys,
            "filas_afectadas": orphan_rows_count,
            "orphan_df": orphan_values,
        })

    return {
        "relación": relation_name,
        "registros": len(child_df),
        "claves_nulas": int(child_values.isna().sum()),
        "claves_huérfanas": orphan_rows_count,
        "claves_huérfanas únicas": unique_keys_count,
        "estado": "OK" if unique_keys_count == 0 else "REVISAR",
    }

list_relations = [
    {
        "relacion": "pedidos → clientes",
        "dataframes": [orders, customers],
        "keys": ["customer_id", "customer_id"],
    },
    {
        "relacion": "detalles → pedidos",
        "dataframes": [items, orders],
        "keys": ["order_id", "order_id"],
    },
    {
        "relacion": "detalles → productos",
        "dataframes": [items, products],
        "keys": ["product_id", "product_id"],
    },
    {
        "relacion": "detalles → vendedores",
        "dataframes": [items, sellers],
        "keys": ["seller_id", "seller_id"],
    },
    {
        "relacion": "pagos → pedidos",
        "dataframes": [payments, orders],
        "keys": ["order_id", "order_id"],
    },
    {
        "relacion": "reseñas → pedidos",
        "dataframes": [reviews, orders],
        "keys": ["order_id", "order_id"],
    },
    {
        "relacion": "productos → traducciones",
        "dataframes": [products, translations],
        "keys": ["product_category_name", "product_category_name"],
    },
]

results = [
    validate_foreign_key(
        rel["relacion"],
        rel["dataframes"][0],
        rel["keys"][0],
        rel["dataframes"][1],
        rel["keys"][1],
    )
    for rel in list_relations
]

results_df = pd.DataFrame(results)
results_df.columns = results_df.columns.str.upper()

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("RESUMEN DE VALIDACIÓN DE RELACIONES\n")
    f.write("=" * 60 + "\n\n")
    f.write(results_df.to_string(index=False))
    f.write("\n\n")

    if keys_check_data: 
        f.write("\n" + "=" * 50 + "\n")
        f.write("DETALLE DE CLAVES HUÉRFANAS ENCONTRADAS\n")
        f.write("=" * 50 + "\n")

        for lst in keys_check_data:
            f.write(f"> TABLA: {lst['dataframe']}\n")
            f.write(f"Indices y valores ...\n")
            f.write("-" * 60 + "\n")

            if lst['filas_afectadas'] > 15:
                f.write(f"\n... [ Mostrando 15 primeros registros ]\n")

            muestra_tabla = lst['orphan_df'].head(15).to_string(header=True)
            f.write(muestra_tabla + "\n")
            f.write("\n" + "=" * 60 + "\n\n")

            # f.write("\n".join(lst["keys"]) + "\n")

print(f"Proceso de verificación de relaciones finalizado")