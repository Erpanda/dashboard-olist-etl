from pathlib import Path
import pandas as pd

# Carpeta raiz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Definimos la ruta inical de los CSV
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Reporte de exporación de arcvhios CSV
OUTPUT_TXT = PROJECT_ROOT / "columnas.txt"

# Buscamos y ordenamos los CSV
csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No se encontraron archvos CSV en el directorio: {RAW_DATA_DIR}"
    )

# Conjunto de datos csv
summary = []

# Procesamos los archvios al simultaneo para no mantenerlos todos en memoria
for csv_file in csv_files:
    df = pd.read_csv(csv_file, low_memory=False)

    summary.append(
        {
            "archivo": csv_file.name,
            "filas": df.shape[0],
            "columnas": df.shape[1],
            "nulos": int(df.isna().sum().sum()),
            "duplicados": int(df.duplicated().sum()),
        }
    )

    with open(OUTPUT_TXT, "a", encoding="utf-8") as f:
        f.write(f"\nArchivo: {csv_file.name}\n")
        f.write(f"Columnas: {df.columns.tolist()}\n")

    # Liberamos el DF antes del siguiente (no ocupar mucho espacio)
    del df

summary_df = pd.DataFrame(summary)

with open(OUTPUT_TXT, "a", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("RESUMEN GENERAL\n")
    f.write("=" * 50 + "\n")
    f.write(summary_df.to_string(index=False))
    f.write("\n")

print(f"Proceso de exploración finalizado")