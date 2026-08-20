Primero creamos un entorno virtual: -m venv
=> py -3.12 -m venv .venv
   .venv\Scripts\Activate

Activar el entorno: Activate
=> Verificamos la dirección del entorno: python -c "import sys; print(sys.executable)"

=> Instalaremos las librerias
    python -m pip install --upgrade pip
    python -m pip install pandas streamlit plotly altair sqlalchemy "psycopg[binary]" python-dotenv

Se utiliza "python -m pip" para instalar las librerias dentro del entorno virtual
    - Streamlit => entorno web interactivo
    - altair => graficos declarativos
    - psycopg => conexion con PostgrSQL
    - python_dotenv => cargar credenciales de un .env

Definimos las versiones instaladas para su descarga en otros entorno: requeriments.txt
    - python -m pip freeze > requirements.txt
    Su instalacion es: python -m pip install -r requeriments.txt
    - Verificamos la instalación: python -c "import pandas, streamlit, plotly, altair, sqlalchemy, psycopg, dotenv; print('Instalación correcta')"

Definimos la estructura del proyecto:
    olist-dashboard-etl/
    ├── .venv/
    ├── dashboard/       # Aplicación web de Streamlit
    ├── data/
    │   ├── raw/         # CSV originales sin modificar (datos crudos)
    │   └── processed/   # Datos resultantes de la transformación (datos limpios)
    ├── sql/             # Modelo y consultas de PostgreSQL
    ├── src/             # Código del pipeline ETL
    ├── tests/           # Pruebas del proyecto
    └── requirements.txt

Definición de procesos:
    => extract: data/raw
    => transform: src
    => load: PostgresSQL/Supabase

.resolse() => definie al ruta en absoluta
.glob() => Buscar y filtrar

Path.(__file__).resolve().perent.parent

En la lectura de los csv=> 
    - pd.low_memory: hace la lectura de manera entera, no en bloques (=True)

Diferencia enter un .sum()y doble .sum() ne pd:
    => nulos doble: sumar por filas y columnas (devulve una matriz)
    => duplicaos uno solo: duma por filas repetidas


.isna().any(exis=1).sum() => evalua celda por celda, luego se agrupa por fila, aqui al ser de una sola columna no es necesario, aplica el any cuando son mas columnas y se aplica TRUE por fila ._.

(subset=columna) => Solo identifica los duplicados de esa columna
.toString(index=False) => Pasar un Dataframe a texto sin indices de los Dataframe
.loc => seleccionar y filtrara datos de un DF en base a sus etiquetas (nombre de las filas/indices)

.plit() => Divide por espacios, y "maxsplit=n" separa segn el numero de espacios

=> pd.cut() => agrupar y segmentar datos continuos en intervalos

    df["score_category"] = pd.cut(
        df["review_score"], 
        bins=bins,  #rangos: uno mas que los labels
        labels=labels
    )

.lt() => lo opuesto a .gt() ,aplica true a los menores 

.loc() filtro pro etiqueaty y cunta el final
.iloc() => filtro pro indice pero noc uenta el final
















