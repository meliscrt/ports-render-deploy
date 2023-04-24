import dash
from dash import dcc
from dash import html
from dash.dependencies import ClientsideFunction, Input, Output, State
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import geopandas as gpd
from shapely.geometry import Point

data = 'https://raw.githubusercontent.com/meliscrt/ports-dash-app/main/data/'
ports_data = pd.read_csv(data + 'ports.csv')

ports_data['PORT_POINT'] = [Point(xy) for xy in zip(ports_data.LONGITUDE, ports_data.LATITUDE)]

gdf = gpd.GeoDataFrame(ports_data, geometry='PORT_POINT')
gdf.crs = 'epsg:3857'

ship_cnt_df = pd.read_csv(data + 'ports_individual.csv')

pollutants = ['E_CO2_kg', 'E_SOx_kg', 'E_NOx_kg', 'E_PM_kg', 'E_CH4_kg', 'E_PM2.5_kg']

drop_pollutant = dcc.Dropdown(
        id = 'drop_pollutant',
        clearable=False,
        searchable=False,
        options=[{'label': 'E_CO2_kg', 'value': 'E_CO2_kg'},
                 {'label': 'E_SOx_kg', 'value': 'E_SOx_kg'},
                 {'label': 'E_NOx_kg', 'value': 'E_NOx_kg'},
                 {'label': 'E_PM_kg', 'value': 'E_PM_kg'},
                 {'label': 'E_CH4_kg', 'value': 'E_CH4_kg'},
                 {'label': 'E_PM2.5_kg', 'value': 'E_PM2.5_kg'}],
        value='E_CO2_kg',
        style= {'margin': '4px', 'box-shadow': '0px 0px #ebb36a', 'border-color': '#ebb36a'}
    )

customdata=np.stack(
  (pd.Series(gdf.index),
   gdf['PORT_NAME'],
   gdf['E_CO2_kg'].round(0).astype(str) + ' kg'),
  axis=-1
)

fig_poll = go.Figure(data=go.Scattergeo(lat = gdf.geometry.y,
                                                  lon = gdf.geometry.x,
                                        #text=gdf['E_CO2_kg'].round(0).astype(str) + ' kg',
                                        text = gdf['PORT_NAME'],
                                        customdata=customdata,
                                        hovertemplate="""<em>%{text}</em><br>Emission = %{customdata[2]} """,
                                                  marker = dict(
                                                      color = gdf['E_CO2_kg'],
                                                      colorscale = 'Teal',
                                                      # #reversescale = True,
                                                      opacity = 0.7,
                                                      size = gdf['E_CO2_kg']/50000
                                                  ),

                                                  ))
fig_poll.update_layout(#autosize=True,
                          hovermode='closest',
                          margin=dict(l=0, r=0, b=0, t=0),
    width=1550,
    height=850,
    geo=dict(bgcolor="#373737",
             showland=True,
             landcolor="#0C0C0C",
             subunitcolor="#373737",
             countrycolor="#373737",
             showlakes=True,
             lakecolor="#373737",
             showsubunits=True,
             showcountries=True,
             showcoastlines=False,
             showframe=False,
             resolution=50,
             projection=dict(
                 type='natural earth',
                 # rotation_lon = -100
             ),
             lataxis_range=[25, 70],
             lonaxis_range=[-25, 70]
             ),
    plot_bgcolor='#373737',
    paper_bgcolor="#373737"
)


port_name = ship_cnt_df['PORT_NAME'].unique().tolist()

#------------------------------------------------------ APP ------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets='')



filters_layout = html.Div([
    html.Div([
        html.P('Pollutant', id='preferencesText'),
        dcc.Dropdown(
            placeholder='Select Filters',
            id='dropdown',
            options=[{'label': 'E_CO2_kg', 'value': 'E_CO2_kg'},
                     {'label': 'E_SOx_kg', 'value': 'E_SOx_kg'},
                     {'label': 'E_NOx_kg', 'value': 'E_NOx_kg'},
                     {'label': 'E_PM_kg', 'value': 'E_PM_kg'},
                     {'label': 'E_CH4_kg', 'value': 'E_CH4_kg'},
                     {'label': 'E_PM2.5_kg', 'value': 'E_PM2.5_kg'}],
            value='E_CO2_kg',
            clearable=False,
            className='dropdownMenu',
            multi=False
        )
    ],
        id='dropdown_menu_applied_filters',
        # style={'width': '25%'},
        className="box"
    ),
],
    id="filters_container",
    className='box',
    style={'width': '25%', 'position': 'relative'}
)


selected_location_layout = html.Div([
    html.Div([
        html.H3("Insert selected location", id="title_selected_location"),
        html.Span('X', id="x_close_selection")
    ]),

    html.Div([
        html.Div([
            html.H4("Ship class - count"),
            #html.H6("Bubble size is proportional to the pollution level. Brush to highlight cities."),
            dcc.Graph(id='fig_bar'),
        ],
            className="plot_container_child",
        ),
    ],
        className="plots_container"
    ),

],
    id="selected_location",
    style={"display": "none",
           'color': 'white'}
)

hovered_location_layout = html.Div([
    html.Div([
        html.H3("city", id='hover_title'),
        dcc.Graph("fig_bar")
    ]),
],
    id="hovered_location",
    style={'display': 'none'},
)

app.layout = html.Div([filters_layout,
                       html.Div([
        html.Div(id="width", style={'display': 'none'}),  # Just to retrieve the width of the window
        html.Div(id="height", style={'display': 'none'}),  # Just to retrieve the height of the window
        html.Div([
            dcc.Graph(id='fig_map', clear_on_unhover=False, config={'doubleClick': 'reset'})
        ],
            style={'width': '100%', 'height': '100%'},
            className='background-map-container',

        ),
                           hovered_location_layout,
    ],
        id="map_container",
        style={'display': 'flex'}
    ),

                       #selected_location_layout,
    ], id='page-content',
    style={'position': 'relative', 'background-color':'#373737'})


#################
#   Figures     #
#################
selections = set()

@app.callback(
    Output(component_id='fig_map',component_property='figure'),
    [Input(component_id='dropdown', component_property='value')]
)


def update_map(dropdown_value):

    if not (dropdown_value == 'E_CO2_kg'):
        data_poll = go.Figure(data=go.Scattergeo(
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            text=gdf[dropdown_value].round(0).astype(str) + ' kg',
            #text=gdf['PORT_NAME'],
            customdata=customdata,
            hovertemplate="""<em>%{customdata[1]}</em><br>Emission = %{text} """,
            marker=dict(
                color=gdf[dropdown_value],
                colorscale = 'Teal',
                # colorscale = scl,
                # reversescale = True,
                opacity=0.7,
                size=gdf[dropdown_value] / 1000
            )
        ))


        data_poll.update_layout(#autosize=True,
            width=1550,
            height=850,
                              hovermode='closest',
                              margin=dict(
                                  l=0,
                                  r=0,
                                  b=0,
                                  t=0
                              ),

            geo=dict(bgcolor="#373737",
                     showland=True,
                     landcolor="#0C0C0C",
                     subunitcolor="#373737",
                     countrycolor="#373737",
                     showlakes=True,
                     lakecolor="#373737",
                     showsubunits=True,
                     showcountries=True,
                     showcoastlines=False,
                     showframe=False,
                     resolution=50,
                     projection=dict(
                         type='natural earth',
                         # rotation_lon = -100
                     ),
                     lataxis_range=[25, 70],
                     lonaxis_range=[-25, 70]
                     ),
            plot_bgcolor='#373737',
            paper_bgcolor="#373737"
        )

        fig_map = go.Figure(data=data_poll)
        #fig_map.update_geos(fitbounds="locations")
    else:
        data_poll = go.Figure(data=go.Scattergeo(
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            text=gdf[dropdown_value].round(0).astype(str) + ' kg',
            #text=gdf['PORT_NAME'],
            customdata=customdata,
            hovertemplate="""<em>%{customdata[1]}</em><br>Emission = %{text} """,
            marker=dict(
                color=gdf[dropdown_value],
                colorscale= 'Teal',
                # colorscale = scl,
                # reversescale = True,
                opacity=0.7,
                size=gdf[dropdown_value] / 50000
            )
        ))
        data_poll.update_layout(  # autosize=True,
            width=1550,
            height=850,
            hovermode='closest',
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=0
            ),
            geo=dict(bgcolor= "#373737",
                showland=True,
                landcolor="#0C0C0C",
                subunitcolor="#373737",
                countrycolor="#373737",
                showlakes=True,
                lakecolor="#373737",
                showsubunits=True,
                showcountries=True,
                showcoastlines=False,
                showframe=False,
                resolution=50,
                projection=dict(
                    type='natural earth',
                    # rotation_lon = -100
                ),
                     lataxis_range=[25, 70],
                     lonaxis_range=[-25, 70]
            ),
            plot_bgcolor='#373737',
            paper_bgcolor="#373737"
        )

        fig_map = go.Figure(data=fig_poll)
        #fig_map.update_geos(fitbounds="locations")
    return fig_map



hovered_location = ""

@app.callback([Output('hovered_location', "style"),
              Output('fig_bar', 'figure'),
              Output('hover_title', 'children')],
              [Input('fig_map', 'hoverData')])
def update_hovered_location(hoverData):
    global hovered_location
    location = ""
    if hoverData is not None:
        location = hoverData['points'][0]['text']
        print(location)
        if location != hovered_location:
            hovered_location = location
            style = {'display': 'block'}
        else:
            hovered_location = ""
            location = ""
            style = {'display': 'none'}
    else:
        hovered_location = ""
        location = ""
        style = {'display': 'none'}

    return style, update_fig_bar(location), location


def update_fig_bar(location):
    # categories
    #port_name = ship_cnt_df['PORT_NAME'].unique().tolist()
    if len(location) > 0:
        # print(n)
        print(f"value user chose: {location}")
        print(type(location))
        select_df = ship_cnt_df[ship_cnt_df["PORT_NAME"]==location]

        colors = ['rgb(234, 252, 253)', 'rgb(192, 229, 232)', 'rgb(149, 207, 216)', 'rgb(114, 184, 205)',
                         'rgb(89, 159, 196)', 'rgb(72, 134, 187)', 'rgb(62, 109, 178)', 'rgb(62, 83, 160)', 'rgb(58, 60, 125)', 'rgb(44, 42, 87)', 'rgb(25, 25, 51)', 'rgb(3, 5, 18)']

        fig_bar = make_subplots(
            rows=2, cols=1,
            #column_widths=[0.6, 0.4],
            row_heights=[0.4, 0.6],
            specs=[[{"type": "pie"}],
                   [{"type": "bar"}]]
        )

        # Pie chart
        fig_bar.add_trace(go.Pie(labels=select_df["SHIP_CLASS"], values=select_df["IMO"],
                                 marker_colors=colors,
                                 #marker=dict(colors=palette),
                                 textposition='inside', textinfo='percent+label',
                                 showlegend=False),
            row=1, col=1
        )

        # Bar chart
        fig_bar.add_trace(
            go.Bar( x=select_df['SHIP_CLASS'], y=select_df['E_CO2_kg'],
                    marker_color=colors,
                    #colorscale='gnbu',
                    showlegend=False),
            row=2, col=1
        )


        fig_bar.update_layout(
                #font_size=12,
                font=dict(
                family="Courier New, monospace",
                size=12,
                color="White"),
                margin=dict(
                    l=0,  # left margin
                    r=20,  # right margin
                    b=0,  # bottom margin
                    t=0,  # top margin
                ),
                height=800,
                width=300,
                paper_bgcolor='#373737',
                plot_bgcolor='#373737',
                font_color="white", showlegend = False,

                polar=dict(
                    bgcolor='rgba(0,0,0,0)',
                    angularaxis=dict(linewidth=3, showline=False, showticklabels=True),
                    radialaxis=dict(showline=False,
                                    showticklabels=False,
                                    linewidth=2,
                                    gridcolor='rgba(0,0,0,0)',
                                    gridwidth=2)))
        # #fig_bar.update_traces(textinfo="value+percent").update_layout(title_x=0.5)
        return fig_bar
    elif len(location) == 0:
        raise dash.exceptions.PreventUpdate



server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)

