import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from params import color_map, symbol_map
from user import run_process
import logging

def run_app(folder_path):
    try:
        logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info(f'Iniciando el proceso con la carpeta: {folder_path}')
        
        df = run_process(folder_path)
        logging.info('Proceso completado y datos cargados en el DataFrame.')

        app = dash.Dash(__name__)

        app.layout = html.Div([
            html.H1("Dashboard de Visualización", style={'font-family': 'Arial', 'font-weight': 'bold'}),
            
            html.Label("Seleccionar subconjunto de datos por columna (Gráfico 1):", style={'font-family': 'Arial', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='dropdown-columna-graph1',
                options=[{'label': i, 'value': i} for i in df['columna'].unique()],
                multi=True,
                value=list(df['columna'].unique())
            ),

            html.Div([
                html.Label("Seleccionar variable para el eje X (Gráfico 1):", style={'font-family': 'Arial', 'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='dropdown-x-graph1',
                    options=[{'label': col, 'value': col} for col in df.columns],
                    value='fecha'
                ),
                html.Label("Seleccionar variable para el eje Y (Gráfico 1):", style={'font-family': 'Arial', 'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='dropdown-y-graph1',
                    options=[{'label': col, 'value': col} for col in df.columns],
                    value='riego_refino_peso_g'
                ),
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            dcc.Graph(id='graph1'),

            # html.H2("Dashboard análisis de Cu", style={'font-family': 'Arial', 'font-weight': 'bold'}),
            
            # html.Label("Seleccionar subconjunto de datos por columna (Gráfico 2):", style={'font-family': 'Arial', 'font-weight': 'bold'}),
            # dcc.Dropdown(
            #     id='dropdown-columna-graph2',
            #     options=[{'label': i, 'value': i} for i in df_il['columna'].unique()],
            #     multi=True,
            #     value=list(df_il['columna'].unique())
            # ),
            
            # dcc.Graph(id='graph2'),
        ])

        @app.callback(
            Output('graph1', 'figure'),
            [Input('dropdown-x-graph1', 'value'),
             Input('dropdown-y-graph1', 'value'),
             Input('dropdown-columna-graph1', 'value')]
        )
        def update_graph1(x_variable, y_variable, selected_tipo):
            filtered_df = df[df['columna'].isin(selected_tipo)]
            fig = px.scatter(filtered_df, x=x_variable, y=y_variable, color='columna',
                             color_discrete_map=color_map, symbol='columna', symbol_map=symbol_map, height=600, width=1200)
            fig.update_traces(marker=dict(size=0), selector=dict(mode='markers', name='TBC015 OP Enriquecido'))
            fig.update_traces(mode='lines', selector=dict(name='TBCE15 OP Enriquecido'))
            fig.update_traces(marker=dict(size=0), selector=dict(mode='markers', name='TBC016 OP Enriquecido'))
            fig.update_traces(mode='lines', selector=dict(name='TBCE16 OP Enriquecido'))
            fig.update_traces(marker=dict(size=0), selector=dict(mode='markers', name='TBCM011 OP Mixto'))
            fig.update_traces(mode='lines', selector=dict(name='TBCM11 OP Mixto'))
            fig.update_layout(
                title={'text': f'<b>{y_variable} vs {x_variable}</b>', 'x': 0.5, 'y': 0.95, 'xanchor': 'center', 'yanchor': 'top'},
                xaxis=dict(
                    titlefont=dict(size=18),
                    tickfont=dict(size=14)
                ),
                yaxis=dict(
                    titlefont=dict(size=18),
                    tickfont=dict(size=14)
                ),
                legend=dict(
                    font=dict(size=14)
                )
            )
            return fig

        logging.info('Iniciando el servidor Dash.')
        app.run_server(debug=False)

    except Exception as e:
        logging.error(f'Error al iniciar el servidor Dash: {e}')
        print(f'Error al iniciar el servidor Dash: {e}')