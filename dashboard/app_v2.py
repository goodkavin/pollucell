import os
from os.path import isfile, join

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import mysql.connector
import configparser
import objectpath
import json
import requests

from components import make_dash_table

app = dash.Dash(__name__)

server = app.server

# Load data
df = pd.read_csv('../sampledata/rsl_pm25.csv') #relative path - need to execute app inside /dashboard
#print(df)

config = configparser.ConfigParser()
config.read('config.ini')

mydb = mysql.connector.connect(
  host=config['DATABASE']['HOST'],
  user=config['DATABASE']['USER'],
  passwd=config['DATABASE']['PASSWORD'],
  database="pollucell"
)

#print(mydb)

df2 = pd.read_sql('SELECT * FROM TestTable', con=mydb)
#print(df2)

pathway = '../data/'
files = [f for f in os.listdir(pathway) if isfile(join(pathway, f))]

# Create app layout
app.layout = html.Div(className="container", children=[
    html.Div(
        className="app-header",
        children=[
            html.H1('PolluSmartCell Dashboard')
        ]
    ),

    html.Div(
        children=
        html.H5('''
        Using Wireless Communication To Detect
        Polluted Atmospheric Condition
        ''')
    ),

    dcc.Dropdown(id='filename',
                 options=[
                     {'label': i, 'value': i} for i in files
                 ],
                 value=files[0]
    ),

    dcc.Graph(id='temperature-graph'),

    dcc.Dropdown(id='pm',
        options=[
            {'label': 'PM 2.5', 'value': 'PM25'},
            {'label': 'PM 10', 'value': 'PM10'},
           # {'label': 'O3', 'value': 'O3'},
           # {'label': 'CO', 'value': 'CO'},
            {'label': 'NO2', 'value': 'NO2'},
           # {'label': 'SO2', 'value': 'SO2'}
        ],
        value='PM25'
    ),

    dcc.Graph(id='pm-graph'),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                go.Scatter(
                    x=df['dateTime'],
                    y=df['Signal_strength'],
                    name='Signal strength'
                ),
                go.Scatter(
                    x=df['dateTime'],
                    y=df['value'],
                    name='PM2.5'
                )
           ],
            'layout': go.Layout(
                title='Signal strength vs PM2.5',
                xaxis={'title': 'Date and time'},
                yaxis={'title': 'Value'}
            )
        }
    ),
    html.Div(children=[
        html.H3('MySQL: TestTable')
    ]),

    html.Div([
        dash_table.DataTable(
        id='test-table',
        columns=[{"name": i, "id": i} for i in df2.columns],
        data=df2.to_dict("rows"),
        )
    ]),

    dcc.Graph(
        id='example-graph-2',
        figure={
            'data': [
                go.Scatter(
                    x=df2['Column1'],
                    y=df2['Column2'],
                    name='x = Column1'
                ),
                go.Scatter(
                    x=df2['Column2'],
                    y=df2['Column1'],
                    name='x = Column2'
                )

            ],
            'layout': go.Layout(
                title='Graph From TestTable',
                xaxis={'title': 'x'},
                yaxis={'title': 'y'}
            )
        }
    )

])

@app.callback(
    Output(component_id='temperature-graph', component_property='figure'),
    [Input(component_id='filename', component_property='value')]
)
def update_figure(input_value):
    file = '../data/{}'.format(input_value)
    with open(file,'r') as f:
        targets_1 = [line for line in f if "mavlink_scaled_pressure_t" in line]

    df_1 = pd.DataFrame(targets_1, columns=["c"])
    df_1_2 = pd.DataFrame(df_1.c.str.split(',').tolist(),
                                   columns = ['c1','c2','c3','c4','c5','c6','c7','c8','c9','c10'
                                             ,'c11','c12','c13','c14','c15','c16','c17','c18','c19','c20'
                                             ,'c21','c22'])
    df_1_3 = df_1_2.filter(['c1','c14','c16','c18'], axis=1)
    df_1_4 = df_1_3.rename(index=str, columns={"c1": "datetime", "c14": "press_abs", "c16": "press_diff", "c18": "temperature"})
    df_1_4['datetime']= df_1_4['datetime'].astype('datetime64')
    df_1_4['press_abs']= df_1_4['press_abs'].astype('float')
    df_1_4['press_diff']= df_1_4['press_diff'].astype('float')
    df_1_4['temperature']= df_1_4['temperature'].astype('float')

    fig = {
        'data': [
            {'x': df_1_4['datetime'],
            'y': df_1_4['temperature'],
            'name': 'Temperature'
            }],
            'layout': {
                'xaxis': {'title': 'datetime'},
                'yaxis': {'title': "value"}
            }
        }

    return fig

@app.callback(
   Output(component_id='pm-graph', component_property='figure'),
   [Input(component_id='pm', component_property='value'),
    Input(component_id='filename', component_property='value')])
def update_pm(input_pm, input_value):
    file = '../data/{}'.format(input_value)
    with open(file,'r') as f:
        targets_1 = [line for line in f if "mavlink_scaled_pressure_t" in line]

    df_1 = pd.DataFrame(targets_1, columns=["c"])
    df_1_2 = pd.DataFrame(df_1.c.str.split(',').tolist(),
                                   columns = ['c1','c2','c3','c4','c5','c6','c7','c8','c9','c10'
                                             ,'c11','c12','c13','c14','c15','c16','c17','c18','c19','c20'
                                             ,'c21','c22'])
    df_1_3 = df_1_2.filter(['c1','c14','c16','c18'], axis=1)
    df_1_4 = df_1_3.rename(index=str, columns={"c1": "datetime", "c14": "press_abs", "c16": "press_diff", "c18": "temperature"})
    df_1_4['datetime']= df_1_4['datetime'].astype('datetime64')
    df_1_4['press_abs']= df_1_4['press_abs'].astype('float')
    df_1_4['press_diff']= df_1_4['press_diff'].astype('float')
    df_1_4['temperature']= df_1_4['temperature'].astype('float')

    uav_start = df_1_4.datetime.min()
    uav_end = df_1_4.datetime.max()
    uav_date = df_1_4.datetime[0]
    sdate = uav_date + pd.DateOffset(days=-1)
    sdate = sdate.strftime('%y-%m-%d')
    edate = uav_date + pd.DateOffset(days=1)
    edate = edate.strftime('%y-%m-%d')
    stationId = "50t"
    param = input_pm
    stime = "00"
    etime = "24"
    r = requests.get('http://air4thai.pcd.go.th/webV2/history/api/data.php?'
                     +'stationID='+stationId
                     +'&param='+param
                     +'&type=hr&sdate='+sdate
                     +'&edate='+edate
                     +'&stime='+stime
                     +'&etime='+etime)
    source = r.json()
    data = source['stations'][0]['data']
    df1 = pd.DataFrame(data)
    df1.columns = ['datetime', 'value']

    trace = go.Scatter(
        x = df1['datetime'],
        y = df1['value']
    )

    data2 = [trace]

    layout = {
        'shapes': [
            # highlight during uav flight
            {
                'type': 'rect',
                # x-reference is assigned to the x-values
                'xref': 'x',
                # y-reference is assigned to the plot paper [0,1]
                'yref': 'paper',
                'x0': uav_start,
                'y0': 0,
                'x1': uav_end,
                'y1': 1,
                'fillcolor': 'rgba(50, 171, 96, 0.6)',
                'line': {
                    'width': 0,
                }
            }
        ]
    }

    fig={'data': data2, 'layout': layout}
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
