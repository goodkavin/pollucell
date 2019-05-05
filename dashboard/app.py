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

from components import make_dash_table

app = dash.Dash(__name__)

server = app.server

# Load data
df = pd.read_csv('../sampledata/rsl_pm25.csv') #relative path - need to execute app inside /dashboard
#print(df)

mydb = mysql.connector.connect(
  host="mysql.cdcmjtosctu0.us-east-2.rds.amazonaws.com",
  user="mm",
  passwd="connect2019",
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
    ),

    dcc.Graph(id='temperature-graph'),

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

if __name__ == '__main__':
    app.run_server(debug=True)
