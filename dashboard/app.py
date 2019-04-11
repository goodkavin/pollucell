# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
import mysql.connector

from components import make_dash_table

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
        'background': '#FFFFFF',
        'text': '#7FDBFF'
}

# Load data
df = pd.read_csv('~/Documents/GitHub/pollucell/sampledata/rsl_pm25.csv') #local path
print(df)

mydb = mysql.connector.connect(
  host="mysql.cdcmjtosctu0.us-east-2.rds.amazonaws.com",
  user="mm",
  passwd="connect2019",
  database="pollucell"
)

print(mydb)

df2 = pd.read_sql('SELECT * FROM TestTable', con=mydb)
print(df2)

# Create app layout
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(children='PolluSmartCell Dashboard'),

    html.Div(children='''
        PolluSmartCell: Using Wireless Communication To Detect Polluted Atmospheric Condition
    '''),

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
    html.Div([
        html.H2('MySQL: TestTable')
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

if __name__ == '__main__':
    app.run_server(debug=True)
