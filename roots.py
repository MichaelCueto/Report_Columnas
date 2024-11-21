
import os
import sys

def get_base_path():
    """Obtener la base path dependiendo si la aplicación está congelada o no."""
    if getattr(sys, 'frozen', False):
        # Path cuando la aplicación está empaquetada con PyInstaller
        return sys._MEIPASS
    else:
        # Path de desarrollo: directorio donde se encuentra este script
        return os.path.dirname(os.path.abspath(__file__))

def ensure_directory(path):
    """Asegurar que el directorio existe, si no, crearlo."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"Directorio creado: {path}")

base_path = get_base_path()

# Rutas relativas, usando base_path para construir las rutas completas
folder_path = os.path.join(base_path, 'columnas_actualizado')
root_db_cu = os.path.join(base_path, 'data_cuIL.xlsx')
root_graficas = os.path.join(base_path, 'graficas_columnas')

# Asegurar que los directorios para los datos y gráficas existan
ensure_directory(folder_path)  # Específicamente importante para cambios de usuario
ensure_directory(root_graficas)  # Para guardar gráficas generadas

# No es necesario crear directorio para root_db_cu ya que es un archivo,
# pero deberías asegurar que el archivo exista si tu aplicación depende de él al iniciar.

