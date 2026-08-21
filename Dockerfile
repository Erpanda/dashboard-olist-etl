# Minimal Dockerfile for both Streamlit app and ETL
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure Streamlit can read secrets if mounted
RUN mkdir -p /app/.streamlit

EXPOSE 8501

# Default: run the Streamlit app. For ETL override the command in docker-compose or `docker run`.
CMD ["streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
