import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
#from app import app
import sqlite3

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([html.H1("Tesla Stock Price")], style={'textAlign': "center"}),
    dcc.Graph(id="my-graph1"),
    dcc.Graph(id="my-graph2"),
    html.Button(id='submit-button', n_clicks=0, children='update')
    #dcc.Interval(id='graph_update', interval=5000)
], className="container")

@app.callback(
    [Output("my-graph1", 'figure'),
    Output("my-graph2", 'figure')],
    [Input('submit-button', 'n_clicks')])
def graph_update(n_clicks):
    print(n_clicks)
    con = sqlite3.connect('test.db')
    data=pd.read_sql_query("SELECT * FROM coin_premium",con)
    data = data.set_index(pd.DatetimeIndex(data['date']))
    df1 = data['KRW2USD'].resample('5Min').ohlc()
    df2 = data['USD2KRW'].resample('5Min').ohlc()
    
    trace1 = go.Candlestick(x=df1.index,open=df1['open'],high=df1['high'],low=df1['low'],close=df1['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace2 = go.Candlestick(x=df2.index,open=df2['open'],high=df2['high'],low=df2['low'],close=df2['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    return {'data': [trace1], 'layout': go.Layout(title=f"KRW2USD")}, {'data': [trace2], 'layout': go.Layout(title=f"USD2KRW")}
    


if __name__ == '__main__':
    app.run_server(host='0.0.0.0') #debug=True)#,