# 1. Usamos un Linux ligero y limpio con Python 3.11
FROM python:3.11-slim

# 2. Carpeta de trabajo
WORKDIR /app

# 3. Copiamos e instalamos el requirements.txt (aquí descargará la v1.58.0 o la más nueva)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. INSTALAMOS CHROMIUM Y SUS DEPENDENCIAS DE LINUX (Aquí sí tenemos permisos de Root)
RUN playwright install chromium
RUN playwright install-deps

# 5. Copiamos tu código
COPY api.py .

# 6. Prendemos el servidor
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-10000}
