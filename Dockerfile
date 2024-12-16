# Usa una imagen base de Python
FROM python:3.9-slim

# Configurar el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos y la aplicación
COPY requirements.txt requirements.txt
COPY . .

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto donde tu aplicación se ejecutará
EXPOSE 5001

# Comando para ejecutar tu aplicación Flask en modo debug
CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]

