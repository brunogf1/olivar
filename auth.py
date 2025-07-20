import dash
from dash import html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from passlib.hash import bcrypt

from database import Session
from models import User
from dashboard import layout_dashboard

# Formulário de login
def layout_login(msg_erro=''):
    return html.Div([
        html.H1("Login", className="text-center mt-4"),
        html.H3("Autenticação", style = {"marginTop":"70px"}),
        dbc.Form([
            dbc.Label("Usuário:", style={"marginTop":10}),
            dbc.Input(id="login-login", placeholder="Digite seu usuário", type="text"),
            dbc.Label("Senha:", style={"marginTop":10}),
            dbc.Input(id="password-login", placeholder="Digite sua senha", type="password"),
            dbc.Button("Entrar", id="btn-login", color="primary", style={"marginTop":15, "width": "100%"}),
        ]),
        html.Div(msg_erro, id='msg-erro', style={'color': 'red', 'marginTop': 10}),
    ])

def register_auth_callbacks(app):
    @app.callback(
        Output('area-login', 'children'),
        Output('area-dashboard', 'children'),
        Output('area-dashboard', 'style'),
        Output('usuario-logado', 'data'),
        Output('msg-erro', 'children'),
        Input('btn-login', 'n_clicks'),
        State('login-login', 'value'),
        State('password-login', 'value'),
        State('usuario-logado', 'data'),
        prevent_initial_call=True
    )
    def controladora(
        n_login,
        login, senha,
        usuario_atual
    ):
        ativador = ctx.triggered_id

        if ativador == 'btn-login':
            if not login or not senha:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Preencha usuário e senha!"
            with Session() as session:
                user = session.query(User).filter_by(login=login).first()
                if user and senha == user.password:
                    return "", layout_dashboard(login), {}, login, ""
                else:
                    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Usuário ou senha inválidos!"

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, ""