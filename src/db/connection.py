import os
from pathlib import Path

from dotenv import load_dotenv
# create_engine => creación por defecto del POOL
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Creamos una CONNECTION POOL ._. 
def create_db_connection():
    required_credentials = ["DB_HOST", "DB_USER", "DB_PASSWORD",]
    missing_variables = [var for var in required_credentials if not os.getenv(var)]

    if missing_variables:
        raise ValueError(
            "Faltan variables en .env: " + ", ".join(missing_variables)
        )

    # Contruimos la dirección para la conexion
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "postgres"),
    )

    return create_engine(
        database_url,
        pool_pre_ping=True, ## mantner una conección activa aun con inactividad
        connect_args={"sslmode": "require"}, ### activamos la encriptación de datos
    )

def test_db_connection():
    cn = create_db_connection()

    try:
        with cn.connect() as con:
            database_info = con.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS username
                    """
                )
            ).mappings().one()
            
            print(database_info["database_name"])

    except SQLAlchemyError as error:
        raise ConnectionError(
            "Error de conexión. Revisar las variables .env y las Session Pooler. "
        ) from error

    finally:
        cn.dispose() ## solo usarlo en pruebas

if __name__ == "__main__":
    test_db_connection()