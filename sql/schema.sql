-- CREACIÓN DEUN CONTENEDOR PARA ALAMCENAR LAS TABLAS
CREATE SCHEMA IF NOT EXISTS analytics;
-- => CULQUIER TABLA CREADA SIN EL PROFIJO, SE ALMACENARA EN LA DIRECION "analytics"
SET search_path TO analytics, public;

CREATE TABLE dim_customers (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY
        (START WITH 1 INCREMENT BY 1),
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix VARCHAR(5),
    customer_city TEXT,
    customer_state VARCHAR(2),

    CONSTRAINT pk_dim_customers PRIMARY KEY (customer_key),
    CONSTRAINT uq_dim_customers_customer_id UNIQUE (customer_id)
);

CREATE TABLE dim_products (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY
        (START WITH 1 INCREMENT BY 1),
    product_id TEXT NOT NULL,
    product_category_name TEXT,
    product_category_name_english TEXT,
    category_name TEXT NOT NULL,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(12, 2),
    product_height_cm NUMERIC(12, 2),
    product_width_cm NUMERIC(12, 2),
    product_volume_cm3 NUMERIC(14, 2),

    CONSTRAINT pk_dim_products PRIMARY KEY (product_key),
    CONSTRAINT uq_dim_products_product_id UNIQUE (product_id)
);

CREATE TABLE dim_sellers (
    seller_key BIGINT GENERATED ALWAYS AS IDENTITY 
        (START WITH 1 INCREMENT BY 1), 
    seller_id TEXT NOT NULL,
    seller_zip_code_prefix VARCHAR(5),
    seller_city TEXT,
    seller_state VARCHAR(2),

    CONSTRAINT pk_dim_sellers PRIMARY KEY (seller_key),
    CONSTRAINT uq_dim_sellers_seller_id UNIQUE (seller_id)
);

CREATE TABLE fact_orders (
    order_key BIGINT GENERATED ALWAYS AS IDENTITY (
        START WITH 1 INCREMENT BY 1),
    order_id TEXT NOT NULL,
    customer_key BIGINT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_year SMALLINT NOT NULL,
    purchase_month VARCHAR(7) NOT NULL,
    delivery_days NUMERIC(10, 2),
    delay_days NUMERIC(10, 2),
    delivery_buffer_days NUMERIC(10, 2),
    is_late BOOLEAN,

    CONSTRAINT pk_fact_orders PRIMARY KEY (order_key),
    CONSTRAINT uq_fact_orders_order_id UNIQUE (order_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_key) 
        REFERENCES dim_customers(customer_key),
    CONSTRAINT chk_fact_orders_delivery_days
        CHECK (delivery_days IS NULL OR delivery_days >= 0)

);

CREATE TABLE fact_order_items (
    order_key BIGINT NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_key BIGINT NOT NULL,
    seller_key BIGINT NOT NULL,
    shipping_limit_date TIMESTAMP NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    freight_value NUMERIC(12, 2) NOT NULL,
    item_total_value NUMERIC(12, 2) NOT NULL,
    has_free_freight BOOLEAN NOT NULL,

    CONSTRAINT pk_fact_order_items 
        PRIMARY KEY (order_key, order_item_id),
    CONSTRAINT fk_fact_items_order FOREIGN KEY (order_key) 
        REFERENCES fact_orders(order_key),
    CONSTRAINT fk_fact_items_product FOREIGN KEY (product_key) 
        REFERENCES dim_products(product_key),
    CONSTRAINT fk_fact_items_seller FOREIGN KEY (seller_key) 
        REFERENCES dim_sellers(seller_key),
    CONSTRAINT chk_fact_order_items_price CHECK (price >= 0),
    CONSTRAINT chk_fact_order_items_freight CHECK (freight_value >= 0),
    CONSTRAINT chk_fact_order_items_total CHECK (item_total_value >= 0)
);

CREATE TABLE fact_payments (
    order_key BIGINT NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value NUMERIC(12, 2) NOT NULL,
    has_installments BOOLEAN NOT NULL,

    CONSTRAINT pk_fact_payments PRIMARY KEY (order_key, payment_sequential),
    CONSTRAINT fk_fact_payments_order FOREIGN KEY (order_key)
        REFERENCES fact_orders(order_key),
    CONSTRAINT chk_fact_payments_installments CHECK (payment_installments >= 0),
    CONSTRAINT chk_fact_payments_value CHECK (payment_value >= 0)
);

CREATE TABLE fact_reviews (
    review_id TEXT NOT NULL,
    order_key BIGINT NOT NULL,
    review_score SMALLINT NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    has_comment BOOLEAN NOT NULL,
    satisfaction_level TEXT NOT NULL,
    review_response_hours NUMERIC(12, 2),

    CONSTRAINT pk_fact_reviews PRIMARY KEY (review_id, order_key),
    CONSTRAINT fk_fact_reviews_order FOREIGN KEY (order_key)
        REFERENCES fact_orders(order_key),
    CONSTRAINT chk_fact_reviews_level
        CHECK (satisfaction_level IN ('Negativa', 'Neutral', 'Positiva')),
    CONSTRAINT chk_fact_reviews_score CHECK (review_score BETWEEN 1 AND 5),
    CONSTRAINT chk_fact_reviews_response_hours CHECK (
        review_response_hours IS NULL OR review_response_hours >= 0
    )
);

CREATE INDEX idx_customers_unique ON dim_customers(customer_unique_id);
CREATE INDEX idx_customers_state ON dim_customers(customer_state);
CREATE INDEX idx_products_category ON dim_products(category_name);
CREATE INDEX idx_orders_customer ON fact_orders(customer_key);
CREATE INDEX idx_orders_purchase_date ON fact_orders(purchase_date);
CREATE INDEX idx_orders_status ON fact_orders(order_status);
CREATE INDEX idx_items_product ON fact_order_items(product_key);
CREATE INDEX idx_items_seller ON fact_order_items(seller_key);
CREATE INDEX idx_payments_method ON fact_payments(payment_method);
CREATE INDEX idx_reviews_score ON fact_reviews(review_score);
CREATE INDEX idx_reviews_satisfaction ON fact_reviews(satisfaction_level);
CREATE INDEX idx_reviews_order ON fact_reviews(order_key);

-- Evitamos acceso desde los roles de la API pública de la DB (SupaBase).
REVOKE ALL ON SCHEMA analytics
FROM anon, authenticated;

-- Elima los permisos osbre las tablas para los dos roles
REVOKE ALL ON ALL TABLES IN SCHEMA analytics
FROM anon, authenticated;

-- Verificación de tablas
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'analytics'
ORDER BY table_name;

SELECT
    table_name,
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'analytics' AND (
  constraint_name LIKE 'pk%' OR
  constraint_name LIKE 'fk%' OR
  constraint_name LIKE 'uq%'
)
ORDER BY table_name, constraint_type;


-- => Conección standar para un connection poll

    -- database_url = URL.create(
    --     drivername="postgresql+psycopg",
    --     username=os.getenv("DB_USER"),
    --     password=os.getenv("DB_PASSWORD"),
    --     host=os.getenv("DB_HOST"),
    --     port=int(os.getenv("DB_PORT", "5432")),
    --     database=os.getenv("DB_NAME", "postgres"),
    -- )

    -- return create_engine(
    --     database_url,
    --     pool_pre_ping=True,
    --     connec_arg={"sslmode": "require"}
    -- )

-- => uso de parametros seguros:
    -- query = text("SELECT * FROM clientes WHERE estado = :estado")


-- => .mappingss() diccionario de lso valores con key con el nombre de columnas
-- .scalars() obetern el primer valor cada fila. aplcia mejopr cunado sol hay un final general

-- .all() devulve en una lista 
-- .one() devvuelve solo uno


-- ==========================================================================

-- => CREACION DE VISTAS PARA EL DASHBORD

CREATE OR REPLACE VIEW analytics.vw_monthly_sales AS
SELECT
    o.purchase_month,
    o.purchase_year,
    COUNT(DIStinct o.order_key) AS total_orders,
    SUM(i.item_total_value) AS total_revenue,
    ROUND(SUM(i.item_total_value) / NULLIF(COUNT(DISTINCT o.order_key), 0), 2) AS avg_ticket
FROM analytics.fact_orders as o
JOIN analytics.fact_order_items i ON o.order_key = i.order_key
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY o.purchase_month, o.purchase_year
ORDER BY o.purchase_month;

CREATE OR REPLACE VIEW analytics.vw_sales_by_state AS
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_key) AS total_orders,
    SUM(i.item_total_value) AS total_revenue,
    ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
    ROUND(
        AVG(CASE WHEN o.is_late THEN 1.0 ELSE 0.0 END) * 100, 2
    ) AS late_rate_pct
FROM analytics.fact_orders o
JOIN analytics.dim_customers c ON o.customer_key = c.customer_key
JOIN analytics.fact_order_items i ON o.order_key = i.order_key
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY c.customer_state
ORDER BY total_revenue DESC;

CREATE OR REPLACE VIEW analytics.vw_category_performance AS
SELECT
    p.category_name,
    COUNT(DISTINCT i.order_key) AS total_orders,
    SUM(i.item_total_value) AS total_revenue,
    ROUND(AVG(i.price), 2) AS avg_price,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM analytics.fact_order_items i 
JOIN analytics.dim_products p ON i.product_key = p.product_key
LEFT JOIN analytics.fact_reviews r ON i.order_key = r.order_key
GROUP BY p.category_name
ORDER BY total_revenue DESC;

select * from analytics.vw_monthly_sales;
select * from analytics.vw_sales_by_state;
select * from analytics.vw_category_performance;

CREATE OR REPLACE analytics.vw_sales_state_month AS
SELECT
    c.customer_state,
    o.purchase_month,
    SUM(i.item_total_value) AS total_revenue
FROM analytics.fact_orders o
JOIN analytics.dim_customers c ON o.customer_key = c.customer_key
JOIN analytics.fact_order_items i ON o.order_key = i.order_key
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY c.customer_state, o.purchase_month
ORDER BY c.customer_state, o.purchase_month;

CREATE OR REPLACE VIEW analytics.vw_payment_behavior AS
SELECT
    p.payment_method,
    COUNT(DISTINCT o.order_key) as total_orders,
    SUM(p.payment_value) AS total_revenue,
    ROUND(SUM(p.payment_value) / NULLIF(COUNT(DISTINCT p.order_key), 0), 2) AS avg_ticket,
    ROUND(AVG(p.payment_installments), 1) AS avg_installments,
    ROUND(
        AVG(CASE WHEN p.has_installments THEN 1.0 ELSE 0.0 END) * 100, 2
    ) AS installment_use_pct
FROM analytics.fact_payments p 
JOIN analytics.fact_orders o ON p.order_key = o.order_key
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY p.payment_method
ORDER BY total_revenue DESC;

CREATE OR REPLACE analytics.vw_delivery_performance AS
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_key) AS total_delivered_orders,
    ROUND(AVG(o.delivery_days), 1) AS avg_delivery_days,
    ROUND(AVG(o.delivery_buffer_days), 1) AS avg_buffer_days,
    ROUND(
        AVG(CASE WHEN o.is_late THEN 1.0 ELSE 0.0 END) * 100, 2
    ) AS late_delivery_pct,
    ROUND(AVG(r.avg_order_score), 2) AS avg_review_score,
    ROUND(
        AVG(CASE WHEN NOT o.is_late THEN r.avg_order_score END), 2
    ) AS on_time_review_score,
    ROUND(
        AVG(CASE WHEN o.is_late THEN r.avg_order_score END), 2
    ) AS late_review_score
FROM analytics.fact_orders o
JOIN analytics.dim_customers c ON o.customer_key = c.customer_key
LEFT JOIN (
    SELECT order_key, AVG(review_score) AS avg_order_score
    FROM analytics.fact_reviews
    GROUP BY order_key
) r ON o.order_key = r.order_key
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY late_delivery_pct DESC;

