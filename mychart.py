import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
#from app import app
import sqlite3
import datetime

app = dash.Dash(__name__)

app.layout = html.Div([   
    html.Br(), 
    html.Button(id='submit-button', n_clicks=0, children='update', style={
        'width': '30%',
        'font-size': '150%',
        'height': '50%'}),    
    dcc.RadioItems(
                id='period',
                options=[{'label': i, 'value': i} for i in ['day', 'weak', 'month', '6month', 'year', 'all']],
                value='day',
                labelStyle={'display': 'inline-block', 'font-size':'150%'}
            ),
    html.Br(),
    dcc.Graph(id="my-graph1"),
    dcc.Graph(id="my-graph2"),
    dcc.Graph(id="my-graph3"),
    dcc.Graph(id="my-graph4"),
    dcc.Graph(id="my-graph5"),
    dcc.Graph(id="my-graph6")    
    #dcc.Interval(id='graph_update', interval=5000)
], className="container")

@app.callback(
    [Output("my-graph1", 'figure'),
    Output("my-graph2", 'figure'),
    Output("my-graph3", 'figure'),
    Output("my-graph4", 'figure'),
    Output("my-graph5", 'figure'),
    Output("my-graph6", 'figure')],
    [Input('submit-button', 'n_clicks'),
    Input('period', 'value')])
def graph_update(n_clicks, period):

    con = sqlite3.connect('mybot.db')
    if period == 'day':
        now = datetime.datetime.now() - datetime.timedelta(days=1)
        text = "SELECT * FROM upbit_premium WHERE date > '%s'"%now
        data=pd.read_sql_query(text,con)
    else:
        data=pd.read_sql_query("SELECT * FROM upbit_premium",con)
    weight=pd.read_sql_query("SELECT KRW2USD_weight,USD2KRW_weight FROM upbit_premium ORDER BY date DESC LIMIT 1",con)
    
    KRW2USD = float(weight['KRW2USD_weight'][0])
    USD2KRW = float(weight['USD2KRW_weight'][0])
    #print(type(KRW2USD))
    data = data.set_index(pd.DatetimeIndex(data['date']))
    df1 = data['KRW2USD'].resample('5Min').ohlc()
    df2 = data['USD2KRW'].resample('5Min').ohlc()
    df3 = data['KRW2USD_ETH'].resample('5Min').ohlc()
    df4 = data['USD2KRW_ETH'].resample('5Min').ohlc()
    df5 = data['KRW2USD_XRP'].resample('5Min').ohlc()
    df6 = data['USD2KRW_XRP'].resample('5Min').ohlc()
    
    trace1 = go.Candlestick(x=df1.index,open=df1['open'],high=df1['high'],low=df1['low'],close=df1['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace2 = go.Candlestick(x=df2.index,open=df2['open'],high=df2['high'],low=df2['low'],close=df2['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace3 = go.Candlestick(x=df3.index,open=df3['open'],high=df3['high'],low=df3['low'],close=df3['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace4 = go.Candlestick(x=df4.index,open=df4['open'],high=df4['high'],low=df4['low'],close=df4['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})                       
    trace5 = go.Candlestick(x=df5.index,open=df5['open'],high=df5['high'],low=df5['low'],close=df5['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})
    trace6 = go.Candlestick(x=df6.index,open=df6['open'],high=df6['high'],low=df6['low'],close=df6['close'],
                           increasing={'line': {'color': '#00CC94'}},decreasing={'line': {'color': '#F50030'}})                       
    return {'data': [trace1], 'layout': go.Layout(title=f"KRW2USD",\
            shapes = [dict(x0=0, x1=1, y0=KRW2USD, y1=KRW2USD, xref='paper', yref='y', line_width=2, line_color="rgb(200,0,0)")],\
            annotations=[dict(x=0, y=KRW2USD-0.1, xref='paper', yref='y', showarrow=False, xanchor='left', text='%.2f'%KRW2USD)])},\
            {'data': [trace2], 'layout': go.Layout(title=f"USD2KRW",\
            shapes = [dict(x0=0, x1=1, y0=USD2KRW, y1=USD2KRW, xref='paper', yref='y', line_width=2, line_color="rgb(0,0,200)")],\
            annotations=[dict(x=0, y=USD2KRW+0.1, xref='paper', yref='y', showarrow=False, xanchor='left', text='%.2f'%USD2KRW)])},\
            {'data': [trace3], 'layout': go.Layout(title=f"KRW2USD_ETH",\
            shapes = [dict(x0=0, x1=1, y0=KRW2USD, y1=KRW2USD, xref='paper', yref='y', line_width=2, line_color="rgb(200,0,0)")],\
            annotations=[dict(x=0, y=KRW2USD-0.1, xref='paper', yref='y', showarrow=False, xanchor='left', text='%.2f'%KRW2USD)])},\
            {'data': [trace4], 'layout': go.Layout(title=f"USD2KRW_ETH",\
            shapes = [dict(x0=0, x1=1, y0=USD2KRW, y1=USD2KRW, xref='paper', yref='y', line_width=2, line_color="rgb(0,0,200)")],\
            annotations=[dict(x=0, y=USD2KRW+0.1, xref='paper', yref='y', showarrow=False, xanchor='left', text='%.2f'%USD2KRW)])},\
            {'data': [trace5], 'layout': go.Layout(title=f"KRW2USD_XRP",\
            shapes = [dict(x0=0, x1=1, y0=KRW2USD, y1=KRW2USD, xref='paper', yref='y', line_width=2, line_color="rgb(200,0,0)")],\
            annotations=[dict(x=0, y=KRW2USD-0.1, xref='paper', yref='y', showarrow=False, xanchor='left', text='%.2f'%KRW2USD)])},\
            {'data': [trace6], 'layout': go.Layout(title=f"USD2KRW_XRP",\
            shapes = [dict(x0=0, x1=1, y0=USD2KRW, y1=USD2KRW, xref='paper', yref='y', line_width=2, line_color="rgb(0,0,200)")],\
            annotations=[dict(x=0, y=USD2KRW+0.1, xref='paper', yref='y', showarrow=False, xanchor='left', text='%.2f'%USD2KRW)])}
    


if __name__ == '__main__':
    app.run_server(host='0.0.0.0') #debug=True)#,