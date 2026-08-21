import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

@st.cache_resource
def get_connection():
    database_URL = URL.create(
        drivername="postgresql+psycopg",
        username=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        host=st.secrets["DB_HOST"],
        port=int(st.secrets.get("DB_PORT", "5432")),
        database=st.secrets.get("DB_NAME", "postgres"),
    )

    return create_engine(
        database_URL, pool_pre_ping=True, connect_args={"sslmode": "require"},
    )

@st.cache_data(ttl=600)
def run_query(query, params=None):
    connection = get_connection()

    with connection.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})
    
# -- ==============================

# => Aplicación de la libreria streamlit; connnection SQLpostgres (una sola vez, para siempre)
# Crea la conección UNA sola vez por sesión de la app. 

# => Aplicación de la libreria streamlit; ejecución de QUERY (actualización cada N timepo en caso de actualizaciones)
# Ejecuta una query y cachea el RESULTADO (no la conexión). 