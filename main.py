import dash_bootstrap_components as dbc
from dash import Dash, dash_table, html
import json

# Tenta carregar os dados do arquivo 'result.json'
try:
    with open('result.json', 'r') as f:
        data = json.load(f)
except Exception as e:
    print("Erro ao carregar 'result.json':", e)
    data = []

app = Dash(
    external_stylesheets=[dbc.themes.CERULEAN],
    #requests_pathname_prefix='/dashboard/',
)

server = app.server

# Se data existe, monta a tabela. Se não, mostra mensagem amigável.
layout_table = (
    dash_table.DataTable(
        data=data,
        columns=[{'id': c, 'name': c} for c in data[0].keys()],
        editable=False,
        filter_action='native',
        filter_options={'placeholder_text': 'Filtro...'},
        sort_action='native',
        sort_mode='multi',
        row_deletable=False,
        cell_selectable=False,
        page_action='native',
        page_size=50,
        fixed_rows={'headers': True},
        style_table={'overflowX': 'auto'},
        style_as_list_view=True,
        style_cell={
            'padding': '5px',
            'backgroundColor': '#fff',
            'textAlign': 'center',
            'minWidth': 150,
            'maxWidth': 150,
            'width': 150,
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        },
        style_header={'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#eee'},
        ],
    )
    if data
    else html.P("Não há dados para exibir ou o arquivo 'result.json' está vazio/inválido.", style={"color": "red", "fontWeight": "bold"})
)

app.layout = dbc.Container(
    [
        dbc.Row([
            html.H1(
                'Análise de Estoque',
                className='text-primary text-center fs-3 mt-3',
            ),
        ]),
        html.Br(),
        layout_table,
        html.Hr(),
    ],
    fluid=True,
)

if __name__ == '__main__':
    app.run(debug=True, port=8050)