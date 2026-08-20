from pathlib import Path
import pandas as pd
from src.etl.extract import extract_data

from data.config import DATE_COLUMNS_ORDERS, PAYMENT_METHODS

## ====================================================================

def check_duplicates(df, subset, name):
    duplicates = df.duplicated(subset=subset).sum()
    if duplicates > 0:
        raise ValueError(f"Se encontraron {duplicates} registros duplicados en {name}.")

def parse_datetime_columns(df, columns):
    for col in df.columns:
        if col not in columns:
            continue
        original_non_null = df[col].notna()

        df[col] = pd.to_datetime(df[col], errors="coerce")
        invalid = (original_non_null & df[col].isna()).sum()

        if invalid > 0:
            raise ValueError(f"La columna '{col}' contiene {invalid} fechas inválidas.")

def parse_numeric_columns(df, columns, check_negative = False):
    for col in df.columns:
        if col not in columns: continue

        original_non_null = df[col].notna()
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )
        invalid = (original_non_null & df[col].isna()).sum()

        if invalid > 0:
            raise ValueError(f"La columna '{col}' contiene {invalid} valores no numéricos.")

        if check_negative and (df[col] < 0).sum() > 0:
            raise ValueError(f"La columna '{col}' contiene valores negativos.")

def normalizate_zip_code(zip_code):
    numeric_zip = pd.to_numeric(zip_code, errors="coerce")
    invalid_values = (zip_code.notna() & numeric_zip.isna()).sum()

    if invalid_values > 0:
        raise ValueError(f"Se encontraron {invalid_values} códigos postales inválidos.")

    return (
        numeric_zip
        .round()
        .astype("Int64")
        .astype("string")
        .str.zfill(5)  # => Añadir ceros para completar los 5 caracteres
    )

def normalizate_location(df, city, state):

    df[city] = (
        df[city].astype("string")
        .str.strip().str.title()
    )

    df[state] = (
        df[state].astype("string")
        .str.strip().str.upper()
    )

## ====================================================================

def transform_orders(orders_df):
    # Copiar para no alterar el df "original"
    orders = orders_df.copy()

    check_duplicates(orders, subset="order_id", name="order_id")

    orders["order_status"] = (
        orders["order_status"]
        .str.strip()
        .str.lower()
    )

    parse_datetime_columns(orders, DATE_COLUMNS_ORDERS)

    # Creamos columnas para análisis, filtros y gráficos
    ts = orders["order_purchase_timestamp"].dt
    orders["purchase_date"] = ts.date
    orders["purchase_year"] = ts.year
    orders["purchase_month"] = ts.to_period("M").astype("string")

    # Añadimos variables temporales
    delivered = orders["order_delivered_customer_date"]

    orders["delivery_days"] = (
        (delivered - orders["order_purchase_timestamp"])
        .dt.total_seconds().div(86400).round(2)
    )

    # Buffer real sin recortar: negativo = tarde, positivo = anticipado.
    # Se conserva sin clip para no perder la distribución completa,
    # útil para el dashboard (ej. "promedio de días de anticipación").
    delivery_buffer_days = (
        (orders["order_estimated_delivery_date"] - delivered)
        .dt.total_seconds().div(86400).round(2)
    )

    orders["delay_days"] = (
        (delivered - orders["order_estimated_delivery_date"])
        .dt.total_seconds().div(86400).round(2)
        .clip(lower=0)
    )

    orders["delivery_buffer_days"] = delivery_buffer_days

    orders["is_late"] = orders["delay_days"].gt(0).astype("boolean")
    orders.loc[orders["delay_days"].isna(), "is_late"] = pd.NA

    return orders

def transform_products(products_df, translations_df):
    products = products_df.copy()
    translations = translations_df.copy()

    check_duplicates(products, subset="product_id", name="product_id")

    products["product_category_name"] = products["product_category_name"].str.strip().str.lower()
    translations["product_category_name"] = translations["product_category_name"].str.strip().str.lower()

    products = products.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })

    products = products.merge(
        translations,
        on="product_category_name",
        how="left",
        validate="many_to_one"
    )

    products["category_name"] = (
        products["product_category_name_english"]
        .combine_first(
            products["product_category_name"]
        )
        .fillna("unknown")
        # Normalización de nombres
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    numeric_columns = [
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    parse_numeric_columns(products, numeric_columns)

    # Definición de voluamen del producto
    products["product_volume_cm3"] = (
        products["product_length_cm"] * products["product_height_cm"] * products["product_width_cm"]
    ).round(2)

    integer_columns = [
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
    ]

    for col in integer_columns:
        products[col] = products[col].astype("Int64")

    return products
    
def transform_items(items_df):
    items = items_df.copy()

    check_duplicates(items, subset=["order_id", "order_item_id"], name="order_item")
    parse_datetime_columns(items, ["shipping_limit_date"])
    
    numeric_columns = ["price", "freight_value",]

    parse_numeric_columns(items, numeric_columns, True)

    items["item_total_value"] = (
        items["price"] + items["freight_value"]
    ).round(2)

    # Idnetificamos productos con evnuio gratis
    items["has_free_freight"] = items["freight_value"].eq(0)

    return items

def transform_payments(payments_df):
    payments = payments_df.copy()

    check_duplicates(payments, subset=["order_id", "payment_sequential"], name="payment_id")
    payments["payment_type"] = payments["payment_type"].str.strip().str.lower()

    # Normalización al español
    payments["payment_method"] = payments["payment_type"].map(PAYMENT_METHODS).fillna("Otro")

    numeric_columns = ["payment_installments", "payment_value"]
    parse_numeric_columns(payments, numeric_columns, True)

    payments["payment_installments"] = payments["payment_installments"].astype("Int64")

    # Devuelve un valor booleanoi si es mas de un pago
    payments["has_installments"] = payments["payment_installments"].gt(1)

    return payments

def transform_customers(customers_df):
    customers = customers_df.copy()

    check_duplicates(customers, subset="customer_id", name="customer_id")
    normalizate_location(customers, "customer_city", "customer_state")

    customers["customer_zip_code_prefix"] = (
        normalizate_zip_code(customers["customer_zip_code_prefix"])
    )

    return customers

def transform_sellers(sellers_df):
    sellers = sellers_df.copy()

    check_duplicates(sellers, subset="seller_id", name="seller_id")
    normalizate_location(sellers, "seller_city", "seller_state")

    sellers["seller_zip_code_prefix"] = (
        normalizate_zip_code(sellers["seller_zip_code_prefix"])
    )

    return sellers

def transform_reviews(reviews_df):
    reviews = reviews_df.copy()
    check_duplicates(reviews, subset=["review_id", "order_id"], name="review_id")
    parse_numeric_columns(reviews, ["review_score"])

    # Verificación de rangos
    out_of_range = (
        reviews["review_score"].notna()
        & ~reviews["review_score"].between(1,5)
    ).sum()

    if out_of_range > 0:
        raise ValueError(f"Se encontraron {out_of_range} puntuaciones fuera del rango 1-5.")

    reviews["review_score"] = reviews["review_score"].astype("Int64")

    review_date_columns = ["review_creation_date", "review_answer_timestamp",]
    parse_datetime_columns(reviews, review_date_columns)

    # Normalizamos los textos vacíos
    text_columns = ["review_comment_title", "review_comment_message"]

    for column in text_columns:
        reviews[column] = reviews[column].astype("string").str.strip().replace("", pd.NA)

    reviews["has_comment"] = (
        reviews["review_comment_title"].notna()
        | reviews["review_comment_message"].notna()
    )

    # Clasificacion de satisfacción
    reviews["satisfaction_level"] = pd.cut(
        reviews["review_score"],
        bins=[0, 2, 3, 5],
        labels=["Negativa", "Neutral", "Positiva"]
    ).astype("string")

    reviews["review_response_hours"] = (
        (reviews["review_answer_timestamp"] - reviews["review_creation_date"])
        .dt.total_seconds().div(3600).round(2)
    )

    negative_response_times = (
        reviews["review_response_hours"].lt(0).sum()
    )

    if negative_response_times > 0:
        raise ValueError(f"Se encontraron {negative_response_times} tiempos de respuesta negativos.")

    return reviews

def transform_data(datasets):
    # Creamos una copia del dataset para transformar
    # => El conjunto de dataset (copia) sera modificado solo en orders
    transformed_data = datasets.copy()
    
    transformed_data["orders"] = transform_orders(
        datasets["orders"]
    )
    transformed_data["products"] = transform_products(
        datasets["products"],
        datasets["translations"]
    )
    transformed_data["items"] = transform_items(
        datasets["items"]
    )
    transformed_data["payments"] = transform_payments(
        datasets["payments"]
    )
    transformed_data["customers"] = transform_customers(
        datasets["customers"]
    )
    transformed_data["sellers"] = transform_sellers(
        datasets["sellers"]
    )
    transformed_data["reviews"] = transform_reviews(
        datasets["reviews"]
    )

    return transformed_data

## ====================================================================

if __name__ == "__main__":
    PROJECT_ROOT = (
        Path(__file__).resolve().parent.parent.parent
    )

    RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

    extracted_data = extract_data(RAW_DATA_DIR)
    transformed_data = transform_data(extracted_data)

    orders = transformed_data["orders"]
    products = transformed_data["products"]
    items = transformed_data["items"]
    payments = transformed_data["payments"]
    customers = transformed_data["customers"]
    sellers = transformed_data["sellers"]
    reviews = transformed_data["reviews"]

    with open("reporte_transform.txt", "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("REPORTE DE TRANSFORMACIÓN DE DATOS\n")
        f.write("=" * 50 + "\n")

        for table_name, df in transformed_data.items():
            f.write("\n" + "=" * 50 + "\n")
            f.write(f"TABLA: {table_name}\n")
            f.write("=" * 50 + "\n")
            f.write(f"{df}\n")