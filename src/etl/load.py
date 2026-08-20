from pathlib import Path
import pandas as pd

from sqlalchemy import MetaData, Table, func, select
# Libreiras PostgresSQL (Supa coneccrtion)
from sqlalchemy.dialects.postgresql import insert

from src.db.connection import create_db_connection
from src.etl.extract import extract_data
from src.etl.transform import transform_data
from data.config import SCHEMA, DIMENSION_CONFIG, ORDER_COLUMNS, ORDER_ITEMS_COLUMNS, ORDER_PAYMENTS_COLUMNS, REVIEWS_COLUMNS

def dataframe_to_records(dataframe, columns):
    # Transformamos los dtaos df para postgres => Pasamos NaN, NaT y pd.NA en NONE para postgres
    select_data = dataframe[columns].copy()
    select_data = (
        select_data.astype(object).where(select_data.notna(), None)
    )

    return select_data.to_dict(orient="records")

def upsert_table(con, df, table_name, conflict_columns, columns, batch_size: int = 5000):
    # Insertamos nuevos datos o los reemplzamos
    metadata = MetaData()

    table = Table(table_name, metadata, schema=SCHEMA, autoload_with=con)
    ## => Ispeccion automatica de los tipos de datos
    total_rows = len(df)

    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        batch_df = df.iloc[start:end]

        records = dataframe_to_records(batch_df, columns)

        insert_statement = insert(table).values(records)
        update_values = {
            column: insert_statement.excluded[column]
            for column in columns
                if column not in conflict_columns
        }

        upsert_statement = (
            insert_statement.on_conflict_do_update(
                index_elements=[
                    table.c[column] for column in conflict_columns
                ], 
                set_=update_values
            )
        )

        con.execute(upsert_statement)

        print(
            f" => {table_name}: "
            f"{end:,}/{total_rows:,} procesados"
        )

def get_key_map(con, table_name, business_key, surrogate_key):
    metadata = MetaData()

    table = Table(table_name, metadata, schema=SCHEMA, autoload_with=con)
    statement = select(table.c[business_key], table.c[surrogate_key])

    # Devolverlo en una tablas mas legible
    return pd.read_sql(statement, con)

# Relacionar una ID (PK) con la clave sustituta (valve db con la clave de csv)
def add_surrugate_key(datafranme, key_map, business_key, surrogate_key, relation_name):
    result = datafranme.merge(key_map, on=business_key, how="left", validate="many_to_one")
    missing_mask = result[surrogate_key].isna()

    if missing_mask.any():
        missing_values = (
            result.loc[missing_mask, business_key]
            .drop_duplicates()
            .head(10)
            .tolist()
        )

        raise ValueError(
            f"{relation_name}: existen valores sin "
            f"{surrogate_key}. Ejemplos: "
            f"{missing_values}"
        )

    result[surrogate_key] = (result[surrogate_key].astype("Int64"))
    return result

# Cambios con la relación de tablas (customer_id => customer_key)
def prepare_fact_orders(order_df, customer_keys):
    orders = order_df.copy()

    orders = orders.merge(customer_keys, on="customer_id", how="left", validate="many_to_one")
    missing_customer_keys = (orders["customer_key"].isna())

    if missing_customer_keys.any():
        missing_ids = (
            orders.loc[missing_customer_keys, "customer_id"]
            .drop_duplicates()
            .head(10).tolist()
        )

        raise ValueError(
            "Existen pedidos sin customer_key. "
            f"Ejemplos: {missing_ids}"
        )

    orders["customer_key"] = (orders["customer_key"].astype("Int64"))

    return orders[ORDER_COLUMNS]

# => columns_id: Lista de llaves FK
def prepare_fact_order_items(items_df, order_keys, product_keys, seller_keys):
    items = items_df.copy()

    items = add_surrugate_key(items, order_keys, "order_id", "order_key", "detalle_pedido / pedidos")
    items = add_surrugate_key(items, product_keys, "product_id", "product_key", "detalle_pedido / productos")
    items = add_surrugate_key(items, seller_keys, "seller_id", "seller_key", "detalle_pedido / vendedores")

    items["order_item_id"] = (items["order_item_id"].astype("Int64"))
    return items[ORDER_ITEMS_COLUMNS]

def prepare_fact_order_payments(order_payments_df, order_keys):
    payments = order_payments_df.copy()

    payments = add_surrugate_key(payments, order_keys, "order_id", "order_key", "pagos_pedido / pedidos")

    payments["payment_sequential"] = (payments["payment_sequential"].astype("Int64"))
    payments["payment_installments"] = (payments["payment_installments"].astype("Int64"))
    return payments[ORDER_PAYMENTS_COLUMNS]

def prepare_fact_reviews(reviews_df, order_keys):
    reviews = reviews_df.copy()

    reviews = add_surrugate_key(reviews, order_keys, "order_id", "order_key", "reviews / pedidos")
    reviews["review_score"] = (reviews["review_score"].astype("Int64"))
    return reviews[REVIEWS_COLUMNS]

# Conteo de registros almacenados por tabla
def count_table_rows(con, table_name):
    metadata = MetaData()

    # => Es necesario que se conosca la estrcutua de la tabla a trabajar
    table = Table(table_name, metadata, schema=SCHEMA, autoload_with=con)
    statement = select(func.count()).select_from(table)

    return con.execute(statement).scalar_one()

def load_fact_orders(order_df):
    con = create_db_connection()

    try:

        with con.begin() as connection:
            customer_keys = get_key_map(connection, "dim_customers", "customer_id", "customer_key")
            prepared_orders = prepare_fact_orders(order_df, customer_keys)

            print("\nCargando tabla de hechos: fact_orders...")

            upsert_table(connection, prepared_orders, "fact_orders", ["order_id"], ORDER_COLUMNS, 2000)
            stored_rows = count_table_rows(connection, "fact_orders")
            unique_orders = (order_df["order_id"].nunique())

            if stored_rows != unique_orders:
                raise ValueError(
                    "La cantidad cargada no coincide. "
                    f"Esperados: {unique_orders:,}; "
                    f"almacenados: {stored_rows:,}"
                )

            print(f"\nfact_orders: {stored_rows:,} registros")

    finally: con.dispose()

def load_fact_order_items(order_items_df):
    con = create_db_connection()

    try:
        with con.begin() as connection:
            order_keys = get_key_map(connection, "fact_orders", "order_id", "order_key")
            product_keys = get_key_map(connection, "dim_products", "product_id", "product_key")
            seller_keys = get_key_map(connection, "dim_sellers", "seller_id", "seller_key")

            prepared_items = prepare_fact_order_items(order_items_df, order_keys, product_keys, seller_keys)

            source_rows = len(prepared_items)
            unique_items = (prepared_items[["order_key", "order_item_id"]].drop_duplicates().shape[0])

            if source_rows != unique_items:
                raise ValueError("La fuente contiene detalles de pedidos duplicados.")

            print("\nCargando fact_order_items...")

            upsert_table(connection, prepared_items, "fact_order_items", ["order_key", "order_item_id"], ORDER_ITEMS_COLUMNS, 3000)
            stored_rows = count_table_rows(connection, "fact_order_items")

            if stored_rows != source_rows:
                raise ValueError(
                    "La cantidad cargada no coincide. "
                    f"Esperados: {source_rows:,}; "
                    f"almacenados: {stored_rows:,}"
                )

            print(f"\nfact_order_items: {stored_rows:,} registros")

    finally: con.dispose()

def load_fact_order_paymnets(order_payments_df):
    con = create_db_connection()

    try:
        with con.begin() as connection:
            order_keys = get_key_map(connection, "fact_orders", "order_id", "order_key")
            prepare_payments = prepare_fact_order_payments(order_payments_df, order_keys)

            source_rows = len(prepare_payments)
            unique_items = (prepare_payments[["order_key", "payment_sequential"]].drop_duplicates().shape[0])

            if source_rows != unique_items:
                raise ValueError("La fuente contiene pagos de pedidos duplicados.")

            print("\nCargando fact_payments...")

            upsert_table(connection, prepare_payments, "fact_payments", ["order_key", "payment_sequential"], ORDER_PAYMENTS_COLUMNS, 3000)
            stored_rows = count_table_rows(connection, "fact_payments")

            if stored_rows != source_rows:
                raise ValueError(
                    "La cantidad de pagos no coincide. "
                    f"Esperados: {source_rows:,}; "
                    f"almacenados: {stored_rows:,}"
                )

            print(f"\nfact_payments: {stored_rows:,} registros")

    finally: con.dispose()

def load_fact_reviews(reviews_df):
    con = create_db_connection()

    try:
        with con.begin() as connection:
            order_keys = get_key_map(connection, "fact_orders", "order_id", "order_key")
            prepared_reviews = prepare_fact_reviews(reviews_df, order_keys)

            source_rows = len(prepared_reviews)
            unique_reviews = (prepared_reviews[["review_id", "order_key"]].drop_duplicates().shape[0])

            if source_rows != unique_reviews:
                raise ValueError("La fuente contiene detalles de pedidos duplicados.")

            print("\nCargando fact_reviews...")

            upsert_table(connection, prepared_reviews, "fact_reviews", ["review_id", "order_key"], REVIEWS_COLUMNS, 3000)
            stored_rows = count_table_rows(connection, "fact_reviews")

            if stored_rows != source_rows:
                raise ValueError(
                    "La cantidad de reseñas no coincide. "
                    f"Esperados: {source_rows:,}; "
                    f"almacenados: {stored_rows:,}"
                )

            print(f"\nfact_reviews: {stored_rows:,} registros")

    finally: con.dispose()

# Coordinamos la carga e insercion de lso datos a las tablas
def load_dimensions(transformed_data):
    con = create_db_connection()

    try:
        with con.begin() as connection:
            for dataset, config in (DIMENSION_CONFIG.items()):
                print(f"\nProcesando dataset: {config['table']}")

                upsert_table(connection, transformed_data[dataset], config["table"], [config["business_key"]], config["columns"])

            print("\nREGISTROS EN LA BASE DE DATOS")

            for config in DIMENSION_CONFIG.values():
                total = count_table_rows(connection, config["table"])
                print(f"- {config['table']}: {total:,}")
    finally:
        con.dispose()

if __name__ == "__main__":
    PROJECT_ROOT = (Path(__file__).resolve().parent.parent.parent)
    RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

    extracted_data = extract_data(RAW_DATA_DIR)
    transformed_data = transform_data(extracted_data)

    load_dimensions(transformed_data)

    # Después cargamos los fact tables.
    load_fact_orders(transformed_data["orders"])
    load_fact_order_items(transformed_data["items"])
    load_fact_order_paymnets(transformed_data["payments"])
    load_fact_reviews(transformed_data["reviews"])

    print(
        "\n[OK] Dimensiones y pedidos "
        "cargados correctamente."
    )