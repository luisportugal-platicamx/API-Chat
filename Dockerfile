# 1. Usar la computadora oficial de Microsoft que ya tiene TODO preinstalado
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# 2. Crear una carpeta de trabajo
WORKDIR /app

# 3. Copiar e instalar nuestros requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar nuestro código
COPY api.py .

# 5. Prender el servidor
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-10000}
