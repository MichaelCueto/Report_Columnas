import os
import logging
import pandas as pd
from data_processing import ExcelReader, MetallurgicalProcess
from create_graphics import graphics
from create_ppt import PowerPointGenerator
from curvas_cineticas import curvas_cineticas
from params import list_column, list_enr, list_mixto
from roots import root_db_cu

def run_process(folder_path):
    logging.basicConfig(level=logging.DEBUG, filename='process.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logging.info(f'Carpeta de trabajo proporcionada: {folder_path}')
        
        # Leer archivos Excel
        logging.info('Iniciando la lectura de archivos Excel.')
        excel_reader = ExcelReader(folder_path=folder_path)
        dfs, new_names_columns = excel_reader.read_excel_files()
        logging.info(f'Se leyeron los archivos Excel con nombres de columnas: {new_names_columns}')
        
        # Calcular parámetros
        logging.info('Iniciando el cálculo de parámetros.')
        parameters = excel_reader.calculate_parameters()
        logging.info('Parámetros calculados correctamente.')
        
        # Procesar datos
        logging.info('Iniciando el procesamiento de datos.')
        process = MetallurgicalProcess(
            df=dfs,
            parameters=parameters,
            Raffinate_Density=1.04,
            PLS_Density=0,
            root_db_cu=root_db_cu,
            equivalencias=new_names_columns,
            tiempo_prueba=70
        )
        
        logging.info('Calculando consolidado y constantes de cinética.')
        df_consolidado, df_coeficientes, df_resumen_parametros, df_resumen_modelo_doble, df_resumen_modelo_exponencial, df_resumen_total, df_cluster = process.consolidado()
        logging.info('Consolidado y constantes de cinética calculados correctamente.')

        # Filtrar datos
        logging.info('Aplicando filtro en el consolidado para eliminar filas con valores nulos en Cu_refino_g/kg.')
        df_consolidado = df_consolidado.dropna(subset=['Cu_refino_g/kg'])
        logging.info('Filtro aplicado correctamente.')
        
        data_cu_resumen = process.resumen_cu()
        
        # Validar la existencia de 'data_cuIL.xlsx'
        logging.info('Buscando el archivo data_cuIL.xlsx.')
        base_folder_path = os.path.dirname(folder_path)
        data_cuIL_path = os.path.join(base_folder_path, 'data_cuIL.xlsx')
        if not os.path.exists(data_cuIL_path):
            raise FileNotFoundError(f'El archivo data_cuIL.xlsx no se encontró en la ruta {base_folder_path}')
        
        logging.info('El archivo data_cuIL.xlsx fue encontrado.')

        # Guardar resultados en un archivo Excel
        output_folder = os.path.dirname(data_cuIL_path)
        output_file = 'Consolidado.xlsx'
        output_path = os.path.join(output_folder, output_file)
        logging.info(f'Guardando resultados en el archivo Excel: {output_path}')
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_consolidado.to_excel(writer, sheet_name='Consolidado', index=False)
            df_coeficientes.to_excel(writer, sheet_name='Coeficientes', index=False)
            df_resumen_parametros.to_excel(writer, sheet_name='Resumen_Parametros', index=True)
            df_resumen_total.to_excel(writer, sheet_name='Caracterizacion_Quimica', index=False)
            df_resumen_modelo_doble.to_excel(writer, sheet_name='Modelo 1', index=False)
            df_resumen_modelo_exponencial.to_excel(writer, sheet_name='Modelo 2', index=False)
        logging.info('Resultados guardados en el archivo Excel correctamente.')

        # Generar gráficas de las cinéticas
        logging.info('Generando gráficas de curvas cinéticas para Modelo 1 y Modelo 2.')
        cineticas1 = curvas_cineticas(file=output_file, sheet='Modelo 1')
        cineticas1.curvas(sheet_graphs_name='Graficas_Recuperacion')
        logging.info('Gráficas de recuperación generadas correctamente para Modelo 1.')
        
        cineticas2 = curvas_cineticas(file=output_file, sheet='Modelo 2')
        cineticas2.curvas(sheet_graphs_name='Graficas_Acido')
        logging.info('Gráficas de ácido generadas correctamente para Modelo 2.')

        # Generar gráficos adicionales
        graficas_folder = os.path.join(base_folder_path, 'graficas_columnas')
        if not os.path.exists(graficas_folder):
            os.makedirs(graficas_folder)
        logging.info(f'Generando gráficos adicionales en la carpeta: {graficas_folder}')
        
        graficas = graphics(df=df_consolidado, list_column=list_column, list_enr=list_enr, list_mixto=list_mixto, root_graficas=graficas_folder)
        graficas.gruops()
        logging.info('Gráficos adicionales generados correctamente.')

        # Generar presentación PPT
        logging.info('Generando presentación en PowerPoint.')
        ppt_generator = PowerPointGenerator(graficas_folder)
        ppt_generator.generar_presentacion(total_grupos=11, output_name='Presentación_columnas.pptx')
        logging.info('Presentación generada exitosamente en formato PowerPoint.')
        
        return df_consolidado

    except Exception as e:
        logging.error(f'Error en el proceso: {e}', exc_info=True)
        print(f'Error en el proceso: {e}')
