from pathlib import Path
import os

# -- ======================================

CANDIDATE_KEYS = {
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

# =======================================================================

FILES_CONFIG_RELATIONS = {
    "customers": ("olist_customers_dataset.csv", ["customer_id"]),
    "orders": ("olist_orders_dataset.csv", ["order_id", "customer_id"]),
    "items": ("olist_order_items_dataset.csv", ["order_id", "product_id", "seller_id"]),
    "products": ("olist_products_dataset.csv", ["product_id", "product_category_name"]),
    "sellers": ("olist_sellers_dataset.csv", ["seller_id"]),
    "payments": ("olist_order_payments_dataset.csv", ["order_id"]),
    "reviews": ("olist_order_reviews_dataset.csv", ["order_id"]),
    "translations": ("product_category_name_translation.csv", ["product_category_name"]),
}

# -- ======================================

DATE_COLUMNS_ORDERS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

PAYMENT_METHODS = {
    "credit_card": "Tarjeta de crédito",
    "debit_card": "Tarjeta de débito",
    "boleto": "Boleto bancario",
    "voucher": "Cupón",
    "not_defined": "No definido",
}

# -- =======================================

SCHEMA = "analytics"

# Reglas de formato y estructura de tablas para su migración 
DIMENSION_CONFIG = {
    "customers": {
        "table": "dim_customers",
        "business_key": "customer_id",
        "columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    },
    "products": {
        "table": "dim_products",
        "business_key": "product_id",
        "columns": [
            "product_id",
            "product_category_name",
            "product_category_name_english",
            "category_name",
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
            "product_volume_cm3",
        ],
    },
    "sellers": {
        "table": "dim_sellers",
        "business_key": "seller_id",
        "columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
    },
}

ORDER_COLUMNS = [
    "order_id",
    "customer_key",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "purchase_date",
    "purchase_year",
    "purchase_month",
    "delivery_days",
    "delay_days",
    "delivery_buffer_days",
    "is_late",
]

ORDER_ITEMS_COLUMNS = [
    "order_key",
    "order_item_id",
    "product_key",
    "seller_key",
    "shipping_limit_date",
    "price",
    "freight_value",
    "item_total_value",
    "has_free_freight",
]

ORDER_PAYMENTS_COLUMNS = [
    "order_key",
    "payment_sequential",
    "payment_type",
    "payment_method",
    "payment_installments",
    "payment_value",
    "has_installments",
]

REVIEWS_COLUMNS = [
    "review_id",
    "order_key",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
    "has_comment",
    "satisfaction_level",
    "review_response_hours",
]
