# --- Etapa 1: Construcción y dependencias ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Evita que Python escriba archivos .pyc y fuerza el buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos herramientas de compilación por si alguna dependencia lo requiere
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos las dependencias en el espacio de usuario
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- Etapa 2: Entorno de ejecución final ---
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

# Copiamos solo las librerías instaladas desde la etapa de compilación
COPY --from=builder /root/.local /root/.local
# Copiamos el código fuente de nuestra aplicación
COPY ./app ./app

# Exponemos el puerto nativo de FastAPI
EXPOSE 8000

# Comando por defecto para arrancar la API lista para producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]