# dashboard.py
from dash import html
import dash_bootstrap_components as dbc
from dash import dash_table
import json

def layout_dashboard(usuario):
    # Exemplo: carrega dados do result.json (ou troque para buscar do banco)
    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []

    return html.Div([
    dbc.Row([
        html.H2('Análise de Estoque', className='text-primary text-center fs-4 mt-3'),
    ]),
    html.Br(),
    html.Div(  # wrapper centralizador
        dash_table.DataTable(
            data=data,
            columns=[{'id': c, 'name': c} for c in data[0].keys()] if data else [],
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
            style_table={
                'overflowX': 'auto',    
                'width': '1750px',
                'height': '500px',
                'overflowY': 'scroll',
                # Remova qualquer margin aqui
            },
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
            style_header={
                'fontWeight': 'bold',
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#eee'},
            ],
        ),
        style={
            'display': 'flex',
            'justifyContent': 'center',
            # 'alignItems': 'center',  # Se quiser centralizar verticalmente também
        }
    ),
])