from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from data_processing import ExcelReader, MetallurgicalProcess

# Crear la aplicación Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Permitir solicitudes CORS

# Configuración de la carpeta para guardar archivos subidos
UPLOAD_FOLDER = './temp_files'
ALLOWED_EXTENSIONS = {'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear la carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Variable global para almacenar df_final
df_final = None

# Verificar que los archivos tienen extensiones permitidas
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta principal para cargar la página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar la subida y procesamiento de archivos
@app.route('/upload', methods=['POST'])
def upload_files():
    """Procesar los archivos enviados desde el frontend."""
    global df_final  # Hacer que df_final sea accesible en todo el programa

    if 'files' not in request.files:
        return jsonify({'error': 'No se encontraron archivos en la solicitud'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No se seleccionaron archivos para cargar'}), 400

    # Guardar los archivos en la carpeta temporal
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            saved_files.append(file_path)
            print(f"Archivo guardado: {file_path}")

    if not saved_files:
        print("No se guardaron archivos válidos.")
        return jsonify({'error': 'No se encontraron archivos válidos para procesar'}), 400

    # Procesar los archivos
    try:
        excel_reader = ExcelReader(app.config['UPLOAD_FOLDER'])
        dfs = excel_reader.read_excel_files()
        parameters = excel_reader.calculate_parameters()

        metallurgical_process = MetallurgicalProcess(
            df=dfs,
            parameters=parameters,
            Raffinate_Density=1.04,
            PLS_Density=0
        )
        df_final = metallurgical_process.consolidado()
        df_final = df_final.reset_index(drop=True)
        df_final = df_final.loc[:, ~df_final.columns.duplicated()]

        if df_final.empty:
            return jsonify({'error': 'No se generaron datos procesados'}), 400

        result_json = df_final.to_json(orient="records")
        return jsonify({'data': result_json})

    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
        return jsonify({'error': 'Error al procesar los archivos', 'details': str(e)}), 500
        
@app.route('/get_columns', methods=['GET'])
def get_columns():
    global df_final  # Hacer que df_final sea accesible en esta ruta
    try:
        if df_final is None:
            return jsonify({'error': 'No se han procesado archivos aún'}), 400

        unique_columns = df_final['columna'].unique().tolist()  # Obtén valores únicos
        return jsonify({'columns': unique_columns})  # Devuelve los valores como JSON
    except Exception as e:
        print(f"Error al obtener las columnas: {e}")
        return jsonify({'error': 'No se pudo obtener las columnas', 'details': str(e)}), 500

# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True, port=5001)
