import os
import json
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)
from sqlalchemy import text
from database import Session
from werkzeug.security import check_password_hash

# CONFIGURAÇÕES DE USUÁRIO (ajuste conforme seu banco)
USER_TABLE = "users"            # exemplo: "users" ou "usuarios"
ID_COL = "id"
USERNAME_COL = "login"       # exemplo: "username" ou "login"
PASSWORD_COL = "password"  # exemplo: "password_hash" ou "senha"
ACTIVE_COL = None               # exemplo: "is_active" ou None se não tiver

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "troque-esta-secret-key")

# Cookies de sessão "por sessão" (não persistem após fechar o navegador)
app.config.update(
    SESSION_PERMANENT=False,
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # Em produção: True se usar HTTPS
)

def verify_password(stored_hash: str, provided_password: str) -> bool:
    try:
        if stored_hash and check_password_hash(stored_hash, provided_password):
            return True
    except Exception:
        pass
    return (stored_hash or "") == (provided_password or "")

def login_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Informe usuário e senha.", "danger")
            return redirect(url_for("login"))

        db = Session()
        try:
            sql = text(f"SELECT * FROM {USER_TABLE} WHERE {USERNAME_COL} = :u LIMIT 1")
            row = db.execute(sql, {"u": username}).mappings().first()
        finally:
            db.close()

        if not row:
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("login"))

        if ACTIVE_COL and row.get(ACTIVE_COL) in (0, "0", False, None):
            flash("Usuário inativo.", "danger")
            return redirect(url_for("login"))

        if not verify_password(str(row.get(PASSWORD_COL) or ""), password):
            flash("Senha inválida.", "danger")
            return redirect(url_for("login"))

        # Grava usuário na sessão do servidor (cookie de sessão)
        session["user"] = {"id": row.get(ID_COL), "username": row.get(USERNAME_COL)}
        # Redireciona para a rota que grava o flag por aba (sessionStorage)
        next_url = request.args.get("next") or url_for("index")
        session["after_login_next"] = next_url  # guarda para usar em /post-login
        return redirect(url_for("post_login"))

    return render_template("login.html")

@app.get("/post-login")
@login_required
def post_login():
    """
    Página transitória: grava o flag por aba (sessionStorage) e segue para a rota original.
    """
    next_url = session.pop("after_login_next", url_for("index"))
    return render_template("post_login.html", next_url=next_url)

@app.get("/logout")
def logout():
    session.pop("user", None)
    # Opcional: pegar "next" para redirecionar depois do logout
    next_url = request.args.get("next") or url_for("login")
    return redirect(next_url)

@app.get("/")
@login_required
def index():
    # Carrega dados do result.json
    try:
        with open("result.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []

    columns = list(data[0].keys()) if data else []
    return render_template("index.html", data=data, columns=columns, user=session.get("user"))

if __name__ == "__main__":
    app.run(debug=True, port=8050)