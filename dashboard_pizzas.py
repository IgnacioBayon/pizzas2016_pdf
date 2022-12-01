import pandas as pd
import datetime
import re
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from fpdf import FPDF

warnings.filterwarnings("ignore")

class PDF(FPDF):    
    def titles(self,title):
        self.set_xy(70.0,0.0)
        self.set_font('Arial', 'B', 30)
        self.set_text_color(00,00,80)
        self.cell(w=210.0, h=40.0, align='C', txt=title, border=0)

def extract()->list[pd.DataFrame]:
    file_names = ['data_dictionary.csv', 'order_details.csv', 'orders.csv', 'pizza_types.csv','pizzas.csv']
    df_lst = []
    for name in file_names:
        if name in ['data_dictionary.csv','pizzas.csv','pizza_types.csv']:
            sep = ','
        else:
            sep = ';'
        df = pd.read_csv(f'files2016/{name}', sep, encoding='latin_1')
        df_lst.append(df)
    return df_lst

def compilar_patrones():
    espacio = re.compile(r'\s')
    guion = re.compile(r'-')
    arroba = re.compile(r'@')
    d_0 = re.compile(r'0')
    d_3 = re.compile(r'3')
    uno = re.compile(r'one',re.I)
    dos = re.compile(r'two',re.I)
    comma = re.compile(r',')
    
    
    quitar = [espacio, guion, arroba, d_0, d_3, uno, dos]
    poner = ['_', '_', 'a', 'o', 'e', '1', '2']
    patrones = [quitar, poner, comma]
    return patrones

def drop_nans(df_orders:pd.DataFrame, df_order_details:pd.DataFrame):
    """
    Dropeamos los NaNs de ambos dataframes. Intersecamos ambos dataframes
    para droppear lo que hemos sacado de un dataframe en el otro
    """
    df_order_details.dropna(inplace=True)
    or_id_A = set(df_orders['order_id'].unique())
    or_id_B = set(df_order_details['order_id'].unique())
    keep_order_id = or_id_A & or_id_B
    df_orders = df_orders[df_orders['order_id'].isin(keep_order_id)]
    df_order_details = df_order_details[df_order_details['order_id'].isin(keep_order_id)]
    # Ordenamos los Dataframes y reiniciamos sus índices
    df_orders.sort_values(by='order_id', inplace=True)
    df_orders.reset_index(drop=True, inplace=True)
    df_order_details.sort_values(by='order_id', inplace=True)
    df_order_details.reset_index(drop=True, inplace=True)
    return df_orders, df_order_details

def transform_key(key):
    if key[-1] == 's':
        end_str, count = 2, 0.75
    elif key[-1] == 'm':
        end_str, count = 2, 1
    elif key[-1] == 'l' and key[-2] != 'x':
        end_str, count = 2, 1.5
    elif key[-2:] == 'xl' and key[-3] != 'x': # xl
        end_str, count = 3, 2
    else: # xxl
        end_str, count = 4, 3
    return end_str, count

def limpieza_de_datos(df_orders:pd.DataFrame, df_order_details:pd.DataFrame):
    ### LIMPIEZA DE LOS DATOS
    ## 1. FORMATO DATETIME
    for i in range(len(df_orders)):
        unformatted_date = str(df_orders['date'][i])
        df_orders.loc[i,'date'] = pd.to_datetime(df_orders['date'][i], errors='coerce')
        if pd.isnull(df_orders.loc[i,'date']):
            unformatted_date = unformatted_date[:unformatted_date.find('.')]
            formatted_date = datetime.datetime.fromtimestamp(int(unformatted_date))
            df_orders.loc[i,'date'] = pd.to_datetime(formatted_date)

    df_orders['date'] = pd.to_datetime(df_orders['date'], format="%Y/%m/%d")
    df_orders['week'] = df_orders['date'].dt.week
    df_orders['weekday'] = df_orders['date'].dt.weekday

    ## 2. CORREGIR NOMBRES

    df_orders, df_order_details = drop_nans(df_orders, df_order_details)
    patrones = compilar_patrones()
    [quitar, poner, comma] = patrones
    # Ahora debo corregir los nombres de las pizzas y los números
    for i in range(len(quitar[:-2])):
        df_order_details['pizza_id'] = [quitar[i].sub(poner[i], str(x)) for x in df_order_details['pizza_id']]
    for i in range(len(quitar[:-2]), len(quitar)):
        df_order_details['quantity'] = [quitar[i].sub(poner[i], str(x)) for x in df_order_details['quantity']]
    df_order_details['quantity'] = [abs(int(x)) for x in df_order_details['quantity']]

    
    return df_orders, df_order_details

def transform(df_lst:list[pd.DataFrame]):
    df_orders = df_lst[2]
    df_order_details = df_lst[1]
    df_orders.dropna(subset='date', inplace=True)
    df_orders.reset_index(drop=True, inplace=True)
    df_orders.drop('time', axis=1, inplace=True)

    df_orders, df_order_details  = limpieza_de_datos(df_orders, df_order_details)

    return df_orders, df_order_details, 

def obtain_dfs_plots(df_lst: list[pd.DataFrame], df_orders: pd.DataFrame, df_order_details: pd.DataFrame):
    pizzas_df = df_lst[4]

    # Creamos nuestro Diccionario de Pizzas Anual
    pizzas_anual_dict = {}
    pizzas_anual_sizes_dict = {}
    for index in range(len(pizzas_df)):
        pizzas_anual_dict[pizzas_df['pizza_type_id'][index]] = 0
        pizzas_anual_sizes_dict[pizzas_df['pizza_id'][index]] = 0


    # SACAMOS DATAFRAME PIZZAS SEMANALES EN EL AÑO
    weeks_dict = {}
    for week in range(1,52):
        # Creamos nuestro Diccionario de Pizzas Semanal
        pizzas_semana_dict = {}
        for pizza in pizzas_anual_dict:
            pizzas_semana_dict[pizza] = 0

        week_orders = df_orders.loc[df_orders['week']==week]
        order_ids = week_orders['order_id']
        week_df = df_order_details.loc[df_order_details['order_id'].isin(order_ids)]
        
        for index in range(1,len(week_df)):
            # Así accedemos a un valor concreto: df.iloc[columna].iloc[fila]
            
            key = week_df['pizza_id'].iloc[index]
            end_str, count = transform_key(key)
            value = week_df['quantity'].iloc[index]*count
            pizzas_semana_dict[key[:-end_str]] += value
            pizzas_anual_dict[key[:-end_str]] += value
        
        weeks_dict[week] = pizzas_semana_dict
        order_ids = week_orders['order_id']
        week_df = df_order_details.loc[df_order_details['order_id'].isin(order_ids)]

    # SACAMOS DATAFRAME PIZZAS POR DÍAS
    weekdays_dict = {}
    dayofweek = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
    for day in range(7):
        pizzas_weekday_dict = {}
        for pizza in pizzas_anual_dict:
            pizzas_weekday_dict[pizza] = 0
            
        weekday_orders = df_orders.loc[df_orders['weekday']==day]
        order_ids = weekday_orders['order_id']
        weekday_df = df_order_details.loc[df_order_details['order_id'].isin(order_ids)]
        
        for index in range(1,len(week_df)):
            # Así accedemos a un valor concreto: df.iloc[columna].iloc[fila]
            
            key = weekday_df['pizza_id'].iloc[index]
            end_str, count = transform_key(key)
            value = weekday_df['quantity'].iloc[index]*count
            pizzas_weekday_dict[key[:-end_str]] += value
        weekdays_dict[dayofweek[day]] = pizzas_weekday_dict
    
    datos_anual = {'pizzas':list(pizzas_anual_dict.keys()), 'quantity': list(pizzas_anual_dict.values())}
    df_pizzas_anuales = pd.DataFrame.from_dict(datos_anual).round(decimals=0)
    df_pizzas_anuales.sort_values(by='quantity', inplace=True, ascending=False)
    df_pizzas_semanales = pd.DataFrame(weeks_dict)
    df_pizzas_weekdays = pd.DataFrame(weekdays_dict)
    
    return df_pizzas_anuales, df_pizzas_semanales, df_pizzas_weekdays

def plots(df_pizzas_anuales: pd.DataFrame, df_pizzas_semanales: pd.DataFrame, df_pizzas_weekdays: pd.DataFrame):
    if not os.path.exists('plt_figs'):
        os.mkdir('plt_figs')

    # Annual Pizzas
    plt.figure(figsize=(12,8))
    plt.title(f"(Ponderated) Annual Pizzas")
    ax = sns.barplot(x='quantity', y='pizzas', data=df_pizzas_anuales,palette='rocket_r',orient='h') # rocket_r
    plt.savefig('plt_figs/pizza_requests.png', transparent=True)

    # Time Evolution
    top_pizzas = list(df_pizzas_anuales.head()['pizzas'])
    df_top_pizzas = df_pizzas_semanales.loc[df_pizzas_semanales.index.isin(top_pizzas)]
    pizzas = list(df_top_pizzas.index)
    
    plt.figure(figsize=(12,6))
    plt.title(f"Week Order Evolution - Top 5 Pizzas")
    for pizza in pizzas:
        ax = sns.lineplot(data=df_top_pizzas.loc[pizza],palette='rocket_r') # rocket_r
    plt.xlabel('Week')
    plt.ylabel('Quantity')
    plt.ylim(0)
    plt.legend(pizzas)
    plt.savefig('plt_figs/time_evolution.png', transparent=True)

    # Pie Chart
    explode = [0]*len(df_pizzas_anuales)
    for i in range(5):
        explode[i] = 0.1
    plt.figure(figsize=(12,6))
    plt.title(f"(Ponderated) Annual Pizzas")
    ax = plt.pie(df_pizzas_anuales['quantity'], explode)
    plt.legend(top_pizzas)
    plt.savefig('plt_figs/pie_chart.png', transparent=True)

    # Weekdays Barplot
    df_pizzas_weekdays = df_pizzas_weekdays.round(decimals=0)
    df_pizzas_weekdays.head()
    total_pizzas_por_dias = {}
    for columna in df_pizzas_weekdays:
        total_pizzas_por_dias[columna] = sum(df_pizzas_weekdays[columna])
    
    plt.figure(figsize=(12,6))
    plt.title("Pizzas Ordered by WeekDays")
    ax = sns.barplot(x=list(total_pizzas_por_dias.keys()), y=list(total_pizzas_por_dias.values()) ,palette='rocket_r')
    plt.savefig('plt_figs/weekdays.png', transparent=True)

    # Table
    df_tabla = df_pizzas_anuales.head(15)
    df_tabla.set_index(pd.Series(range(1,16)), inplace=True)
    plt.figure(figsize=(3,4))
    plt.title("Top 15 pizzas by sales")
    ax = plt.subplot(111, frame_on=False) # no visible frame
    ax.xaxis.set_visible(False)  # hide the x axis
    ax.yaxis.set_visible(False)  # hide the y axis
    pd.plotting.table(ax, df_tabla, loc='center')
    plt.savefig('plt_figs/table.png', transparent=False)

def load():
    pdf = PDF()
    pdf.add_page(orientation='L')
    pdf.titles(title='Dashboard 2016 - Maven Pizzas')
    pdf.image('plt_figs/table.png', 85,30,60)
    pdf.image('plt_figs/pie_chart.png',-60,5,210)
    pdf.image('plt_figs/pizza_requests.png',0,100,150)
    pdf.image('plt_figs/weekdays.png',130,110,170)
    pdf.image('plt_figs/time_evolution.png',130,30,170)

    pdf.set_author('Ignacio Bayón Jiménez-Ugarte')
    pdf.output('dashboard.pdf','F')
    

if __name__ == "__main__":
    df_lst = extract()
    df_orders, df_order_details = transform(df_lst)
    df_pizzas_anuales, df_pizzas_semanales, df_pizzas_weekdays = obtain_dfs_plots(df_lst,df_orders, df_order_details)
    plots(df_pizzas_anuales, df_pizzas_semanales, df_pizzas_weekdays)
    load()