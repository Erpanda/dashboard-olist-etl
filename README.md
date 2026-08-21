# Olist ETL & Analytics Dashboard

Proyecto de ingeniería de datos enfocado en la construcción de un
**pipeline ETL**, modelado dimensional en **PostgreSQL** y visualización
de métricas mediante un **dashboard interactivo en Streamlit**.

El proyecto utiliza el dataset público de **Olist E-commerce** para
transformar datos transaccionales en información útil para el análisis
de ventas, clientes, productos, pagos y entregas.

------------------------------------------------------------------------

## Tecnologías

-   **Python**
-   **Pandas**
-   **PostgreSQL**
-   **SQLAlchemy**
-   **Psycopg**
-   **Streamlit**
-   **Plotly**
-   **Altair**

------------------------------------------------------------------------

## Arquitectura

``` text
CSV Raw Data
     │
     ▼
 Extract
     │
     ▼
 Transform
     │
     ▼
 Validate
     │
     ▼
 PostgreSQL
     │
     ├── Dimensions
     ├── Facts
     └── Analytical Views
              │
              ▼
       Streamlit Dashboard
```

El pipeline sigue tres etapas principales:

**Extract → Transform → Load**

-   **Extract:** lectura de los datasets originales de Olist.
-   **Transform:** limpieza, normalización, conversión de tipos y
    generación de métricas.
-   **Load:** carga de dimensiones y tablas de hechos en PostgreSQL
    mediante operaciones `UPSERT`.

------------------------------------------------------------------------

## Estructura del proyecto

``` text
olist-dashboard-etl/
│
├── dashboard/
│   ├── app.py
│   └── db_connection.py
│
├── data/
│   ├── raw/
│   └── config.py
│
├── src/
│   ├── db/
│   │   └── connection.py
│   ├── etl/
│   │   ├── extract.py
│   │   ├── transform.py
│   │   └── load.py
│   ├── validate_key.py
│   ├── validate_relations.py
│   └── explore_data.py
│
├── sql/
│   └── schema.sql
│
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## Modelo de datos

La base de datos utiliza un modelo dimensional dentro del esquema
`analytics`.

### Dimensiones

``` text
dim_customers
dim_products
dim_sellers
```

### Tablas de hechos

``` text
fact_orders
fact_order_items
fact_payments
fact_reviews
```

Además, se utilizan claves sustitutas, claves foráneas, restricciones e
índices para mantener la integridad y facilitar las consultas
analíticas.

### Creación de la Base de Datos - Schema "analytics"

#### Pasos de ejecución

1. **Abrir la terminal en VS Code:**
   Asegúrate de estar en la carpeta raíz de tu proyecto (donde se encuentra la carpeta `sql/`).

2. **Reemplazar credenciales:**
   Sustituye `[DB_USER]`, `[DB_PASSWORD]` y `[DB_PORT]` por tus datos reales de Supabase. Ten en cuenta que el puerto varía según si utilizas una conexión mediante IPv4 o IPv6.

3. **Ejecutar el comando:**
   Copia y ejecuta la siguiente línea en tu terminal:

```bash
psql "postgresql://[DB_USER]:[DB_PASSWORD]@aws-0-ca-central-1.pooler.supabase.com:[DB_PORT]/postgres" -f sql/schema.sql
```

------------------------------------------------------------------------

## Vistas analíticas

El dashboard consume vistas SQL diseñadas para obtener métricas
previamente procesadas:

``` text
vw_monthly_sales
vw_sales_by_state
vw_category_performance
vw_sales_state_month
vw_payment_behavior
vw_delivery_performance
```

Estas vistas permiten separar la lógica analítica de la interfaz del
dashboard.

------------------------------------------------------------------------

## Dashboard

La aplicación desarrollada con **Streamlit** consulta PostgreSQL y
presenta indicadores y visualizaciones sobre:

-   Evolución de ventas
-   Ventas por estado
-   Rendimiento por categoría
-   Métodos de pago
-   Comportamiento de entregas
-   Satisfacción del cliente

Las visualizaciones se construyen principalmente con **Plotly** y
**Altair**.

------------------------------------------------------------------------

## Instalación

### 1. Clonar el repositorio

``` bash
git clone <repo-url>
cd olist-dashboard-etl
```

### 2. Crear entorno virtual

``` bash
python -m venv .venv
```

En Windows:

``` bash
.venv\Scripts\activate
```

### 3. Instalar dependencias

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## Configuración de PostgreSQL

Crear un archivo `.env` en la raíz:

``` env
DB_HOST=tu_host
DB_PORT=5432
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=tu_base_de_datos
```

Las credenciales reales **no deben subirse al repositorio**.

Para Streamlit pueden configurarse mediante `.streamlit/secrets.toml` o
directamente mediante los secretos del entorno de despliegue.

------------------------------------------------------------------------

## Ejecutar el ETL

Para ejecutar el pipeline completo:

``` bash
python src/etl/load.py
```

También pueden ejecutarse las etapas individualmente:

``` bash
python src/etl/extract.py
python src/etl/transform.py
```

### Validación de datos

``` bash
python src/validate_key.py
python src/validate_relations.py
```

Estos scripts permiten detectar duplicados, claves inválidas y
relaciones huérfanas antes de realizar la carga.

------------------------------------------------------------------------

## Ejecutar el dashboard

Primero debe ejecutarse `sql/schema.sql` y cargarse la información
mediante el pipeline ETL.

Después:

``` bash
streamlit run dashboard/app.py
```

La aplicación se iniciará localmente y consultará las vistas disponibles
en PostgreSQL.

------------------------------------------------------------------------

## Dataset

El proyecto utiliza los datasets de **Olist Brazilian E-Commerce**,
incluyendo información relacionada con:

-   Customers
-   Orders
-   Order Items
-   Products
-   Sellers
-   Payments
-   Reviews
-   Product Categories

Los archivos originales se almacenan en `data/raw/`.

------------------------------------------------------------------------

## Flujo general

``` text
Olist CSV
    │
    ▼
Extracción
    │
    ▼
Transformación
    │
    ▼
Validación
    │
    ▼
Modelo dimensional
    │
    ▼
PostgreSQL
    │
    ▼
Vistas analíticas
    │
    ▼
Streamlit Dashboard
```

------------------------------------------------------------------------

## Seguridad

El proyecto mantiene las credenciales fuera del código fuente mediante:

-   `.env` para el pipeline ETL.
-   `st.secrets` para Streamlit.
-   `.gitignore` para evitar publicar información sensible.

------------------------------------------------------------------------

## Objetivo

Este proyecto busca aplicar un flujo completo de **Data Engineering +
Data Analytics**, desde datos crudos hasta su transformación en
indicadores visuales útiles para el análisis del comportamiento
comercial de un e-commerce.
