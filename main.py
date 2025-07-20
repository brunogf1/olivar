import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from models import Base
from database import engine
from auth import layout_login, register_auth_callbacks

Base.metadata.create_all(engine)  # Cria a tabela users se faltar

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CERULEAN],
    suppress_callback_exceptions=True
)
server = app.server

app.layout = dbc.Container(
    [
        dcc.Store(id='usuario-logado', storage_type='session'),
        dbc.Row([
            dbc.Col([
                html.Div(id='area-login', children=layout_login()),
                html.Div(id='area-dashboard', style={'display': 'none'}),
            ], width=6)
        ], justify="center")
    ], fluid=True,
)

register_auth_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True, port=8050)