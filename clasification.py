import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.optimize import curve_fit
import os
import logging
import pandas as pd
from data_processing import ExcelReader, MetallurgicalProcess
from create_graphics import graphics
from create_ppt import PowerPointGenerator
from curvas_cineticas import curvas_cineticas
from params import list_column, list_enr, list_mixto
from roots import root_db_cu
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import pandas as pd

class clasification_model():
    def __init__(self):
        
    
    def create_cluster(self, archivo, hoja, lista_ipc, n_clusters, n_components):
    df = pd.read_excel(archivo, sheet_name=hoja)
    
    # Función para eliminar valores '<X' convirtiéndolos en float
    def eliminar_menor(valor):
        if isinstance(valor, str) and '<' in valor:
            return float(valor.replace('<', ''))
        return valor
    
    df = df.applymap(eliminar_menor)
    db = df[lista_ipc]
    
    # Escalar los datos antes de aplicar KMeans y PCA
    scaler = StandardScaler()
    db_scaled = scaler.fit_transform(db)

    # Aplicar PCA
    def use_pca():
        pca = PCA(n_components=n_components)
        db_pca = pca.fit_transform(db_scaled)
        
        # Mostrar varianza explicada
        explained_variance = pca.explained_variance_ratio_
        explained_variance_acum = np.cumsum(explained_variance)

        plt.figure(figsize=(8, 6))
        plt.bar(range(1, len(explained_variance) + 1), explained_variance, alpha=0.5, align='center', label='Varianza explicada individual')
        plt.plot(range(1, len(explained_variance_acum) + 1), explained_variance_acum, marker='o', color='red', label='Varianza explicada acumulada')
        plt.ylabel('Porcentaje de varianza explicada')
        plt.xlabel('Componentes principales')
        plt.title('Varianza explicada por PCA')
        plt.legend(loc='best')
        plt.grid(True)
        plt.show()

        # Crear un DataFrame con las componentes principales
        db_pca = pd.DataFrame(db_pca, columns=[f'PC{i+1}' for i in range(n_components)])
        db_pca['columna'] = df['columna']
        return db_pca
    
    db_pca = use_pca()
    
    # Método del codo para determinar el número de clusters
    inercias = []
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, random_state=0)
        kmeans.fit(db_pca.drop(columns='columna'))
        inercias.append(kmeans.inertia_)
    
    # Graficar el método del codo
    plt.plot(range(1, 11), inercias, marker='o')
    plt.title('Método del Codo')
    plt.xlabel('Número de clusters')
    plt.ylabel('Inercia')
    plt.show()
    
    # Aplicar KMeans con el número de clusters especificado
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(db_pca.drop(columns='columna'))
    centros = kmeans.cluster_centers_
    etiquetas = kmeans.labels_

    # Agregar las etiquetas de cluster al DataFrame de PCA
    db_pca['Cluster'] = etiquetas
    
    # También agregar las etiquetas de cluster al DataFrame original (db)
    db['Cluster'] = etiquetas

    # Mostrar la matriz de correlación y el heatmap
    corr = db.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm')
    plt.show()

    # Función para graficar los clusters en las variables originales
    def grafica_cluster_originales(df, x, y):
        # Filtrar los datos por clusters
        colores = sns.color_palette('hsv', len(df['Cluster'].unique()))
        plt.figure(figsize=(8, 6))
        for i, cluster in enumerate(df['Cluster'].unique()):
            cluster_data = df[df['Cluster'] == cluster]
            plt.scatter(cluster_data[x], cluster_data[y], color=colores[i], label=f'Cluster {cluster}', s=50)

        # Etiquetas y título
        plt.title(f'Gráfico de {x} vs {y} (Coloreado por Cluster)')
        plt.xlabel(x)
        plt.ylabel(y)
        plt.legend()
        plt.grid(True)
        plt.show()

    # Iterar sobre pares de columnas originales para hacer gráficos
    for i, x in enumerate(lista_ipc):
        for j, y in enumerate(lista_ipc):
            if i >= j:
                continue
            grafica_cluster_originales(db, x, y) 
    
    return db_pca

    folder_path = 'columnas_actualizada_'
    excel_reader = ExcelReader(folder_path=folder_path)
    dfs, new_names_columns = excel_reader.read_excel_files()
    parameters = excel_reader.calculate_parameters()
    a = MetallurgicalProcess(df=dfs, parameters=parameters,
                                    Raffinate_Density=1.04, PLS_Density=0,
                                    root_db_cu=root_db_cu, equivalencias=new_names_columns)
    lista_dfs1,lista_dfs2,lista_dfs3,lista_dfs4,lista_dfs5,lista_dfs6,df_cluster  = a.consolidado()

