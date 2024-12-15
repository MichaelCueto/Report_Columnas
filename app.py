from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import pandas as pd
from data_processing import ExcelReader, MetallurgicalProcess

# Crear la aplicación Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Permitir solicitudes CORS

# Variable global para almacenar df_final
df_final = None

@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar la subida y procesamiento de archivos
@app.route('/upload', methods=['POST'])
def upload_files():
    global df_final

    data = request.get_json()
    folder_data = data.get('folderData', [])

    if not folder_data:
        return jsonify({'error': 'No se seleccionaron archivos o carpeta no válida'}), 400

    try:
        # Procesar los archivos con ExcelReader
        folder_path = os.path.commonpath([file['relativePath'] for file in folder_data])
        excel_reader = ExcelReader(folder_path)
        dfs = excel_reader.read_excel_files()
        parameters = excel_reader.calculate_parameters()

        metallurgical_process = MetallurgicalProcess(
            df=dfs,
            parameters=parameters,
            Raffinate_Density=1.04,
            PLS_Density=0
        )
        df_final = metallurgical_process.consolidado()

        # Validar y procesar df_final
        if df_final.empty:
            return jsonify({'error': 'No se generaron datos procesados'}), 400

        df_final = df_final.reset_index(drop=True)
        df_final = df_final.loc[:, ~df_final.columns.duplicated()]

        # Convertir la columna "fecha" a tipo datetime si existe
        if 'fecha' in df_final.columns:
            df_final['fecha'] = pd.to_datetime(df_final['fecha'], unit='ms', errors='coerce')
            df_final['fecha'] = df_final['fecha'].dt.strftime('%d/%m/%Y')

        result_json = df_final.to_json(orient="records")
        return jsonify({'data': result_json})

    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
        return jsonify({'error': 'Error al procesar los archivos', 'details': str(e)}), 500

# Ruta para obtener las columnas únicas
@app.route('/get_columns', methods=['GET'])
def get_columns():
    global df_final
    try:
        if df_final is None:
            return jsonify({'error': 'No se han procesado archivos aún'}), 400

        unique_columns = df_final['columna'].unique().tolist()
        features = df_final.columns.tolist()
        return jsonify({'columns': unique_columns, 'features': features})

    except Exception as e:
        print(f"Error al obtener las columnas: {e}")
        return jsonify({'error': 'Error al obtener las columnas', 'details': str(e)}), 500

# Ruta para devolver datos filtrados
@app.route('/get_filtered_data', methods=['POST'])
def get_filtered_data():
    global df_final
    try:
        if df_final is None:
            return jsonify({'error': 'No se han procesado datos aún'}), 400

        data = request.get_json()
        selected_columns = data.get('columns', [])
        variable_x = data.get('variableX', 'dias')
        variable_y = data.get('variableY', 'Ext%Cu_IL')

        if not selected_columns:
            return jsonify({'error': 'No se seleccionaron columnas'}), 400

        print(f"Columnas seleccionadas: {selected_columns}")
        print(f"Variable X: {variable_x}, Variable Y: {variable_y}")

        # Validar si las columnas seleccionadas existen
        if 'columna' not in df_final.columns:
            return jsonify({'error': "La columna 'columna' no existe en los datos procesados."}), 400

        # Filtrar el DataFrame
        filtered_df = df_final[df_final['columna'].isin(selected_columns)]

        if filtered_df.empty:
            return jsonify({'error': 'No hay datos para los valores seleccionados'}), 400

        # Validar si las variables X e Y existen en el DataFrame
        if variable_x not in filtered_df.columns or variable_y not in filtered_df.columns:
            return jsonify({'error': f"Las columnas seleccionadas para X ({variable_x}) o Y ({variable_y}) no existen en los datos procesados."}), 400

        # Preparar datos para el gráfico
        scatter_data = {
            'x': filtered_df[variable_x].tolist(),
            'y': filtered_df[variable_y].tolist(),
            'label': filtered_df['columna'].tolist()
        }

        return jsonify(scatter_data)
    except Exception as e:
        print(f"Error al filtrar datos: {e}")
        return jsonify({'error': 'Error al filtrar datos', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)