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
import numpy as np

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

pathway = '../data/balloon/'
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

    dcc.Graph(id='overview-graph'),

    html.Div(id='metadata', children=[
        html.Tr([html.Td(['Name']), html.Td(id='meta-name')]),
        html.Tr([html.Td(['Date']), html.Td(id='meta-date')]),
        html.Tr([html.Td(['Time']), html.Td(id='meta-time')]),
        html.Tr([html.Td(['Latitude']), html.Td(id='meta-lat')]),
        html.Tr([html.Td(['Longitude']), html.Td(id='meta-long')]),
    ]),

    dcc.Graph(id='tinv-graph'),

    html.Div(id='tinv-prediction'),

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
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("rows"),
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
    Output(component_id='overview-graph', component_property='figure'),
    [Input(component_id='filename', component_property='value')]
)
def update_overview(input_value):
    file = '../data/balloon/{}'.format(input_value)
    df = pd.read_csv(file, sep=",")
    trace1 = go.Scatter(
              x= df['datetime'],
              y= df['temp'],
              name= 'Temperature'
             )
    trace2 = go.Scatter(
              x= df['datetime'],
              y= df['alt'],
              name= 'Altitude'
             )

    data = [trace1, trace2]

    fig = {
            'data': data,
            'layout': {
                      'xaxis': {'title': 'datetime'},
                      'yaxis': {'title': "value"}
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
    name = "Chula balloon"
    df['datetime'] =  pd.to_datetime(df['datetime'])
    time = df['datetime'].min().strftime("%H:%M:%S")+" - "+df['datetime'].max().strftime("%H:%M:%S")
    date = df['datetime'].min().strftime("%d/%m/%y")
    bins = np.arange(0,df['alt'].max() + 1, 1)
    df['bins'] = pd.cut(df['alt'], bins, labels=False)
    df = df.groupby('bins').mean()
    iroc = -df['temp'].diff(periods=5) / df['alt'].diff(periods=5)
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
                     'xaxis': {'title': 'alt'},
                     'yaxis': {'title': 'temp'},
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
    tinv_alt = iroc.idxmin()

    return "Suspect TINV layer around "+str(tinv_alt)+" meters"

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

if __name__ == '__main__':
    app.run_server(debug=True)
