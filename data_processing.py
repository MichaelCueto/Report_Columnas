import pandas as pd
import numpy as np
import math
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
import os
from plotnine import*
#import openpyxl

import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score,mean_squared_error
from openpyxl import load_workbook
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
from plotly.subplots import make_subplots
import re
# Ignorar todas las advertencias
warnings.filterwarnings("ignore")

class ExcelReader:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def read_excel_files(self):
        file_names = [f for f in os.listdir(self.folder_path) if f.endswith('.xlsx')]
        patterns = [
            (r'18513 - Enriquecido TCS - (\d{3}) 1M-', r'TCS \1'),
            (r'18513 - Enriquecido TCC - (\d{3}) 8M-', r'TCC \1'),
            (r'18513 - Mixto TCS - (\d{3}) 1M-', r'TCS \1'),
            (r'18513 - Transicional TCS - (\d{3}) 1M-', r'TCS \1'),
            (r'18513 Composito Enriquecido TBCE-(\d{2}) 1M -', r'TBCE\1 OP Enriquecido'),
            (r'18513 Composito Mixto TBCM-(\d{2}) 1M -', r'TBCM\1 OP Mixto'),
            (r'18513 Composito GEOTECNIA', r'Geotecnia - ROM3'),
            (r'18513 Composito ROM (\d{1}) -', r'ROM\1'),
            (r'TBC(\d{3})', r'TBC \1'),
            (r'TBC(\d{3}) - D', r'TBC \1 - D'),
            (r'TBC(\d{3}) - 3D', r'TBC \1 - 3D')
        ]
        converted_names = {}
        dfs = []
        for file_name in file_names:
            # Quitar la extensión .xlsx
            file_name_no_ext = os.path.splitext(file_name)[0]
            original_name = file_name_no_ext
            for pattern, replacement in patterns:
                file_name_no_ext = re.sub(pattern, replacement, file_name_no_ext)
            # Eliminar ceros a la izquierda en los números después de 'TCS ' o 'TBCM'
            file_name_no_ext = re.sub(r'TCS 0*', 'TCS ', file_name_no_ext)
            file_name_no_ext = re.sub(r'TCC 0*', 'TCC ', file_name_no_ext)
            file_name_no_ext = re.sub(r'TBC 0*', 'TBC ', file_name_no_ext)
            file_name_no_ext = re.sub(r'TBCM0*', 'TBCM', file_name_no_ext)
            converted_names[original_name] = file_name_no_ext 
            df = self.read_single_excel(os.path.join(self.folder_path,file_name))
            df['Nombre del Archivo'] = file_name_no_ext
            dfs.append(df)
        return dfs,converted_names

    def read_single_excel(self, file_path):
        try:
            # Determinar la hoja según el nombre del archivo
            if 'enriquecido' in file_path.lower():
                sheet_name = 'ENRIQUECIDO'
            elif 'transicional' in file_path.lower():
                sheet_name = 'TRANSICIONAL'
            elif 'mixto' in file_path.lower():
                sheet_name = 'MIXTO'
            else:
                sheet_name = 'COLUMNA'
            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=28, usecols='C:Z')
            last_row_col_5 = df[df.iloc[:, 6].notna()].index[-1]
            last_row_col_8 = df[df.iloc[:, 7].notna()].index[-1]
            last_row = max(last_row_col_5, last_row_col_8)
            df =  df.iloc[:last_row + 1]
            df1 = df.drop(df.columns[2], axis=1)
            df1 = df1.fillna(0)
            inicio_df = df1.index[0]
            df0 = df.head(inicio_df)
            df0 = df0.drop(df0.columns[2], axis=1)
            df_concatenado = pd.concat([df0, df1], axis=0)
            df_concatenado.columns = ['Tiempo', 'Fecha', 'Día', 'Peso(g)_PLS', 'ÁcidoLibre(g/Kg)_PLS', 'pH_PLS', 'ORP(mV)_PLS', 'Temp_PLS', 'Temp_Amb_PLS', 'Temp_Column_PLS', 'Cu(g/Kg)_PLS',
                                      'Fe(g/Kg)_PLS', 'Fe+2(g/Kg)_PLS', 'Extraccion_Cu%', 'H2SO4_Total(Kg/T)', 'Peso(g)_Feed', 'ÁcidoLibre(g/Kg)_Feed', 'pH_Feed', 'ORP(mV)_Feed', 'Acido_ingresa(g)',
                                      'Cu(g/Kg)_Feed', 'Fe(g/Kg)_Feed', 'Fe+2(g/Kg)_Feed']
            df_concatenado['Nombre del Archivo'] = os.path.basename(file_path)
            return df_concatenado
        except Exception as e:
            print(f"Error al procesar el archivo {file_path}: {e}")
            return None
        
    def calculate_parameters(self):
        results = []
        file_names = [f for f in os.listdir(self.folder_path) if f.endswith('.xlsx')]
        for file_name in file_names:
            file_path = os.path.join(self.folder_path, file_name)
            try:
                if 'enriquecido' in file_name.lower():
                    sheet_name = 'ENRIQUECIDO'
                elif 'transicional' in file_name.lower():
                    sheet_name = 'TRANSICIONAL'
                elif 'mixto' in file_name.lower():
                    sheet_name = 'MIXTO'
                else:
                    sheet_name = 'COLUMNA'
                dry_column_charge = float(load_workbook(file_path)[sheet_name]['AI51'].value)
                column_size = load_workbook(file_path)[sheet_name]['D13'].value
                peso_inicial = float(load_workbook(file_path)['Mineral']['L16'].value)
                values = load_workbook(file_path)['Mineral']['J24'].value.split(',')
                cu_inicial = float(values[0].split('=')[-1].strip().split()[0])
                #Acido = float(values[1].split('=')[-1].strip().split()[0])
                fe_total_inicial = float(values[2].split('=')[-1].strip().split()[0])
                fe_2_inicial = float(values[3].split('=')[-1].strip().split()[0])
                h2so4_inicial = float(load_workbook(file_path)['Mineral']['L29'].value)
                altura_inicial_mineral = load_workbook(file_path)[sheet_name]['AI53'].value
                cu_total = load_workbook(file_path)[sheet_name]['AG35'].value
                fe_total = load_workbook(file_path)[sheet_name]['AH35'].value
                cu_acido = load_workbook(file_path)[sheet_name]['AJ35'].value
                cu_cn = load_workbook(file_path)[sheet_name]['AK35'].value
                cu_residual = load_workbook(file_path)[sheet_name]['AL35'].value
                material_moisture = load_workbook(file_path)[sheet_name]['AI39'].value
                results.append((dry_column_charge,column_size,peso_inicial,cu_inicial,h2so4_inicial,fe_total_inicial,fe_2_inicial,altura_inicial_mineral, cu_total, fe_total,cu_acido,cu_cn,cu_residual, material_moisture))
            except Exception as e:
                print(f"Error al extraer los parametros {file_name}: {e}")
                results.append((None, None, None, None, None, None, None, None, None, None,None,None,None, None))
        return results
    
class MetallurgicalProcess:
    def __init__(self,df, parameters,Raffinate_Density,PLS_Density,root_db_cu,equivalencias,tiempo_prueba):
        self.df = df
        self.parameters = parameters
        self.Raffinate_Density = Raffinate_Density
        self.PLS_Density = PLS_Density
        self.db_cu = pd.read_excel(root_db_cu)
        self.equivalencias = equivalencias
        self.tiempo_prueba = tiempo_prueba
    def area_column(self,column_size):
        db_area = {
        'Column_Size': ['4"X8 m', '6"X6 m', '6"X1 m', '6"X3 m', '8"X1 m','8"X4 m','8"X6 m','3mX6 m','8"X8 m','8"X10 m','8"X12 m','8"X16 m','8"X20 m',
                '8"X24 m','8"X30 m','12"X3 m','30"X3 m','1mX10 m','4mX5 m', '6mX1 m'],
        'Column_Diameter(in)': [4.0, 6.0, 6.0, 6.0, 8.0, 8.0 ,8.0, 118.1, 8.0 ,8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 12.0, 30.0, 39.4, 157.5, 236.2]}
        df_area = pd.DataFrame(db_area)
        df_area['Column_Area(m2)'] = math.pi*0.25*(df_area['Column_Diameter(in)']*2.54*0.01)**2
        columna_buscada = 'Column_Size' 
        fila_dato = df_area[df_area[columna_buscada] == column_size].index[0]
        Column_Area = df_area.iloc[fila_dato]['Column_Area(m2)']
        return Column_Area

    def process(self):
        dfs1 = []
        dfs2 = []
        dfs3 = []
        dfs4 = []
        dfs5 = []
        dfs6 = []
        dfs7 = []
        for df, params in zip(self.df, self.parameters):
            try:
                (dry_column_charge, column_size, peso_inicial, cu_inicial, h2so4_inicial, fe_total_inicial, fe_2_inicial, altura_inicial_mineral, cu_total, fe_total, cu_acido,cu_cn, cu_residual,material_moisture) = params
                fe_3_inicial = fe_total_inicial - fe_2_inicial
                #reffinate
                df_feed = df[['Nombre del Archivo','Fecha','Día','Peso(g)_Feed','Cu(g/Kg)_Feed','ÁcidoLibre(g/Kg)_Feed','Fe(g/Kg)_Feed',
                'Fe+2(g/Kg)_Feed','ORP(mV)_Feed','pH_Feed']].fillna(0)
                df_feed['Día'] = pd.to_numeric(df_feed['Día'], errors='coerce')
                df_feed['Fecha'] = pd.to_datetime(df_feed['Fecha'])
                df_feed['Nombre del Archivo'] = df_feed['Nombre del Archivo'].str.replace('.xlsm','')
                df_feed['Feedin_Ratio(g/g)'] = (df_feed['Peso(g)_Feed'].cumsum()) / (dry_column_charge * 1000)
                df_feed['Actual_Rate(Kg/hm2)'] = (df_feed['Peso(g)_Feed'].cumsum()) / (1000 * df_feed['Día'] * 24 * self.area_column(column_size))
                df_feed['Fe+3(g/Kg)_Feed'] = df_feed['Fe(g/Kg)_Feed'] - df_feed['Fe+2(g/Kg)_Feed']
                df_feed['Peso(g)_Feed'].iloc[0] = peso_inicial
                df_feed['Cu(g/Kg)_Feed'].iloc[0] = cu_inicial
                df_feed['ÁcidoLibre(g/Kg)_Feed'][0] = h2so4_inicial
                df_feed['Fe(g/Kg)_Feed'].iloc[0] = fe_total_inicial
                df_feed['Fe+2(g/Kg)_Feed'].iloc[0] = fe_2_inicial
                df_feed['Fe+3(g/Kg)_Feed'].iloc[0] = fe_3_inicial
            except Exception as e:
                print(f"Error en el archivo {df['Nombre del Archivo'].iloc[0]}:{e}")
                continue

            #pls 
            df_pls = df[['Peso(g)_PLS','Cu(g/Kg)_PLS','ÁcidoLibre(g/Kg)_PLS','Fe(g/Kg)_PLS','Fe+2(g/Kg)_PLS','ORP(mV)_PLS','pH_PLS']].fillna(0)
            df_pls['pH_PLS'] = pd.to_numeric(df_pls['pH_PLS'], errors='coerce')
            df_pls['Feedin_Ratio(g/g)_pls'] = (df_pls['Peso(g)_PLS'].cumsum())/(dry_column_charge*1000)
            df_pls['Actual_Rate(Kg/hm2)'] = (df_pls['Peso(g)_PLS'].cumsum())/(1000*df_feed['Día']*24*self.area_column(column_size))
            df_pls['Fe+3(g/Kg)_PLS'] = df_pls['Fe(g/Kg)_PLS'] - df_pls['Fe+2(g/Kg)_PLS']
            df_pls['Cu_Neto(g/Kg)_PLS'] = df_pls['Cu(g/Kg)_PLS'] - df_feed['Cu(g/Kg)_Feed']

            #others
            num_rows = len(df_pls)
            df_others = pd.DataFrame(index=range(num_rows))
            Free_Column_Height = [(int(column_size[:1]) - altura_inicial_mineral) * 100 if i == 0 else 0 for i in range(num_rows)]
            df_others['Raffinate_Density'] = self.Raffinate_Density
            df_others['PLS_Density'] = self.PLS_Density
            df_others['Free_Column_Height'] = Free_Column_Height
            df_others['Cumulated Compaction'] = df_others['Free_Column_Height'].cumsum()
            df_others['Cumulated Compaction'][1:] = df_others['Cumulated Compaction'][1:] - df_others['Cumulated Compaction'][1]
            df_others['Cumulated Compaction'][0] = 0
            df_others

            #raffinate_calculations
            Cu_feed_incial = cu_inicial*peso_inicial/1000
            H2SO4_feed_inicial = dry_column_charge*h2so4_inicial
            Added_H2SO4_Cumulated_inicial = H2SO4_feed_inicial/dry_column_charge
            Fe_Total_feed_inicial = fe_total_inicial*peso_inicial/1000
            Fe_2_feed_inicial = fe_2_inicial*peso_inicial/1000
            Fe_3_feed_inicial = Fe_Total_feed_inicial - Fe_2_feed_inicial
            Added_Fe_3_Cumulated_inicial = Fe_3_feed_inicial/dry_column_charge
            if fe_total_inicial == 0:
                Fe3_Fe2_inicial = 0
            else:
                Fe3_Fe2_inicial = fe_3_inicial/fe_2_inicial

            if fe_total_inicial == 0:
                Fe2_FeT_inicial = 0
            else:
                Fe2_FeT_inicial = fe_2_inicial/fe_total_inicial
            Added_FeT_Cumulated_inicial =  Fe_Total_feed_inicial/dry_column_charge
            df_feed_calc = pd.DataFrame()
            df_feed_calc['Cu(g)'] = df_feed['Peso(g)_Feed']*df_feed['Cu(g/Kg)_Feed']/1000
            df_feed_calc['Cu(g)'][0] = Cu_feed_incial

            df_feed_calc['H2SO4(g)'] = df_feed['Peso(g)_Feed']*df_feed['ÁcidoLibre(g/Kg)_Feed']/1000
            df_feed_calc['H2SO4(g)'][0] = H2SO4_feed_inicial

            df_feed_calc['Added_H2SO4_Cumulated(Kg/Tn)'] = (df_feed_calc['H2SO4(g)'].cumsum() + H2SO4_feed_inicial)/dry_column_charge
            df_feed_calc['Added_H2SO4_Cumulated(Kg/Tn)'][0] = Added_H2SO4_Cumulated_inicial

            df_feed_calc['Fe_Total(g)'] = df_feed['Peso(g)_Feed']*df_feed['Fe(g/Kg)_Feed']/1000
            df_feed_calc['Fe_Total(g)'][0] = Fe_Total_feed_inicial

            df_feed_calc['Fe+2(g)'] = df_feed['Peso(g)_Feed']*df_feed['Fe+2(g/Kg)_Feed']/1000
            df_feed_calc['Fe+2(g)'][0] = Fe_2_feed_inicial

            df_feed_calc['Fe+3(g)'] = df_feed['Peso(g)_Feed']*df_feed['Fe+3(g/Kg)_Feed']/1000
            df_feed_calc['Fe+3(g)'][0] = Fe_3_feed_inicial

            df_feed_calc['AAdded_Fe+3_Cumulated(Kg/Tn)'] = (df_feed_calc['Fe+3(g)'].cumsum() + Fe_3_feed_inicial)/dry_column_charge
            df_feed_calc['AAdded_Fe+3_Cumulated(Kg/Tn)'][0] = Added_Fe_3_Cumulated_inicial

            df_feed_calc['Fe+3/Fe+2'] = (df_feed['Fe+3(g/Kg)_Feed']/df_feed['Fe+2(g/Kg)_Feed']).fillna(0)
            df_feed_calc['Fe+3/Fe+2'][0] = Fe3_Fe2_inicial

            if (df_feed['Peso(g)_Feed'] == 0).all():
                df_feed_calc['Fe+2/FeT'] = 0
            else:
                condicion = (df_feed['Fe+2(g/Kg)_Feed'] <= 0) | (df_feed['Fe+2(g/Kg)_Feed'] > df_feed['Fe(g/Kg)_Feed'])
                df_feed_calc['Fe+2/FeT'] = pd.Series(index=df_feed.index)
                df_feed_calc.loc[condicion, 'Fe+2/FeT'] = 0
                df_feed_calc.loc[~condicion, 'Fe+2/FeT'] = df_feed.loc[~condicion, 'Fe+2(g/Kg)_Feed'] / df_feed.loc[~condicion, 'Fe(g/Kg)_Feed']
            df_feed_calc['Fe+2/FeT'][0] = Fe2_FeT_inicial

            df_feed_calc['Added_FeT_Cumulated(Kg/Tn)'] = (df_feed_calc['Fe_Total(g)'].cumsum() + Fe_Total_feed_inicial)/dry_column_charge
            df_feed_calc['Added_FeT_Cumulated(Kg/Tn)'][0] = Added_FeT_Cumulated_inicial

            #pls calculations
            df_pls_calc = pd.DataFrame()
            df_pls_calc['Cu(g)_pls'] = df_pls['Peso(g)_PLS']*df_pls['Cu(g/Kg)_PLS']/1000
            df_pls_calc['pH*Liters_pls'] = df_pls['Peso(g)_PLS']*df_pls['pH_PLS']
            df_pls_calc['H2SO4(g)_pls'] = df_pls['Peso(g)_PLS']*df_pls['ÁcidoLibre(g/Kg)_PLS']/1000
            df_pls_calc['Fe_Total(g)_pls'] = df_pls['Peso(g)_PLS']*df_pls['Fe(g/Kg)_PLS']/1000
            df_pls_calc['Fe+2(g)_pls'] = df_pls['Peso(g)_PLS']*df_pls['Fe+2(g/Kg)_PLS']/1000
            df_pls_calc['Fe+3(g)_pls'] = df_pls['Peso(g)_PLS']*df_pls['Fe+3(g/Kg)_PLS']/1000
            df_pls_calc['Cu/FeT_pls'] = (df_pls['Cu(g/Kg)_PLS']/df_pls['Fe(g/Kg)_PLS']).fillna(0)
            df_pls_calc['Cu/Fe+2_pls'] = (df_pls['Cu(g/Kg)_PLS']/df_pls['Fe+2(g/Kg)_PLS']).fillna(0)

            condicion_1 = (df_pls['Peso(g)_PLS'] == 0) | (df_pls['Fe+2(g/Kg)_PLS'] > df_pls['Fe(g/Kg)_PLS'])
            df_pls_calc['Fe+3/Fe+2_pls'] = pd.Series(index=df_pls.index)
            df_pls_calc.loc[condicion_1, 'Fe+3/Fe+2_pls'] = 0
            df_pls_calc.loc[~condicion_1, 'Fe+3/Fe+2_pls'] = df_pls.loc[~condicion_1, 'Fe+3(g/Kg)_PLS'] / df_pls.loc[~condicion_1, 'Fe+2(g/Kg)_PLS']

            condicion_2 = (df_pls['Peso(g)_PLS'] == 0) | (df_pls['Fe+2(g/Kg)_PLS'] > df_pls['Fe(g/Kg)_PLS'])
            df_pls_calc['Fe+2/Fe_pls'] = pd.Series(index=df_pls.index)
            df_pls_calc.loc[condicion_2, 'Fe+2/Fe_pls'] = 0
            df_pls_calc.loc[~condicion_2, 'Fe+2/Fe_pls'] = df_pls.loc[~condicion_2, 'Fe+2(g/Kg)_PLS'] / df_pls.loc[~condicion_2, 'Fe(g/Kg)_PLS']

            #element balance
            df_eb = pd.DataFrame()
            if (df_pls_calc['Cu(g)_pls'] == 0).all():
                df_eb['Leached_Cu_day(g)'] = -1*df_feed_calc['Cu(g)']
            else:
                df_eb['Leached_Cu_day(g)'] =  df_pls_calc['Cu(g)_pls'] - df_feed_calc['Cu(g)']
            df_eb['Leached_Cu_day(g)'][0] = 0
            df_eb['Leached_Cu_cumulated(g)'] = df_eb['Leached_Cu_day(g)'].cumsum()
            df_eb['Leached_Cu_cumulated(mol)'] = df_eb['Leached_Cu_cumulated(g)']/63.55

            df_eb['Leached_Fe_day(g)'] = df_pls_calc['Fe_Total(g)_pls'] - df_feed_calc['Fe_Total(g)']
            df_eb['Leached_Fe_day(g)'][0] = 0
            df_eb['Leached_Fe_cumulated(g)'] = df_eb['Leached_Fe_day(g)'].cumsum()
            df_eb['Leached_Fe_cumulated(mol)'] = df_eb['Leached_Fe_cumulated(g)']/dry_column_charge

            if (df_pls_calc['Fe+2(g)_pls'] == 0).all():
                df_eb['Leached_Fe+2_day(g)'] = -1*df_feed_calc['Fe+2(g)']
            else:
                df_eb['Leached_Fe+2_day(g)'] =  df_pls_calc['Fe+2(g)_pls'] - df_feed_calc['Fe+2(g)']
            df_eb['Leached_Fe+2_cumulated(g)'] = df_eb['Leached_Fe+2_day(g)'].cumsum()

            if (df_pls_calc['Fe+3(g)_pls'] == 0).all():
                df_eb['Consumed_Fe+3_day(g)'] = df_feed_calc['Fe+3(g)']
            else:
                df_eb['Consumed_Fe+3_day(g)'] =  - df_pls_calc['Fe+3(g)_pls'] + df_feed_calc['Fe+3(g)']
            df_eb['Consumed_Fe+3_cumulated(g)'] = df_eb['Consumed_Fe+3_day(g)'].cumsum()
            df_eb['Consumed_Fe+3_cumulated(mole)'] = df_eb['Consumed_Fe+3_cumulated(g)']/55.85
            
            df_eb['Consumed_Fe+3_cumulated(Kg/Tn)'] = df_eb['Consumed_Fe+3_cumulated(g)']/dry_column_charge

            condicion_3 = (df_pls['Feedin_Ratio(g/g)_pls'] == 0)
            df_eb['Fe+3_Cu_cumulated(mole/mole)'] = pd.Series(index=df_pls.index)
            df_eb.loc[condicion_3, 'Fe+3_Cu_cumulated(mole/mole)'] = 0
            df_eb.loc[~condicion_3, 'Fe+3_Cu_cumulated(mole/mole)'] = df_eb.loc[~condicion_3, 'Consumed_Fe+3_cumulated(mole)'] / df_eb.loc[~condicion_3, 'Leached_Cu_cumulated(mol)']

            condicion_4 = (df_pls['Feedin_Ratio(g/g)_pls'] == 0)
            df_eb['Fe+3_Cu_cumulated(Kg/Kg)'] = pd.Series(index=df_pls.index)
            df_eb.loc[condicion_4, 'Fe+3_Cu_cumulated(Kg/Kg)'] = 0
            df_eb.loc[~condicion_4, 'Fe+3_Cu_cumulated(Kg/Kg)'] = df_eb.loc[~condicion_4, 'Consumed_Fe+3_cumulated(g)'] / df_eb.loc[~condicion_4, 'Leached_Cu_cumulated(g)']
            
            df_eb['Consumed_H2SO4_GroosDay(g)'] =  df_feed_calc['H2SO4(g)'] - df_pls_calc['H2SO4(g)_pls']
            df_eb['Consumed_H2SO4_GroosDay(g)'][0] = H2SO4_feed_inicial

            df_eb['Consumend_H2SO4_Eq_Acid_Day_Cu(g)'] = 1.54*df_eb['Leached_Cu_day(g)']
            df_eb['Consumend_H2SO4_Eq_Acid_Day_Fe(g)'] = 1.76*df_eb['Leached_Fe_day(g)']
            df_eb['Consumend_H2SO4_NextDay(g)'] = df_eb['Consumed_H2SO4_GroosDay(g)'] - df_eb['Consumend_H2SO4_Eq_Acid_Day_Cu(g)']

            df_eb['Consumed_H2SO4_GrossDay(Kg/Tn)'] = df_eb['Consumed_H2SO4_GroosDay(g)']/dry_column_charge
            df_eb['Consumed_H2SO4_Acid_Day_Cu(Kg/Tn)'] = df_eb['Consumend_H2SO4_Eq_Acid_Day_Cu(g)']/dry_column_charge
            df_eb['Consumed_H2SO4_Acid_Day_Fe(Kg/Tn)'] = df_eb['Consumend_H2SO4_Eq_Acid_Day_Fe(g)']/dry_column_charge
            df_eb['Consumed_H2SO4_NextDay(Kg)'] = df_eb['Consumend_H2SO4_NextDay(g)']/dry_column_charge

            #recovery
            Cu_Total_g = cu_total*dry_column_charge*1000/100
            Fe_Total_g = fe_total*dry_column_charge*1000/100
            df_rec = pd.DataFrame()
            df_rec['Partial(g/Kg)'] = ((df_pls['Peso(g)_PLS']*df_pls['Cu(g/Kg)_PLS']) - (df_feed['Peso(g)_Feed']*df_feed['Cu(g/Kg)_Feed']))/(dry_column_charge*1000)
            df_rec['Partial(g/Kg)'][0] = 0
            df_rec['Cumulated(g/Kg)'] = df_rec['Partial(g/Kg)'].cumsum()
            df_rec['Cumulated(%CuT)'] = (df_rec['Cumulated(g/Kg)']*100)/(10*cu_total)
            df_rec['Cumulated(g/Kg)'][0] = 0
            df_rec['Residue(%CuT)'] = (Cu_Total_g - df_eb['Leached_Cu_day(g)'].cumsum())/(10*dry_column_charge)
            df_rec['Residue(%CuT)'][0] = 0
            df_rec['Partial_FeT%'] = (df_eb['Leached_Fe_day(g)']/Fe_Total_g) *100
            df_rec['Partial_FeT%'][0] = 0
            
            condition = (df_pls['Feedin_Ratio(g/g)_pls'] == 0 )
            df_rec['Cumulated_FeT%'] = pd.Series(index=df_rec.index)
            df_rec.loc[condition,'Cumulated_FeT%'] = 0
            df_rec.loc[~condition,'Cumulated_FeT%'] = df_rec['Partial_FeT%'].cumsum()

            #ADICIONAL
            df_add = pd.DataFrame()
            df_add['KgFe+2/tms_ore'] = df_eb['Leached_Fe+2_cumulated(g)']/dry_column_charge
            df_add['Cu_extraido(Kg)'] =  df_eb['Leached_Cu_cumulated(g)']/1000
            df_add['Cu_adic_Ref(Kg)'] = df_feed_calc['Cu(g)']/1000
            df_add['Cu_acum_adic_Ref(Kg)'] = df_add['Cu_adic_Ref(Kg)'].cumsum()
            df_add['m3'] = (df_feed['Peso(g)_Feed'].iloc[1:].cumsum())/1000
            df_add['m3']= df_add['m3'].fillna(0)
            df_add['Cu_extraido(Kg/m3)'] = (df_add['Cu_extraido(Kg)']/df_add['m3']).fillna(0)

            condicion_5 = (df_add['Cu_extraido(Kg)'] == 0)
            df_add['Kg_Cu_extr/kg_Cu_ad(Kg/Kg)'] = pd.Series(index=df_add.index)
            df_add.loc[condicion_5, 'Kg_Cu_extr/kg_Cu_ad(Kg/Kg)'] = 0
            df_add.loc[~condicion_5, 'Kg_Cu_extr/kg_Cu_ad(Kg/Kg)'] = df_add.loc[~condicion_5, 'Cu_extraido(Kg)'] / df_add.loc[~condicion_5, 'Cu_acum_adic_Ref(Kg)']

            condicion_6 = (df_eb['Leached_Cu_day(g)']==0)
            df_add['KgCu_extr/dia(Kg)'] = pd.Series(index=df_add.index)
            df_add.loc[condicion_6,'KgCu_extr/dia(Kg)'] = df_add['KgCu_extr/dia(Kg)'].shift(1)
            df_add.loc[~condicion_6, 'KgCu_extr/dia(Kg)'] = df_eb.loc[~condicion_6, 'Leached_Cu_day(g)'] / 1000
            df_add['KgCu_extr/dia(Kg)'] = df_add['KgCu_extr/dia(Kg)'].fillna(0)
            
            if (df_feed['Feedin_Ratio(g/g)'] == 0).all():
                df_add['Raffinate_Fe+3/FeT'] = 0
            else:
                condicion_1 = df_feed['Fe+3(g/Kg)_Feed'] <= 0
                condicion_2 = df_feed['Fe+3(g/Kg)_Feed'] > df_feed['Fe(g/Kg)_Feed']
                df_add['Raffinate_Fe+3/FeT'] = np.where(condicion_1, 0, np.where(condicion_2, 0, df_feed['Fe+3(g/Kg)_Feed'] / df_feed['Fe(g/Kg)_Feed']))
            df_add['Raffinate_Fe+3/FeT'][0] = 0


            condicion_1 = df_pls['Feedin_Ratio(g/g)_pls'] == 0
            condicion_2 = df_pls['Fe+3(g/Kg)_PLS'] <= 0
            condicion_3 = df_pls['Fe+3(g/Kg)_PLS'] > df_pls['Fe(g/Kg)_PLS']

            df_add['pls_Fe+3/FeT'] = np.where(condicion_1, 0, np.where(condicion_2, 0, np.where(condicion_3, 1, df_pls['Fe+3(g/Kg)_PLS'] / df_pls['Fe(g/Kg)_PLS'])))

            condicion_7 = (df_feed['Fe+3(g/Kg)_Feed'] == 0)
            df_add['Fe+3pls/Fe+3ref'] = pd.Series(index=df_add.index)
            df_add.loc[condicion_7, 'Fe+3pls/Fe+3ref'] = 0
            df_add.loc[~condicion_7, 'Fe+3pls/Fe+3ref'] = df_pls.loc[~condicion_7, 'Fe+3(g/Kg)_PLS'] / df_feed.loc[~condicion_7, 'Fe+3(g/Kg)_Feed']

            #consumo de acido
            df_ac = pd.DataFrame()
            df_ac['Gross_Acid_Consumption(Kg/Tn)'] = df_eb['Consumed_H2SO4_GrossDay(Kg/Tn)'].cumsum()
            df_ac['Net_Acid_Consumption(Kg/Tn)'] = df_eb['Consumed_H2SO4_NextDay(Kg)'].cumsum()

            condition = (df_rec['Cumulated(%CuT)'] == 0)
            df_ac['Net_Acid_Consumption(Kg/KgCu)'] = pd.Series(index=df_rec.index)
            df_ac.loc[condition, 'Net_Acid_Consumption(Kg/KgCu)'] = 0
            df_ac.loc[~condition, 'Net_Acid_Consumption(Kg/KgCu)'] = df_ac.loc[~condition, 'Net_Acid_Consumption(Kg/Tn)'] / (cu_total * df_rec.loc[~condition, 'Cumulated(%CuT)']) * 10

            #VOLUME BALANCE
            df_vol = pd.DataFrame()
            condition = (df_pls['Feedin_Ratio(g/g)_pls'] == 0)
            df_vol['D/R Ratio'] = pd.Series(index=df_pls.index)
            df_vol.loc[condition, 'D/R Ratio'] = 0
            df_vol.loc[~condition, 'D/R Ratio'] = (df_pls.loc[~condition,'Peso(g)_PLS'].cumsum()) / (df_feed.loc[~condition,'Peso(g)_Feed'].cumsum())
            df_vol['Retained_Solution(%vol/vol)'] = (df_feed['Peso(g)_Feed'].cumsum() - df_pls['Peso(g)_PLS'].cumsum())/(df_feed['Peso(g)_Feed'].cumsum())*100
            df_vol['Retained_Solution(%vol/vol)'][0] = 0
            df_vol['Retained_Solution(g/Kg)']= (df_feed['Peso(g)_Feed'].cumsum() - df_pls['Peso(g)_PLS'].cumsum())/(dry_column_charge*1000)
            df_vol['Retained_Solution(g/Kg)'][0] = 0
            
            # condition = (df_feed['Peso(g)_Feed'] == 0)
            # df_vol['Dynamic_Moisture'] = pd.Series(index=df_pls.index)
            # df_vol['Dynamic_Moisture'][0] = 0
            # df_vol.loc[condition, 'Dynamic_Moisture'] = df_vol.loc[condition, 'Dynamic_Moisture'].shift(1)
            # df_vol.loc[~condition, 'Dynamic_Moisture'] = material_moisture + df_vol.loc[~condition, 'Retained_Solution(g/Kg)'] * df_others.loc[~condition, 'Raffinate_Density']
            # df_vol['Dynamic_Moisture'][0] = 0
            # df_vol['Dynamic_Moisture'] = df_vol['Dynamic_Moisture'].fillna(0)
            
            df_final_1 = pd.concat([df_feed,df_pls,df_others,df_rec,df_ac,df_eb,df_feed_calc,df_pls_calc,df_vol,df_add],axis=1)

            df_IL = pd.DataFrame()
            db = df_rec['Cumulated(%CuT)']
            df_IL['Ext%Cu_oxidos'] = (db*cu_total)/cu_acido
            df_IL['Ext%Cu_facil'] = (db*cu_total)/(cu_acido + 0.5*cu_cn)
            df_IL['Ext%Cu_IL'] = (db*cu_total)/(cu_acido + cu_cn)
            df_final_2 = pd.concat([df_final_1, df_IL], axis=1)
            df_final_2 = df_final_2.drop(df_final_2.index[0])
            #df_final_3 = df_final_3[['Nombre del Archivo','Día','Cumulated(%CuT)','Ext%Cu_facil','Ext%Cu_IL']]
            df_final_3 = df_final_2.copy()        

            def modelo_ajuste(df, columna_dias, columna_y, modelo):
                df = df[[columna_dias, columna_y]].dropna()
                yo = df[columna_y]
                xo = df[columna_dias]
                # Definir los modelos
                def modelo1_t(t, A1, A2, R1, R2):
                    return 100 * (A1 * (1 - (1 - A2)**(t - 3)) + R1 * (1 - (1 - R2)**(t - 3)))
                
                def modelo2_t(t, K1, K2, K3, n):
                    return np.where(t < 3, 0, K1 * (K2 * (1 - np.exp(-K3 * (t - 3)**n))))

                def modelo1_ac(ac, B1, B2, S1, S2):
                    return 100 * (B1 * (1 - (1 - B2)**(ac - ac_0)) + S1 * (1 - (1 - S2)**(ac - ac_0)))
                
                def modelo2_ac(ac, G1, G2, G3, n):
                    return np.where(ac < ac_0, 0,G1 * (G2 * (1 - np.exp(-G3 * (ac - ac_0)**n))))
                       

                if modelo == 'modelo1_t':
                    # Parámetros iniciales y límites para el primer modelo
                    initial_params = [1, 0.5, 1, 0.5]
                    param_bounds = ([0, 0, 0, 0], [np.inf, 1, np.inf, 1])

                    try:
                        params_restricted, params_covariance_restricted = curve_fit(
                            modelo1_t, xo, yo, p0=initial_params, bounds=param_bounds, maxfev=50000
                        )
                        A1, A2, R1, R2 = params_restricted
                        y_pred_restricted = modelo1_t(xo, A1, A2, R1, R2)
                        r2 = r2_score(yo, y_pred_restricted)
                        rmse = (mean_squared_error(yo, y_pred_restricted))
                        return A1, A2, R1, R2, r2,rmse, xo, yo
                    except RuntimeError as e:
                        print(f"Error in curve fitting: {e}")
                        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, xo, yo
                

                elif modelo == 'modelo2_t':
                    # Parámetros iniciales y límites para el tercer modelo
                    initial_params = [1, 1, 1, 1]
                    param_bounds = ([0, 0, 0, 0], [np.inf, np.inf, np.inf, np.inf])

                    try:
                        params_restricted, params_covariance_restricted = curve_fit(
                            modelo2_t, xo, yo, p0=initial_params, bounds=param_bounds, maxfev=60000
                        )
                        K1, K2, K3, n = params_restricted
                        y_pred_restricted = modelo2_t(xo, K1, K2, K3, n)
                        r2 = r2_score(yo, y_pred_restricted)
                        rmse = np.sqrt(mean_squared_error(yo, y_pred_restricted))
                        return K1, K2, K3, n, r2, rmse, xo, yo
                    
                    except RuntimeError as e:
                        print(f"Error in curve fitting: {e}")
                        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, xo, yo
                
                elif modelo == 'modelo1_ac':
                    # Parámetros iniciales y límites para el segundo modelo
                    initial_params = [1, 0.5, 1, 0.5]
                    param_bounds = ([0, 0, 0, 0], [np.inf, 1, np.inf, 1])

                    try:
                        params_restricted, params_covariance_restricted = curve_fit(
                            modelo1_ac, xo, yo, p0=initial_params, bounds=param_bounds, maxfev=50000
                        )
                        B1, B2, S1, S2 = params_restricted
                        y_pred_restricted = modelo1_ac(xo, B1, B2, S1, S2)
                        r2 = r2_score(yo, y_pred_restricted)
                        rmse = np.sqrt(mean_squared_error(yo, y_pred_restricted))
                        return B1, B2, S1, S2, r2,rmse, xo, yo
                    
                    except RuntimeError as e:
                        print(f"Error in curve fitting: {e}")
                        return np.nan, np.nan, np.nan, np.nan, np.nan,np.nan, xo, yo
                    
                elif modelo == 'modelo2_ac':
                    # Parámetros iniciales y límites para el segundo modelo
                    initial_params = [1, 1, 1, 1]
                    param_bounds = ([0, 0, 0, 0], [np.inf, np.inf, np.inf, np.inf])

                    try:
                        params_restricted, params_covariance_restricted = curve_fit(
                            modelo2_ac, xo, yo, p0=initial_params, bounds=param_bounds, maxfev=50000
                        )
                        G1, G2, G3, n = params_restricted
                        y_pred_restricted = modelo2_ac(xo, G1, G2, G3, n)
                        r2 = r2_score(yo, y_pred_restricted)
                        rmse = np.sqrt(mean_squared_error(yo, y_pred_restricted))
                        return G1, G2, G3, n, r2,rmse, xo, yo
                    
                    except RuntimeError as e:
                        print(f"Error in curve fitting: {e}")
                        return np.nan, np.nan, np.nan, np.nan, np.nan,np.nan, xo, yo

                else:
                    print("Modelo no reconocido")
                    return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, xo, yo
                        
            ac_0 = df_final_3['Added_H2SO4_Cumulated(Kg/Tn)'].min()

            #modelos Rec vs time
            A1,A2,R1,R2,r2_t1,rmse_t1,xo,yo = modelo_ajuste(df_final_3,'Día','Cumulated(%CuT)',modelo='modelo1_t')
            K1, K2, K3, n1, r2_t2, rmse_t2, xo, yo = modelo_ajuste(df_final_3, 'Día', 'Cumulated(%CuT)', modelo='modelo2_t')

            df_final_3['Ext%_Cu_model_t1'] = 100 * (A1 * (1 - (1 - A2)**(xo - 3)) + R1 * (1 - (1 - R2)**(xo - 3)))
            df_final_3['Ext%_Cu_model_t2'] = K1 * (K2 * (1 - np.exp(-K3 * (xo - 3)**n1)))

            #modelos Rec vs cons_acido
            B1,B2,S1,S2,r2_ac1,rmse_ac1,ac,yo = modelo_ajuste(df_final_3,'Added_H2SO4_Cumulated(Kg/Tn)', 'Cumulated(%CuT)', modelo='modelo1_ac')
            G1, G2, G3, n2,r2_ac2,rmse_ac2,ac,yo = modelo_ajuste(df_final_3, 'Added_H2SO4_Cumulated(Kg/Tn)', 'Cumulated(%CuT)', modelo='modelo2_ac')
        
            #df_final_3['ExtAcum_CuT_%_pred_2'] = df_final_3['ExtAcum_CuT_%_pred_2'].fillna(0)
            df_final_3['Ext%_Cu_model_ac1'] = 100 * (B1 * (1 - (1 - B2)**(ac - ac_0)) + S1 * (1 - (1 - S2)**(ac - ac_0)))
            df_final_3['Ext%_Cu_model_ac2'] = G1 * (G2 * (1 - np.exp(-G3 * (ac - ac_0)**n2)))

            db_1 = pd.DataFrame({
            'columna': [df_final_3['Nombre del Archivo'].iloc[0]],
            'dias_max_lixiviación' : xo.max(),
            'r2 modelo Rec vs Tiempo': [r2_t1],
            'error modelo Rec vs Tiempo':[rmse_t1],
            'A1': [A1],
            'A2': [A2],
            'R1': [R1],
            'R2': [R2],
            'r2 modelo Rec vs Tiempo 2': [r2_t2],
            'error modelo Rec vs Tiempo 2':[rmse_t2],
            'K1': [K1],
            'K2': [K2],
            'K3': [K3],
            'ac': [ac_0],
            'acido_consumido':ac.max(),
            'r2 modelo Rec vs acido': [r2_ac1],
            'error modelo Rec vs acido':[rmse_ac1],
            'B1': [B1],
            'B2': [B2],
            'S1': [S1],
            'S2': [S2],
            'r2 modelo Rec vs acido 2': [r2_ac2],
            'error modelo Rec vs acido 2':[rmse_ac2],
            'G1': [G1],
            'G2': [G2],
            'G3': [G3],
            'ac ': [ac_0],
            'CuS/CuT':cu_cn/cu_total,
            '% CuT': cu_total,
            'ley_cu':[cu_total],
            'cu_cn':cu_cn,
            'cu_acido':cu_acido,
            'cu_IL':cu_acido+cu_cn,
            })

            #formato pmh resumen
            df_cm = pd.DataFrame()
            df_cm['columna'] = df_final_3['Nombre del Archivo'].unique()
            #parte1
            df_cm['CuT (%)_calculado'] = [cu_acido + cu_acido + cu_residual]
            df_cm['CuT (%)_ensayado'] = [cu_total]
            df_cm['FeT (%)'] = [fe_total]
            df_cm['CuS (%)'] = [cu_acido]
            df_cm['CuCN (%)'] = [cu_cn]
            df_cm['CuRes (%)'] = [cu_residual]
            #parte2
            df_cm['Ley CuT, Kg/ton'] = df_cm['CuT (%)_ensayado'] * 10
            df_cm['Ley CuCN, Kg/ton'] = df_cm['CuCN (%)'] * 10
            df_cm['Ley CuS, Kg/ton'] = df_cm['CuS (%)'] * 10
            df_cm['Ley Res, Kg/ton'] = df_cm['CuRes (%)'] * 10
            #parte3
            df_cm['%CuS/CuT'] = (df_cm['CuS (%)']/df_cm['CuT (%)_ensayado'])*100
            df_cm['%CuRes/CuT'] = (df_cm['CuRes (%)']/df_cm['CuT (%)_ensayado'])*100
            df_cm['%CuCN/CuT'] = (df_cm['CuCN (%)']/df_cm['CuT (%)_ensayado'])*100
            #parte4
            df_cm['% Cu Total en función Cab Calculada'] = df_cm['%CuRes/CuT'] + df_cm['%CuS/CuT'] + df_cm['%CuCN/CuT']
            df_cm['% Índice lixiviabilidad'] = df_cm['%CuS/CuT'] + df_cm['%CuCN/CuT']
            df_cm['Recup Facil Bacterial'] = df_cm['%CuS/CuT'] + 0.5*df_cm['%CuCN/CuT']
            
            #parte5
            # crear función para tener los datos respecto o en función del numero de dias
            def dias_parametros(df,dias,dias_max=False):
                df['Día'] = pd.to_numeric(df['Día'], errors='coerce')  # Convierte la columna a numérica
                if dias_max == True:
                    dias = df['Día'].max()
                    df_cu_dias = df['Cumulated(%CuT)'].max()
                    df_fe_dias = df['Cumulated_FeT%'].max()
                    df_acido_dias = df['Net_Acid_Consumption(Kg/Tn)'].max()
                else:
                    if not df[df['Día']==dias].empty:
                        df_cu_dias = df.loc[df['Día']==dias,'Cumulated(%CuT)'].values[0]
                        df_fe_dias = df.loc[df['Día']==dias,'Cumulated_FeT%'].values[0]
                        df_acido_dias = df.loc[df['Día']==dias,'Net_Acid_Consumption(Kg/Tn)'].values[0]
                    else:
                        df_cu_dias = None
                        df_fe_dias = None
                        df_acido_dias = None
                return [dias], [df_cu_dias], [df_fe_dias], [df_acido_dias]

            df_cm['Dias de Lixiviación'], df_cm['Recup Cu del CuT, %'], df_cm['Recup Cu del FeT, %'],df_cm['Consumo Total de Acido'] = dias_parametros(df_final_3,dias=40,dias_max=None)
            #df_cm['Dias de Lixiviación'], df_cm['Recup Cu del CuT, %'], df_cm['Recup Cu del FeT, %'],df_cm['Consumo Total de Acido'] = dias_parametros(df_final_3,dias=None,dias_max=True)
            #parte 6
            df_cm['Recup CuT, kg/ton'] = df_cm['CuT (%)_ensayado']*df_cm['Recup Cu del CuT, %']*10/100
            df_cm['Recup Cu, kg/ton Sulfuros'] = df_cm['Recup CuT, kg/ton']-df_cm['CuS (%)']*10
            df_cm['Recup Cu Secundario del CuCN'] = df_cm['Recup Cu, kg/ton Sulfuros']*100/(df_cm['CuCN (%)']*10)
            df_cm['Recup Cu sulfuros del (CuCN+CuRes)'] = df_cm['Recup Cu, kg/ton Sulfuros']*100/(df_cm['CuCN (%)']*10 + df_cm['CuRes (%)']*10)
            df_cm['Falta recuperar del Cu Secundario'] = 100 - df_cm['Recup Cu Secundario del CuCN']
            df_cm['Falta recuperar de todos Sulfuros'] = 100 - df_cm['Recup Cu sulfuros del (CuCN+CuRes)']
            df_cm['Falta recuperar del Cu Secundario Kg/ton'] = df_cm['Recup Cu, kg/ton Sulfuros'] - df_cm['Ley CuCN, Kg/ton']
            df_cm['Recup Cu adicional sobre Facil Bacterial'] = df_cm['Recup Cu del CuT, %'] - df_cm['Recup Facil Bacterial']
            df_cm['Recup Cu del IL'] = (df_cm['Recup Cu del CuT, %']/df_cm['% Índice lixiviabilidad'])*100
            df_cm['Recup Cu Secundario del CuT'] = (df_cm['Recup Cu, kg/ton Sulfuros']/df_cm['Ley CuT, Kg/ton'])*100
            df_cm['Falta recuperar del Cu Secundario, %'] = df_cm['%CuCN/CuT'] - df_cm['Recup Cu Secundario del CuT']
            df_cm['Recup CuCN facil en Ac. Sulfurico, %'] = (df_cm['Recup Cu, kg/ton Sulfuros']/(0.5*df_cm['Ley CuCN, Kg/ton']))*100

            #formato resumen condiciones
            #solo enriquecidos
            #parte1 - caracterización quimica
            df_rc = pd.DataFrame()
            df_rc['columna'] = df_final_3['Nombre del Archivo'].unique()
            df_rc['CuT (%)_calculado'] = [cu_acido + cu_acido + cu_residual] 
            df_rc['CuT (%)_ensayado'] = [cu_total]
            df_rc['FeT (%)'] = [fe_total]
            df_rc['CuS (%)'] = [cu_acido]
            df_rc['CuCN (%)'] = [cu_cn]
            df_rc['CuRes (%)'] = [cu_residual]
            df_rc['%CuS/CuT'] = (df_rc['CuS (%)']/df_rc['CuT (%)_ensayado'])*100
            df_rc['%CuRes/CuT'] = (df_rc['CuRes (%)']/df_rc['CuT (%)_ensayado'])*100
            df_rc['%CuCN/CuT'] = (df_rc['CuCN (%)']/df_rc['CuT (%)_ensayado'])*100
            df_rc['% Cu Total en función Cab Calculada'] = df_rc['%CuS/CuT'] + df_rc['%CuRes/CuT'] + df_rc['%CuCN/CuT']
            df_rc['% Índice lixiviabilidad'] = df_rc['%CuS/CuT'] + df_rc['%CuCN/CuT']
            df_rc['Recup Facil Bacterial'] = df_rc['%CuS/CuT'] + 0.5*df_rc['%CuCN/CuT']

            #parte2 - Dias
            df_rcd1 = pd.DataFrame()
            df_rcd2 = pd.DataFrame()
            df_rcd3 = pd.DataFrame()
            df_rcd1['Día'], df_rcd1['Recup Cu del CuT, %'], df_rcd1['Recup Cu del FeT, %'], df_rcd1['Consumo Total de Acido']= dias_parametros(df_final_3,dias=None,dias_max=True)
            df_rcd2['Día'], df_rcd2['Recup Cu del CuT, %'], df_rcd2['Recup Cu del FeT, %'], df_rcd2['Consumo Total de Acido']= dias_parametros(df_final_3,dias=30,dias_max=False)
            df_rcd3['Día'], df_rcd3['Recup Cu del CuT, %'], df_rcd3['Recup Cu del FeT, %'], df_rcd3['Consumo Total de Acido'] = dias_parametros(df_final_3,dias=60,dias_max=False)
            df_rcd_total = pd.concat([df_rc,df_rcd1, df_rcd2, df_rcd3],axis=1)
            
            # Análisis_Clusters
            def generar_dataframes(df, dias_maximo):
                dataframes = []
                for dias in range(15, dias_maximo + 1, 5):
                    df_temp = pd.DataFrame()
                    df_temp[f'Día_{dias}'], df_temp[f'RecCu_{dias}'], df_temp[f'RecFe_{dias}'], df_temp[f'ConsumoAcido_{dias}'] = dias_parametros(df, dias=dias, dias_max=False)
                    dataframes.append(df_temp)
                df_final = pd.concat(dataframes, axis=1)
                df_final['columna'] = df['Nombre del Archivo'].unique()[0]
                return df_final

            # Crear el dataframe con los resultados de generar_dataframes
            df_cluster = generar_dataframes(df=df_final_3, dias_maximo=self.tiempo_prueba)
            #df_cluster['columa'] = df_final_3['Nombre del Archivo']

            #formato pmh modelo rec - consumo acido
            df_final_4 = pd.DataFrame()
            df_final_4['columna'] = df_final_3['Nombre del Archivo']
            df_final_4['dias'] = df_final_3['Día']
            df_final_4['RR'] = df_final_3['Feedin_Ratio(g/g)']
            df_final_4['% CuT Acumul'] = df_final_3['Cumulated(%CuT)']
            df_final_4['Mod Rec Cu'] = df_final_3['Ext%_Cu_model_t1']
            df_final_4['error'] = (df_final_4['% CuT Acumul'] - df_final_4['Mod Rec Cu'])**2
            df_final_4['acido agregado'] = df_final_3['Added_H2SO4_Cumulated(Kg/Tn)']
            df_final_4['Mod Rec Cu acido'] = df_final_3['Ext%_Cu_model_ac1']
            df_final_4['Error'] = (df_final_4['% CuT Acumul'] - df_final_4['Mod Rec Cu acido'])**2
            df_final_4['NAC'] = df_final_3['Net_Acid_Consumption(Kg/Tn)']

            def agregar_encabezado_modelo_doble(df, A1, A2, R1, R2,B1,B2,S1,S2,r2_1,r2_2,rmse_1,rmse_2,to,aco):
                header_data = [
                    ["","","A1", A1, "",'B1',B1,"", "",''],
                    ["","","A2", A2, "",'B2',B2,"", "",''],
                    ["","","R1", R1, "",'S1',S1,"", "",''],
                    ["","","R2", R2, "",'S2',S2,"","",''],
                    ["","","to", to, "",'ao',aco,"", "",''],
                    ["","","","","","","","","",''],
                    ["","","R2", "S2", "", "R2", "S2", "","",''],
                    ["","",r2_1, rmse_1,"",r2_2,rmse_2,"","",''],
                    ["","","","","","","","","",''],
                    #['columna',"dias", "RR", "% CuT Acumul", "Mod Rec Cu", "error", "acido_agregado", "Mod Rec Cu_acido", "error_acido", "NCA"]
                    ]
                
                header_df = pd.DataFrame(header_data)
                header_df.columns = df.columns
                # Concatenar los encabezados con el DataFrame original
                combined_df = pd.concat([header_df, df], ignore_index=True, axis=0)
                combined_df['dias']= pd.to_numeric(combined_df['dias'], errors='coerce')
                return combined_df
            
                        
            def agregar_encabezado_modelo_exponencial(df, K1, K2, K3, n1,G1,G2,G3,n2,r2_1,r2_2,rmse_1,rmse_2,to,aco):
                header_data = [
                    ["","","K1", K1, "",'G1',G1,"", "",''],
                    ["","","K2", K2, "",'G2',G2,"", "",''],
                    ["","","K3", K3, "",'G3',G3,"", "",''],
                    ["","","n1", n1, "",'n2',n2,"","",''],
                    ["","","to", to, "",'ao',aco,"", "",''],
                    ["","","","","","","","","",''],
                    ["","","R2", "S2", "", "R2", "S2", "","",''],
                    ["","",r2_1, rmse_1,"",r2_2,rmse_2,"","",''],
                    ["","","","","","","","","",''],
                    #['columna',"dias", "RR", "% CuT Acumul", "Mod Rec Cu", "error", "acido_agregado", "Mod Rec Cu_acido", "error_acido", "NCA"]
                    ]
                
                header_df = pd.DataFrame(header_data)
                header_df.columns = df.columns
                # Concatenar los encabezados con el DataFrame original
                combined_df = pd.concat([header_df, df], ignore_index=True, axis=0)
                combined_df['dias']= pd.to_numeric(combined_df['dias'], errors='coerce')
                return combined_df
            
            df_con_encabezado_modelo_doble = agregar_encabezado_modelo_doble(df_final_4, A1, A2, R1, R2,B1,B2,S1,S2,r2_t1,r2_ac1,rmse_t1,rmse_ac1,to=3,aco=ac_0)
            #df_con_encabezado_modelo_doble['dias']= pd.to_numeric(df_con_encabezado_modelo_doble['dias'], errors='coerce')
            
            df_con_encabezado_modelo_exponencial = agregar_encabezado_modelo_exponencial(df_final_4,K1, K2, K3, n1,G1,G2,G3,n2,r2_t2,r2_ac2,rmse_t1,rmse_t2,to=3,aco=ac_0)
            #df_con_encabezado_modelo_exponencial['dias']= pd.to_numeric(df_con_encabezado_modelo_exponencial['dias'], errors='coerce')
            
            dfs1.append(df_final_2)
            dfs2.append(db_1)
            dfs3.append(df_cm)
            dfs4.append(df_con_encabezado_modelo_doble)
            dfs5.append(df_con_encabezado_modelo_exponencial)
            dfs6.append(df_rcd_total)
            dfs7.append(df_cluster)

        return dfs1,dfs2,dfs3,dfs4,dfs5,dfs6,dfs7
    
    def resumen_cu(self):
        data_resumen_cu = pd.DataFrame()
        data_resumen_cu['Columnas'] = self.db_cu['equivalencias']
        data_resumen_cu['Ley_Cabeza'] = self.db_cu['CuTotal']
        data_resumen_cu['Indice_Lixiviación'] = self.db_cu['CuTotal']/(self.db_cu['CuH2SO4'] + self.db_cu['CuCN'])
        return data_resumen_cu
            

    def consolidado(self):
        lista_dfs1,lista_dfs2,lista_dfs3,lista_dfs4,lista_dfs5,lista_dfs6,lista_dfs7  = self.process()
        
        #lista_dfs7
        df_cluster = pd.concat(lista_dfs7,axis=0)
        
        #lista_dfs1 es el consolidado
        df_consolidado = pd.concat(lista_dfs1,axis=0)
        
        #lista_dfs2 es un df con los coeficientes de los 
        #4 modelos(2 de tiempo y 2 de cons_acido)
        df_coeficientes = pd.concat(lista_dfs2, axis=0)

       # lista_dfs3 es el resumen de parámetros importantes
        def asignar_odenar_grupos(columna):
            directorio = 'columnas_actualizada_'
            # Listas para agrupar los nombres de los archivos
            lista_enriquecidos = []
            lista_mixtos = []
            lista_transicionales = []
            lista_referenciales = []

            # Recorrer todos los archivos en el directorio
            for archivo in os.listdir(directorio):
                if archivo.endswith('.xlsx'):
                    partes = archivo.split(' - ')
                    if len(partes) > 2:
                        tcs_part = partes[2].split(' ')[0].lstrip('0')
                        nombre_tcs = f"TCS {tcs_part}"
                        
                        # Clasificación según el nombre del archivo
                        if 'Enriquecido' in archivo:
                            lista_enriquecidos.append(nombre_tcs)
                        elif 'Mixto' in archivo:
                            lista_mixtos.append(nombre_tcs)
                        elif 'Transicional' in archivo:
                            lista_transicionales.append(nombre_tcs)
                        else:
                            lista_referenciales.append(nombre_tcs)

            if columna in lista_enriquecidos:
                return 1
            if columna in lista_transicionales:
                return 3
            if columna in lista_mixtos:
                return 2
            if columna in lista_referenciales:
                return 4
            else:
                999
        df_resumen_parametros = pd.concat(lista_dfs3, axis=0)
        df_resumen_parametros['grupo'] = df_resumen_parametros['columna'].apply(asignar_odenar_grupos)
        grupo_col = df_resumen_parametros.pop('grupo')
        df_resumen_parametros.insert(0, 'grupo', grupo_col)
        df_resumen_parametros['grupo'] = pd.to_numeric(df_resumen_parametros['grupo'], errors='coerce')
        df_resumen_parametros_ordenado = df_resumen_parametros.sort_values(by=['grupo','Dias de Lixiviación'])
        reemplazos = {1: 'Enr', 2: 'Mix', 3: 'Tran', 4: 'Ref'}
        df_resumen_parametros_ordenado['grupo'] = df_resumen_parametros_ordenado['grupo'].replace(reemplazos)
        #df_resumen_parametros_ordenado['grupo'] = df_resumen_parametros['grupo'].replace(reemplazos)
        df_resumen_parametros = df_resumen_parametros_ordenado.transpose()


        def funcion_modelo_ordenar(df,var_orden):
            lista_df_resumen_sin_ordenar = df
            lista_df_resumen_ordenada = sorted(lista_df_resumen_sin_ordenar, key=lambda df:df[var_orden].max())
            df_resumen_ordenada = pd.concat(lista_df_resumen_ordenada,axis=1)
            headers_s = df_resumen_ordenada.columns.tolist()
            df_resumen_ordenada.iloc[8] = headers_s
            df_resumen_ordenada.columns = range(df_resumen_ordenada.shape[1])
            return df_resumen_ordenada
        
        def clasificador_grupos(df,atributo):
            directorio = 'columnas_actualizada_'
            # Listas para agrupar los nombres de los archivos
            lista_enriquecidos = []
            lista_mixtos = []
            lista_transicionales = []
            lista_referenciales = []

            # Recorrer todos los archivos en el directorio
            for archivo in os.listdir(directorio):
                if archivo.endswith('.xlsx'):
                    partes = archivo.split(' - ')
                    if len(partes) > 2:
                        tcs_part = partes[2].split(' ')[0].lstrip('0')
                        nombre_tcs = f"TCS {tcs_part}"
                        # Clasificación según el nombre del archivo
                        if 'Enriquecido' in archivo:
                            lista_enriquecidos.append(nombre_tcs)
                        elif 'Mixto' in archivo:
                            lista_mixtos.append(nombre_tcs)
                        elif 'Transicional' in archivo:
                            lista_transicionales.append(nombre_tcs)
                        else:
                            lista_referenciales.append(nombre_tcs)
            df_enriquecido = df[df[atributo].isin(lista_enriquecidos)]
            df_mixto = df[df[atributo].isin(lista_mixtos)]
            df_transicional = df[df[atributo].isin(lista_transicionales)]
            df_referencial = df[df[atributo].isin(lista_referenciales)]
            return df_enriquecido, df_mixto, df_transicional, df_referencial


        #lista_dfs4 es el resultado del modelo doble
        df_resumen_modelo_doble = funcion_modelo_ordenar(lista_dfs4,'dias')
        #df_resumen_modelo_doble = pd.concat(df_resumen_modelo_doble, axis=1)

        #lista_dfs5 es el resultado del modelo exponencial
        df_resumen_modelo_exponencial = funcion_modelo_ordenar(lista_dfs5,'dias')
        #df_resumen_modelo_exponencial = pd.concat(df_resumen_modelo_exponencial, axis=1)

        #lista_dfs6 es el resumen de caracterización química
        df_resumen_carac_quim = pd.concat(lista_dfs6, axis=0)
        df_enriquecido, df_mixto, df_transicional, df_referencial = clasificador_grupos(df=df_resumen_carac_quim, atributo='columna')
        df_enriquecido = df_enriquecido.reset_index(drop=True)
        df_mixto = df_mixto.reset_index(drop=True)
        df_transicional = df_transicional.reset_index(drop=True)
        df_referencial = df_referencial.reset_index(drop=True)
        df_resumen_total =  pd.concat([df_enriquecido, df_mixto, df_transicional, df_referencial],axis=1)


        nuevos_nombres = {'Nombre del Archivo':'columna','Fecha':'fecha','Día':'dias','Peso(g)_Feed':'riego_refino_peso_g','Feedin_Ratio(g/g)':'ratio_riego_refino_m3/t',
                          'Actual_Rate(Kg/hm2)':'ratio_riego_refino_kg/hm2','Cu(g/Kg)_Feed':'Cu_refino_g/kg','ÁcidoLibre(g/Kg)_Feed':'acido_refino_g/kg',
                          'Fe(g/Kg)_Feed':'FeTotal_refino_g/kg','Fe+2(g/Kg)_Feed':'Fe+2_refino_g/kg','Fe+3(g/Kg)_Feed':'Fe+3_refino_g/kg','ORP(mV)_Feed':'ORP_refino_mV',
                          'pH_Feed':'pH_refino','Peso(g)_PLS':'DrainDown_PLS_g','Feedin_Ratio(g/g)_pls':'DrainDownPLS_g/kg','Actual_Rate(Kg/hm2)':'Drain_Down_PLS_kg/hm2',
                          'Cu(g/Kg)_PLS':'Cu_PLS_g/kg','Cu_Neto(g/Kg)_PLS':'CuNet_PLS_g/kg','ÁcidoLibre(g/Kg)_PLS':'acido_PLS_g/kg','Fe(g/Kg)_PLS':'FeTotal_PLS_g/kg',
                          'Fe+2(g/Kg)_PLS':'Fe+2_PLS_g/kg','Fe+3(g/Kg)_PLS':'Fe+3_PLS_g/kg','ORP(mV)_PLS':'ORP_PLS_mV','pH_PLS':'pH_PLS','Raffinate_Density':'densidad_refino_gr/cc',
                          'PLS_Density':'densidad_PLS_gr/cc','Free_Column_Height':'altura_libre_column_cm','Cumulated Compaction':'%_compactacion_column',
                          'Partial(g/Kg)':'ExtParc_CuT_g/kg','Cumulated(g/Kg)':'ExtAcum_CuT_g/kg','Cumulated(%CuT)':'ExtAcum_CuT_%','Residue(%CuT)':'residuo_Cu_acum_%',
                          'Partial_FeT%':'ExtParc_FeT_%','Cumulated_FeT%':'ExtAcum_FeT_%','Gross_Acid_Consumption(Kg/Tn)':'ConsBrutoAci_kg/t','Net_Acid_Consumption(Kg/Tn)':'ConsNeto_Aci_kg/t',
                          'Net_Acid_Consumption(Kg/KgCu)':'ConsNetoAci_kg/kgCu','Cu(g)':'Cu_agregado_refino_g','H2SO4(g)':'acido_parcial_agregado_refino_g',
                          'Added_H2SO4_Cumulated(Kg/Tn)':'acido_acum_agregado_refino_kg/t','Fe_Total(g)':'FeT_agregado_refino_g','Fe+2(g)':'Fe+2_agregado_refino_g',
                          'Fe+3(g)':'Fe+3_agregado_refino_g','AAdded_Fe+3_Cumulated(Kg/Tn)':'Fe+3_acum_agregado_refino_kg/t','Fe+3/Fe+2':'Fe+3/Fe+2_agregado_refino',
                          'Fe+2/FeT':'Fe+2/FeT_agregado_refino','Added_FeT_Cumulated(Kg/Tn)':'FeT_acum_agregado_refino_kg/t','Cu(g)_pls':'Cu_percolado_PLS_g',
                          'pH*Liters_pls':'pH*PLS_percolado','H2SO4(g)_pls':'acido_percolado_PLS_g','Fe_Total(g)_pls':'FeT_percolado_PLS_g','Fe+2(g)_pls':'Fe+2_percolado_PLS_g',
                          'Fe+3(g)_pls':'Fe+3_percolado_PLS_g','Cu/FeT_pls':'CuT/FeT_PLS','Cu/Fe+2_pls':'CuT/Fe+2_PLS','Fe+3/Fe+2_pls':'Fe+3/Fe2+_PLS','Fe+2/Fe_pls':'Fe+2/FeT_PLS',
                          'D/R Ratio':'PLS_percolado/refino_agregado','Retained_Solution(%vol/vol)':'%vol/vol_SolucionRetenida','Retained_Solution(g/Kg)':'SolucionRetenida_g/kg','Dynamic_Moisture':'humedad_dinamica_%',
                          'Leached_Cu_day(g)':'Cu_lixiviado_dia_g','Leached_Cu_cumulated(g)':'Cu_lixiviado_acum_g','Leached_Cu_cumulated(mol)':'Cu_lixiviado_acum_mol','Leached_Fe_day(g)':'Fe_lixiviado_dia_g',
                          'Leached_Fe_cumulated(g)':'Fe_lixiviado_acum_g','Leached_Fe_cumulated(mol)':'Fe_lixiviado_acum_kg/t','Leached_Fe+2_day(g)':'Fe+2_lixiviado_dia_g',
                          'Leached_Fe+2_cumulated(g)':'Fe+2_lixiviado_acum_g','Consumed_Fe+3_day(g)':'Fe+3_consumido_dia_g','Consumed_Fe+3_cumulated(g)':'Fe+3_consumido_acum_g','Consumed_Fe+3_cumulated(mole)':'Fe+3_consumido_acum_mol',
                          'Consumed_Fe+3_cumulated(Kg/Tn)':'Fe+3_consumido_acum/t','Fe+3_Cu_cumulated(mole/mole)':'Fe+3_consumido_acum_mol/Cu_lixiviado_acum_mol','Fe+3_Cu_cumulated(Kg/Kg)':'Fe+3_consumido_acum_kg/Cu_lixiviado_acum_kg',
                          'Consumed_H2SO4_GroosDay(g)':'consumo_bruto_acido_dia_g','Consumend_H2SO4_Eq_Acid_Day_Cu(g)':'consumo_equivalente_dia_acido_Cu_g','Consumend_H2SO4_Eq_Acid_Day_Fe(g)':'consumo_equivalente_dia_acido_Fe_g',
                          'Consumend_H2SO4_NextDay(g)':'consumo_neto_acido_g','Consumed_H2SO4_GrossDay(Kg/Tn)':'consumo_bruto_acido_dia_kg/t','Consumed_H2SO4_Acid_Day_Cu(Kg/Tn)':'consumo_equivalente_dia_acido_Cu_kg/t',
                          'Consumed_H2SO4_Acid_Day_Fe(Kg/Tn)':'consumo_equivalente_dia_acido_Fe_kg/t','Consumed_H2SO4_NextDay(Kg)':'consumo_neto_dia_acido_kg/t','KgFe+2/tms_ore':'Fe+2_lixiviado_acum_kg/t',
                          'Cu_extraido(Kg)':'Cu_extraido_acum_kg','Cu_adic_Ref(Kg)':'Cu_adicionado_refino_dia_kg','Cu_acum_adic_Ref(Kg)':'Cu_adicionado_refino_acum_kg','m3':'m3_agregados_refino_acum',
                          'Cu_extraido(Kg/m3)':'Cu_extraido_kg/refino_agregado_m3','Kg_Cu_extr/kg_Cu_ad(Kg/Kg)':'Cu_extraido_kg/Cu_adicionado_refino','KgCu_extr/dia(Kg)':'Cu_extraido_dia_kg','Raffinate_Fe+3/FeT':'Fe+3/FeT_refino',
                          'pls_Fe+3/FeT':'Fe+3/FeT_PLS','Fe+3pls/Fe+3ref':'Fe+3_PLS / Fe+3_refino','Ext%Cu_oxidos':'Ext%Cu_oxidos','Ext%Cu_facil':'Ext%Cu_facil','Ext%Cu_IL':'Ext%Cu_IL'}
        df_consolidado = df_consolidado.rename(columns=nuevos_nombres)
        return df_consolidado,df_coeficientes, df_resumen_parametros, df_resumen_modelo_doble, df_resumen_modelo_exponencial, df_resumen_total, df_cluster




