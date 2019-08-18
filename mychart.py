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
    html.Button(id='submit-button', n_clicks=0, children='update'),
    dcc.Graph(id="my-graph1"),
    dcc.Graph(id="my-graph2"),
    dcc.Graph(id="my-graph3"),
    dcc.Graph(id="my-graph4")    
    #dcc.Interval(id='graph_update', interval=5000)
], className="container")

@app.callback(
    [Output("my-graph1", 'figure'),
    Output("my-graph2", 'figure'),
    Output("my-graph3", 'figure'),
    Output("my-graph4", 'figure')],
    [Input('submit-button', 'n_clicks')])
def graph_update(n_clicks):
    print(n_clicks)
    con = sqlite3.connect('mybot.db')
    data=pd.read_sql_query("SELECT * FROM upbit_premium",con)
    data = data.set_index(pd.DatetimeIndex(data['date']))
    df1 = data['KRW2USD'].resample('5Min').ohlc()
    df2 = data['USD2KRW'].resample('5Min').ohlc()
    df3 = data['KRW2USD_ETH'].resample('5Min').ohlc()
    df4 = data['USD2KRW_ETH'].resample('5Min').ohlc()
    
    trace1 = go.Candlestick(x=df1.index,open=df1['open'],high=df1['high'],low=df1['low'],close=df1['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace2 = go.Candlestick(x=df2.index,open=df2['open'],high=df2['high'],low=df2['low'],close=df2['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace3 = go.Candlestick(x=df3.index,open=df3['open'],high=df3['high'],low=df3['low'],close=df3['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace4 = go.Candlestick(x=df4.index,open=df4['open'],high=df4['high'],low=df4['low'],close=df4['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})                       
    return {'data': [trace1], 'layout': go.Layout(title=f"KRW2USD")}, {'data': [trace2], 'layout': go.Layout(title=f"USD2KRW")}, {'data': [trace3], 'layout': go.Layout(title=f"KRW2USD_ETH")},{'data': [trace4], 'layout': go.Layout(title=f"USD2KRW_ETH")}
    


if __name__ == '__main__':
    app.run_server(host='0.0.0.0') #debug=True)#,