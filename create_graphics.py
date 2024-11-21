import seaborn as sns
import matplotlib.pyplot as plt
from params import color_map
from params import marker_map
from params import list_column,list_enr,list_mixto
import logging
import os

class graphics:
    def __init__(self,df,list_column,list_enr,list_mixto,root_graficas):
        self.df = df
        self.list_column = list_column
        self.list_enr = list_enr
        self.list_mixto = list_mixto
        self.root_graficas = root_graficas

    def gruops(self):
        sns.set_theme(style='whitegrid')
        for i, sub_list in enumerate(self.list_column, start=1):
            df_selected = self.df[self.df['columna'].isin(sub_list)]
            
            try:
                df_selected = self.df[self.df['columna'].isin(sub_list)]
                if i == len(self.list_column):
                    df_enr_total = self.df[self.df['columna'].isin(self.list_mixto)]
                else:
                    df_enr_total = self.df[self.df['columna'].isin(self.list_enr)]

                folder_name = os.path.join(self.root_graficas, f'graficas_grupo{i}')
                os.makedirs(folder_name, exist_ok=True)
                logging.info(f"Directorio creado: {folder_name}")

                max_dias_db = df_selected['dias'].unique().max()
                logging.info(f"Máximo valor de 'dias' en el grupo {i}: {max_dias_db}")

                # ExtAcum_CuT_% vs dias
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='dias', y='ExtAcum_CuT_%', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=55)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_1 = self.df[self.df['columna']==enr_val]
                    df_enr_1 = df_enr_1[df_enr_1['dias']<=max_dias_db]
                    sns.lineplot(data=df_enr_1, x='dias', y='ExtAcum_CuT_%', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left',fontsize=14)
                plt.title('ExtAcum_CuT_% vs dias', fontweight='bold',fontsize=20)
                plt.xlim(0,round(df_selected['dias'].max()*1.1))
                if df_selected['ExtAcum_CuT_%'].max()>=70:
                    limy = 100
                else:
                    limy=None
                plt.ylim(0,limy)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                plt.xlabel('dias',fontsize=15)
                plt.ylabel('ExtAcum_CuT_',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'ExtAcum_CuT_%_vs_dias.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico ExtAcum_CuT_% vs dias guardado en: {folder_name}")

                # Ext%Cu_IL vs dias
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='dias', y='Ext%Cu_IL', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=55)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_2 = self.df[self.df['columna']==enr_val]
                    df_enr_2 = df_enr_2[df_enr_2['dias']<=max_dias_db]
                    sns.lineplot(data=df_enr_2, x='dias', y='Ext%Cu_IL', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left', fontsize=14)
                plt.title('Ext%Cu_IL vs dias', fontweight='bold',fontsize=20)
                plt.xlim(0,round(df_selected['dias'].max()*1.1))
                if df_selected['Ext%Cu_IL'].max()>=70:
                    limy = 100
                else:
                    limy=None
                plt.ylim(0,limy)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                plt.xlabel('dias',fontsize=15)
                plt.ylabel('Ext%Cu_IL',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'Ext%Cu_IL_vs_dias.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico Ext%Cu_IL vs dias guardado en: {folder_name}")

                # acido acumulado agregado refino vs Ext%_Cu_IL
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='acido_acum_agregado_refino_kg/t', y='Ext%Cu_IL', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=55)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_3 = self.df[self.df['columna']==enr_val]
                    sns.lineplot(data=df_enr_3, x='acido_acum_agregado_refino_kg/t', y='Ext%Cu_IL', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left',fontsize=14)
                plt.title('Ext%Cu_IL vs acido_acum_agregado_refino_kg/t', fontweight='bold',fontsize=20)
                plt.xlim(round(df_selected['acido_acum_agregado_refino_kg/t'].min()*0.9),round(df_selected['acido_acum_agregado_refino_kg/t'].max()*1.1))
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                plt.xlabel('acido_acum_agregado_refino_kg/t',fontsize=15)
                plt.ylabel('Ext%Cu_IL',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'Ext%Cu_IL_vs_acido_acum_agregado_refino_kg_t.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico acido acumulado agregado refino vs Ext%_Cu_IL guardado en: {folder_name}")

                # Consumo Neto de Acido vs Ext%_Cu_IL
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='ConsNeto_Aci_kg/t', y='Ext%Cu_IL', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=55)
                for enr_val in df_enr_total['columna'].unique():
                    plt.plot(df_enr_total[df_enr_total['columna']==enr_val]['ConsNeto_Aci_kg/t'], df_enr_total[df_enr_total['columna']==enr_val]['Ext%Cu_IL'], color=color_map[enr_val], linestyle='-', linewidth=2.5, label=enr_val)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left',fontsize=14)
                plt.title('Ext%Cu_IL vs ConsNeto_Aci_kg/t', fontweight='bold',fontsize=20)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                plt.xlabel('ConsNeto_Aci_kg/t',fontsize=15)
                plt.ylabel('Ext%Cu_IL',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'Ext%Cu_IL_vs_ConsNeto_Aci_kg_t.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico Consumo Neto de Acido vs Ext%_Cu_IL guardado en: {folder_name}")

                # ORP en el PLs vs dias
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='dias', y='ORP_PLS_mV', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=55)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_4 = self.df[self.df['columna']==enr_val]
                    df_enr_4 = df_enr_4[df_enr_4['dias']<=max_dias_db]
                    sns.lineplot(data=df_enr_4, x='dias', y='ORP_PLS_mV', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left', fontsize=14)
                plt.title('ORP_PLS_mV vs dias', fontweight='bold',fontsize=20)
                plt.xlim(0,round(df_selected['dias'].max()*1.1))
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                plt.xlabel('dias',fontsize=15)
                plt.ylabel('ORP_PLS_mV',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'ORP_PLS_mV_vs_dias.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico ORP en el PLs vs dias guardado en: {folder_name}")

                # Fe+3 / FeT en el PLS vs dias
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='dias', y='Fe+3/FeT_PLS', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=55)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_5 = self.df[self.df['columna']==enr_val]
                    df_enr_5 = df_enr_5[df_enr_5['dias']<=max_dias_db]
                    sns.lineplot(data=df_enr_5, x='dias', y='Fe+3/FeT_PLS', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left',fontsize=14)
                plt.title('Fe+3/FeT_PLS vs dias', fontweight='bold',fontsize=20)
                plt.xlim(0,round(df_selected['dias'].max()*1.1))
                if df_selected['Fe+3/FeT_PLS'].max()>0.7:
                    limy=1
                else:
                    limy=None
                plt.ylim(0,limy)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                plt.xlabel('dias',fontsize=15)
                plt.ylabel('Fe+3/FeT_PLS',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'Fe+3_FeT_PLS_vs_dias.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico Fe+3 / FeT en el PLS vs dias guardado en: {folder_name}")

                # pH vs dias
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='dias', y='pH_PLS', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=60)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_6 = self.df[self.df['columna']==enr_val]
                    df_enr_6 = df_enr_6[df_enr_6['dias']<=max_dias_db]
                    sns.lineplot(data=df_enr_6, x='dias', y='pH_PLS', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left',fontsize=14)
                plt.title('pH_PLS vs dias', fontweight='bold',fontsize=20)
                plt.xlim(0,round(df_selected['dias'].max()*1.1))
                plt.xticks(fontsize=15)
                plt.yticks(fontsize=15)
                plt.xlabel('dias',fontsize=15)
                plt.ylabel('pH_PLS',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'pH_PLS_vs_dias.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico pH vs dias guardado en: {folder_name}")

                # Acido Libre PLs vs dias
                plt.figure(figsize=(16, 8))
                for col_val in sub_list:
                    db = df_selected[df_selected['columna']==col_val]
                    sns.scatterplot(data=db, x='dias', y='acido_PLS_g/kg', marker=marker_map[col_val], color=color_map[col_val], label=col_val,s=60)
                for enr_val in df_enr_total['columna'].unique():
                    df_enr_7 = self.df[self.df['columna']==enr_val]
                    df_enr_7 = df_enr_7[df_enr_7['dias']<=max_dias_db]
                    sns.lineplot(data=df_enr_7, x='dias', y='acido_PLS_g/kg', color=color_map[enr_val], label=enr_val,linewidth=3.0)
                plt.legend(bbox_to_anchor=(1.001, 1), loc='upper left',fontsize=14)
                plt.title('acido_PLS_g/kg vs dias', fontweight='bold',fontsize=20)
                plt.xlim(0,round(df_selected['dias'].max()*1.1))
                plt.xticks(fontsize=15)
                plt.yticks(fontsize=15)
                plt.xlabel('dias',fontsize=15)
                plt.ylabel('acido_PLS_g/kg',fontsize=15)
                plt.savefig(os.path.join(folder_name, 'acido_PLS_g_kg_vs_dias.png'), bbox_inches='tight')
                plt.close()
                logging.info(f"Gráfico Acido Libre PLs vs dias guardado en: {folder_name}")
            
            except Exception as e:
                logging.error(f"Error procesando el grupo {i}: {e}")
                continue