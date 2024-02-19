from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template

import plotly.express as px
import pandas as pd


resorts = (
    pd.read_csv("./resorts.csv", encoding="ISO-8859-1")
    .assign(
        country_elevation_rank=lambda x: x.groupby("Country", as_index=False)[
            "Highest point"].rank(ascending=False),
        country_price_rank=lambda x: x.groupby("Country", as_index=False)[
            "Price"].rank(ascending=False),
        country_slope_rank=lambda x: x.groupby("Country", as_index=False)[
            "Total slopes"].rank(ascending=False),
        country_cannon_rank=lambda x: x.groupby("Country", as_index=False)[
            "Snow cannons"].rank(ascending=False),
    ))

resorts['Price'] = resorts['Price'].replace(0, 1)

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"

app = Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO, dbc_css])

server = app.server

load_figure_template('SUPERHERO')

app.layout = html.Div([
    dcc.Tabs(
        id='tabs',
        value='tab-1',
        className='dbc',
        children=[
            dcc.Tab(
                label='Resort Map',
                value='tab-1',
                children=[
                    html.H2(id='map_header', style={'textAlign': 'center'}),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card([
                                    html.Span('Filter By Price'),
                                    dcc.Slider(
                                        id='price',
                                        min=20,
                                        max=160,
                                        step=20,
                                        value=60
                                    ),
                                    dbc.Card(
                                        dcc.Checklist(
                                            id='check_list',
                                            options=[
                                                {'label': 'Night Skiing',
                                                    'value': 'Nightskiing'},
                                                {'label': 'Snow Parks',
                                                    'value': 'Snowparks'},
                                                {'label': 'Summer Skiing',
                                                    'value': 'Summer skiing'}
                                            ],
                                            style={'marginLeft': '1rem'},
                                        )
                                    )
                                ]),
                                width=3
                            ),
                            dbc.Col(dbc.Card(dcc.Graph(id='graph')))
                        ]
                    )
                ]
            ),
            dcc.Tab(
                label='Country Profiler',
                value='tab-2',
                children=[
                    html.H2('Create chart to view data',
                            id='bar_header', style={'textAlign': 'center'}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                html.Span('Select Continent:'),
                                dcc.Dropdown(
                                    className='dbc',
                                    id='continent',
                                    options=resorts.Continent.unique(),
                                    value='North America',
                                )
                            ], style={'marginBottom': '1rem'}),
                            dbc.Card([
                                html.Span('Select Country:'),
                                dcc.Dropdown(
                                    className='dbc',
                                    id='country',
                                    value='United States'
                                )
                            ], style={'marginBottom': '1rem'}),
                            dbc.Card([
                                html.Span('Select Metric To Plot:'),
                                dcc.Dropdown(
                                    className='dbc',
                                    id='metric',
                                    options=['Price',
                                             'Highest point',
                                             'Lowest point',
                                             'Total slopes',
                                             'Total lifts'],
                                    value='Price'
                                )
                            ], style={'marginBottom': '1rem'}),
                            html.Button("Create Chart", id='confirm_btn')
                        ]),
                        dbc.Col(
                            dbc.Card(
                                dcc.Graph(id='bar_chart')
                            ),
                            width=5
                        ),
                        dbc.Col([
                            html.H4('Resort Rankings'),
                            dbc.Card(
                                html.Span(id='resort_name'),
                                style={'textAlign': 'center',
                                       'fontSize': '18px'}
                            ),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card(html.Span(id='elevation_rank')),
                                    dbc.Card(html.Span(id='price_rank')),

                                ]),
                                dbc.Col([
                                    dbc.Card(html.Span(id='scope_rank')),
                                    dbc.Card(html.Span(id='cannon_rank')),
                                ])
                            ])
                        ])
                    ])
                ]
            )
        ]
    )
])


@app.callback(
    Output('country', 'options'),
    Input('continent', 'value')
)
def choose_country(continent):
    countries = resorts.query("Continent == @continent")['Country'].unique()
    return countries


@app.callback(
    [
        Output('map_header', 'children'),
        Output('graph', 'figure')
    ],
    [
        Input('price', 'value'),
        Input('check_list', 'value')
    ]
)
def update_mapbox(price, selections):
    if selections == ['Nightskiing']:
        df = resorts.query("Price < @price and Nightskiing == 'Yes'")
    elif selections == ['Summer skiing']:
        df = resorts.query("Price < @price and `Summer skiing` == 'Yes'")
    elif selections == ['Snowparks']:
        df = resorts.query("Price < @price and Snowparks == 'Yes'")
    elif selections in ['Nightskiing', 'Snowparks']:
        df = resorts.query(
            "(Price < @price) and (Nightskiing == 'Yes') and (Snowparks == 'Yes')")
    elif selections in ['Nightskiing', 'Snowparks', 'Summer skiing']:
        df = resorts.query(
            "(Price < @price) and (Nightskiing == 'Yes') and (Snowparks == 'Yes') and (`Summer skiing` == 'Yes')")  # noqa: E501
    else:
        df = resorts.query('Price < @price')

    fig = px.density_mapbox(
        df,
        lat='Latitude',
        lon='Longitude',
        z='Price',
        radius=20,
        center={'lat': 44.5, 'lon': -97.5},
        zoom=1.85,
        mapbox_style='open-street-map',
        color_continuous_scale='Viridis'
    )
    header = f"Resorts less than ${price}/night"
    return header, fig


@app.callback(
    Output('bar_header', 'children'),
    Output('bar_chart', 'figure'),
    Output('confirm_btn', 'n_clicks'),
    Input('continent', 'value'),
    Input('country', 'value'),
    Input('metric', 'value'),
    Input('confirm_btn', 'n_clicks')
)
def update_barchart(continent, country, metric, clicks):
    if not clicks:
        raise PreventUpdate
    df = (
        resorts
        .query("Continent == @continent and Country == @country")
        [['Resort', metric]]
        .sort_values(metric, ascending=False)
        .head()
    )

    fig = px.bar(
        df,
        x='Resort',
        y=metric,
        hover_name='Resort',
        custom_data=['Resort']
    ).update_layout(title={'text': 'Hover Over Bars For Info', 'x': 0.5})

    title = f"Top Resorts in {country} by {metric}"

    return title, fig, 0


@app.callback(
    Output('resort_name', 'children'),
    Output('elevation_rank', 'children'),
    Output('price_rank', 'children'),
    Output('scope_rank', 'children'),
    Output('cannon_rank', 'children'),
    Input('bar_chart', 'hoverData')
)
def show_report(hoverData):
    if not hoverData:
        raise PreventUpdate

    resort_name = hoverData['points'][0]['label']

    df = (
        resorts
        .query("Resort == @resort_name")
        [[
            'country_elevation_rank',
            'country_price_rank',
            'country_slope_rank',
            'country_cannon_rank'
        ]]
    )

    return (
        f"Name: {resort_name}",
        f"Elevation: #{int(df['country_elevation_rank'].values[0])}",
        f"Price: #{int(df['country_price_rank'].values[0])}",
        f"Slope: #{int(df['country_slope_rank'].values[0])}",
        f"Cannon: #{int(df['country_cannon_rank'].values[0])}"
    )


if __name__ == '__main__':
    app.run()
