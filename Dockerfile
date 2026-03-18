# ==============================================================================
# Dockerfile - Sistema de Gestión Empresarial
# ==============================================================================
# Este archivo le dice a Docker cómo "empaquetar" tu aplicación Flask
# para que funcione en cualquier servidor (como tu VPS con EasyPanel).
#
# Usa Python 3.12-slim como base (versión ligera de Linux con Python).
# Instala las dependencias del sistema necesarias para Playwright (Chromium),
# que es lo que usa la app para generar PDFs.
# ==============================================================================

# --- PASO 1: Imagen base ---
# Usamos Python 3.12 en versión "slim" (más ligera que la completa)
FROM python:3.12-slim

# --- PASO 2: Directorio de trabajo ---
# Todo el código de la app se copiará aquí dentro del contenedor
WORKDIR /app

# --- PASO 3: Instalar dependencias del sistema ---
# Playwright necesita estas librerías de Linux para funcionar con Chromium.
# Sin ellas, la generación de PDFs fallará con errores de "browser not found".
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# --- PASO 4: Instalar dependencias de Python ---
# Primero copiamos SOLO requirements.txt para aprovechar la caché de Docker.
# Si no cambias las dependencias, Docker no las reinstalará cada vez.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- PASO 5: Instalar Playwright con Chromium ---
# Descarga el navegador Chromium que se usa para generar PDFs desde HTML.
# --with-deps instala cualquier dependencia extra del sistema que falte.
RUN playwright install --with-deps chromium

# --- PASO 6: Copiar el código de la aplicación ---
# Copia todo el proyecto al contenedor (lo que no esté en .dockerignore).
COPY . .

# --- PASO 7: Crear carpeta instance ---
# Esta carpeta almacena la base de datos y los PDFs generados.
# En producción (EasyPanel), esta carpeta se monta como un "volumen"
# para que los datos persistan aunque se reinicie el contenedor.
RUN mkdir -p /app/instance/pdfs/ofertas /app/instance/pdfs/partes /app/instance/pdfs/facturas

# --- PASO 8: Exponer el puerto ---
# Le dice a Docker que la app escucha en el puerto 5000
EXPOSE 5000

# --- PASO 9: Comando de arranque ---
# Cuando el contenedor se inicie, ejecutará este comando
CMD ["python", "app.py"]
