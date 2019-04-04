# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
        'background': '#FFFFFF',
        'text': '#7FDBFF'
}

df = pd.read_csv('~/Documents/GitHub/pollucell/sampledata/rsl_pm25.csv') #local path

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
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
