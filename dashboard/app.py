import os
from os.path import isfile, join

import dash
import dash_auth
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
import numpy as np

from components import make_dash_table

app = dash.Dash(__name__)

# In production, keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = [
    ['tinv', '7A483g']
]

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

server = app.server

config = configparser.ConfigParser()
config.read('config.ini')

mydb = mysql.connector.connect(
  host=config['DATABASE']['HOST'],
  user=config['DATABASE']['USER'],
  passwd=config['DATABASE']['PASSWORD'],
  database="pollucell"
)

pathway = '../data/balloon/'
files = [f for f in os.listdir(pathway) if isfile(join(pathway, f))]

# Create app layout
app.layout = html.Div(className="container", children=[
    html.Div(
        className="app-header",
        children=[
            html.H1('Temperature Inversion Dashboard')
        ]
    ),

    html.Div(
        children=
        html.H5('''
        Temperature Inversion Measurements From Tethered Balloon 
        ''')
    ),

    dcc.Dropdown(id='filename',
                 options=[
                     {'label': i, 'value': i} for i in files
                 ],
                 value=files[0],
    ),

    html.Div(
        children=
        html.H3('''
        Overview
        ''')
    ),

    dcc.Graph(id='overview-graph'),

    html.Table(id='metadata', children=[
        html.Tr([html.Td(['Name']), html.Td(id='meta-name')]),
        html.Tr([html.Td(['Date']), html.Td(id='meta-date')]),
        html.Tr([html.Td(['Time']), html.Td(id='meta-time')]),
        html.Tr([html.Td(['Latitude']), html.Td(id='meta-lat')]),
        html.Tr([html.Td(['Longitude']), html.Td(id='meta-long')]),
    ],
    style={'margin-left':'auto',
           'margin-right':'auto'}),

    html.Div(
        children=
        html.H3('''
        Temperature Inversion
        ''')
    ),

    dcc.Graph(id='tinv-graph'),

    html.Div(id='tinv-prediction',
        style={'text-align':'center'}),

    html.Div(
        children=
        html.H3('''
        Pollution Comparison
        ''')
    ),

    dcc.Graph(id='pm-graph'),

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

    html.Table(children=[
        html.Tr([html.Td(['Station Name']), html.Td(id='pm-name')]),
        html.Tr([html.Td(['Station ID']), html.Td(id='pm-id')]),
        html.Tr([html.Td(['Latitude']), html.Td(id='pm-lat')]),
        html.Tr([html.Td(['Longitude']), html.Td(id='pm-long')]),
        ],
        style={'margin-left':'auto',
               'margin-right':'auto'}),
])

@app.callback(
    Output(component_id='overview-graph', component_property='figure'),
    [Input(component_id='filename', component_property='value')]
)
def update_overview(input_value):
    file = '../data/balloon/{}'.format(input_value)
    df = pd.read_csv(file, sep=",")
    trace1 = go.Scatter(
              x= df['datetime'],
              y= df['temp'],
              name= 'Temperature (°C)'
             )
    trace2 = go.Scatter(
              x= df['datetime'],
              y= df['alt'],
              name= 'Altitude (m)'
             )

    data = [trace1, trace2]

    fig = {
            'data': data,
            'layout': {
                      'xaxis': {'title': 'Time'},
                      'yaxis': {'title': "Value"}
                      }
          }
    return fig

@app.callback(
    [Output('meta-name', 'children'),
     Output('meta-date', 'children'),
     Output('meta-time', 'children'),
     Output('meta-lat', 'children'),
     Output('meta-long', 'children')],
    [Input(component_id='filename', component_property='value')]
)
def update_metadata(input_value):
    file = '../data/balloon/{}'.format(input_value)
    df = pd.read_csv(file, sep=',')
    name = "Balloon Launch at Main Grass Field CU"
    df['datetime'] =  pd.to_datetime(df['datetime'])
    time = df['datetime'].min().strftime("%H:%M:%S")+" - "+df['datetime'].max().strftime("%H:%M:%S")
    date = df['datetime'].min().strftime("%d/%m/%y")
    clat = 13.738548
    clong = 100.530846

    return name, date, time, clat, clong 

@app.callback(
    Output(component_id='tinv-graph', component_property='figure'),
    [Input(component_id='filename', component_property='value')]
)
def update_tinv(input_value):
    file = '../data/balloon/{}'.format(input_value)
    df = pd.read_csv(file, sep=",")
    bins = np.arange(0,df['alt'].max() + 1, 1)
    df['bins'] = pd.cut(df['alt'], bins, labels=False)
    df = df.groupby('bins').mean()
    iroc = -df['temp'].diff(periods=5) / df['alt'].diff(periods=5)
    tinv_start = iroc.idxmin()-5
    tinv_end = iroc.idxmin()+5
    trace1 = go.Scatter(
              x= df.index,
              y= df['temp'],
              name= 'tinv'
             )

    data = [trace1]

    fig = {
           'data': data,
           'layout': {
                     'xaxis': {'title': 'Altitude (m)'},
                     'yaxis': {'title': 'Temperature (°C)'},
                     'shapes': [
                               # highlight during uav flight
                               {
                                     'type': 'rect',
                                     # x-reference is assigned to the x-values
                                     'xref': 'x',
                                     # y-reference is assigned to the plot paper [0,1]
                                     'yref': 'paper',
                                     'x0': tinv_start,
                                     'y0': 0,
                                     'x1': tinv_end,
                                     'y1': 1,
                                     'fillcolor': 'rgba(255, 131, 16, 0.2)',
                                     'line': {
                                         'width': 0,
                                     }
                               }
                               ]
                       },
           }
    return fig

@app.callback(
    Output('tinv-prediction', 'children'),
    [Input(component_id='filename', component_property='value')]
)
def update_metadata(input_value):
    file = '../data/balloon/{}'.format(input_value)
    df = pd.read_csv(file, sep=',')
    df['datetime'] =  pd.to_datetime(df['datetime'])
    bins = np.arange(0,df['alt'].max() + 1, 1)
    df['bins'] = pd.cut(df['alt'], bins, labels=False)
    df = df.groupby('bins').mean()
    iroc = -df['temp'].diff(periods=5) / df['alt'].diff(periods=5)
    if iroc.min()<-0.1:
        tinv_alt = iroc.idxmin()
        return "Suspect TINV layer around "+str(tinv_alt)+" meters"
    else:
        return "No TINV layer found" 


@app.callback(
   Output(component_id='pm-graph', component_property='figure'),
   [Input(component_id='pm', component_property='value'),
    Input(component_id='filename', component_property='value')])
def update_pm(input_pm, input_value):
    file = '../data/balloon/{}'.format(input_value)
    df = pd.read_csv(file)
    df['datetime'] =  pd.to_datetime(df['datetime'])
    uav_start = df.datetime.min()
    uav_end = df.datetime.max()
    uav_date = df.datetime[0]
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
                'fillcolor': 'rgba(10, 171, 46, 0.8)',
                'line': {
                    'width': 0,
                }
            }
        ]
    }

    fig={'data': data2, 'layout': layout}
    return fig

@app.callback(
        [Output('pm-name', 'children'),
        Output('pm-id', 'children'),
        Output('pm-lat', 'children'),
        Output('pm-long', 'children')],
        [Input(component_id='filename', component_property='value')])
def update_pm_meta(input_value):
    name = "โรงพยาบาลจุฬาลงกรณ์"
    sid = '50t'
    slat = '13.731576', 
    slong = '100.534390'
    return name, sid, slat, slong

if __name__ == '__main__':
    app.run_server(debug=True)
