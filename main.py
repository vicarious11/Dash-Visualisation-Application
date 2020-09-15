import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html

import flask
import glob
import os

from copy import deepcopy

import plotly.graph_objects as go

input_image_directory = './Input/'
output_image_directory = './Output/'

list_of_input_images = [os.path.basename(x) for x in glob.glob('{}*.png'.format(input_image_directory))]
list_of_output_images = [os.path.basename(x) for x in glob.glob('{}*.png'.format(input_image_directory))]

static_image_route = '/static/'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

zoomed_output_image = None
zoomed_input_image = None

app.layout = html.Div([

    dbc.Row(
        dbc.Col(html.H3("Input - Output Image visualisation"),
                width={'size': 6, 'offset': 3},
                ),
    ),

    dbc.Row(
        dbc.Col(
            html.Div("Select Input Image and Output Image. Zoom in Input, results in auto zoom in output. Annotate,"
                     "Image using draw rectangle option in the figure."),
            width=6
        )
    ),
    dbc.Row(
        [
            dbc.Col(dcc.Dropdown(
                id='input_image-dropdown', placeholder='Select Input Image',
                options=[{'label': i, 'value': i} for i in list_of_input_images],
            ), width={'size': 4, 'offset': 1})
            ,

            dbc.Col(dcc.Dropdown(
                id='output_image-dropdown', placeholder='Select Output Image',
                options=[{'label': i, 'value': i} for i in list_of_output_images]
            ), width={'size': 4, 'offset': 1})], no_gutters=True),

    dbc.Row([
            dbc.Col(html.Div(
                children=[dcc.Graph(figure={}, id='input_img')], id='input_image_div'),
                width=6, md={'size': 4,  "offset": 1}
            ),
            dbc.Col(html.Div(
                children=[dcc.Graph(figure={}, id='output_img')], id='output_image_div')
                , width=6, md={'size': 4, "offset": 1}
            )
        ])
    ])


def create_image_with_functionality(static_image_route, value):
    # Create figure
    fig = go.Figure()

    # Constants
    img_width = 900
    img_height = 900
    scale_factor = 0.5

    # Add invisible scatter trace.
    # This trace is added to help the autoresize logic work.
    fig.add_trace(
        go.Scatter(
            x=[0, img_width * scale_factor],
            y=[0, img_height * scale_factor],
            mode="markers",
            marker_opacity=0
        )
    )

    # Configure axes
    fig.update_xaxes(
        visible=False,
        range=[0, img_width * scale_factor]
    )

    fig.update_yaxes(
        visible=False,
        range=[0, img_height * scale_factor],
        scaleanchor="x"
    )

    # Add image
    fig.add_layout_image(
        dict(
            x=0,
            sizex=img_width * scale_factor,
            y=img_height * scale_factor,
            sizey=img_height * scale_factor,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source=static_image_route + value)
    )

    # Configure other layout
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        dragmode='drawrect',
        newshape=dict(line_color='cyan'),
        title_text='Drag to add annotations - use modebar to change drawing tool'
    )

    # Disable the autosize on double click because it adds unwanted margins around the image
    # More detail: https://plotly.com/python/configuration-options/
    return fig


@app.callback(
    [
        dash.dependencies.Output(component_id="input_image_div", component_property='children'),
        dash.dependencies.Output(component_id="output_image_div", component_property='children')
    ],
    [
        dash.dependencies.Input(component_id='input_image-dropdown', component_property='value'),
        dash.dependencies.Input(component_id='output_image-dropdown', component_property='value')
    ])
def update_input__output_image(input_value, output_value):
    if input_value is None or output_value is None:
        raise dash.exceptions.PreventUpdate
    else:
        return [dcc.Graph(figure=create_image_with_functionality(static_image_route, input_value), id="input_img",config=dict(modeBarButtonsToAdd=['drawline',
                                                                                'drawopenpath',
                                                                                'drawclosedpath',
                                                                                'drawcircle',
                                                                                'drawrect',
                                                                                'eraseshape'
                                                                                ]))], \
               [dcc.Graph(figure=create_image_with_functionality(static_image_route, output_value), id="output_img",
                                                                config=dict(modeBarButtonsToAdd=['drawline',
                                                                                'drawopenpath',
                                                                                'drawclosedpath',
                                                                                'drawcircle',
                                                                                'drawrect',
                                                                                'eraseshape'
                                                                                ]))]


@app.callback(
    dash.dependencies.Output(component_id="output_img", component_property='figure'),
    [
        dash.dependencies.Input(component_id="input_img",
                                component_property='relayoutData'),
    ],
    dash.dependencies.State(component_id="output_img", component_property='figure')
)
def update_output_image(relayout_data, output_fig):
    try:
        output_fig['layout'].update(
            {
                'xaxis': {'range': [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]},
                'yaxis': {'range': [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']]
                          }})
    except:
        pass
    return output_fig



# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<image_path>.png'.format(static_image_route))
def serve_input_image(image_path):
    image_name = '{}.png'.format(image_path)
    if image_name not in list_of_input_images:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    return flask.send_from_directory(input_image_directory, image_name)


# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<image_path>.png'.format(static_image_route))
def serve_output_image(image_path):
    image_name = '{}.png'.format(image_path)
    if image_name not in list_of_output_images:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    return flask.send_from_directory(output_image_directory, image_name)


if __name__ == '__main__':
    app.run_server(debug=True)