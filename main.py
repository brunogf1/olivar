import os
import json
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from sqlalchemy import text, Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Session
from werkzeug.security import check_password_hash
from datetime import datetime
import enum

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "troque-esta-secret-key")

# Cookies de sessão "por sessão" (não persistem após fechar o navegador)
app.config.update(
    SESSION_PERMANENT=False,
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # Em produção: True se usar HTTPS
)

# ============ ENUM PARA STATUS ============
class StatusInventario(enum.Enum):
    ABERTO = "Aberto"
    FECHADO = "Fechado"

# ============ MODELO DE INVENTÁRIO ============
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Inventario(Base):
    __tablename__ = 'inventarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    status = Column(SQLEnum(StatusInventario), default=StatusInventario.ABERTO)
    criado_em = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'data_inicio': self.data_inicio.strftime('%d/%m/%Y %H:%M') if self.data_inicio else '-',
            'data_fim': self.data_fim.strftime('%d/%m/%Y %H:%M') if self.data_fim else '-',
            'status': self.status.value,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M')
        }

# Criar tabelas
Base.metadata.create_all(Session().get_bind())

# ============ DECORADOR DE AUTENTICAÇÃO ============
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

# ============ ROTAS DE AUTENTICAÇÃO ============
USER_TABLE = "users"
ID_COL = "id"
USERNAME_COL = "login"
PASSWORD_COL = "password"
ACTIVE_COL = None

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

        session["user"] = {"id": row.get(ID_COL), "username": row.get(USERNAME_COL)}
        next_url = request.args.get("next") or url_for("index")
        session["after_login_next"] = next_url
        return redirect(url_for("post_login"))

    return render_template("login.html")

@app.get("/post-login")
@login_required
def post_login():
    next_url = session.pop("after_login_next", url_for("index"))
    return render_template("post_login.html", next_url=next_url)

@app.get("/logout")
def logout():
    session.pop("user", None)
    next_url = request.args.get("next") or url_for("login")
    return redirect(next_url)

# ============ ROTAS PRINCIPAIS ============
@app.get("/")
@login_required
def index():
    try:
        with open("result.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []

    columns = list(data[0].keys()) if data else []
    return render_template("index.html", data=data, columns=columns, user=session.get("user"))

# ============ ROTAS DE INVENTÁRIOS ============
@app.route("/inventarios", methods=["GET"])
@login_required
def inventarios():
    """Página principal de inventários"""
    return render_template("inventarios.html", user=session.get("user"))

@app.route("/api/inventarios", methods=["GET"])
@login_required
def get_inventarios():
    """API: Retorna todos os inventários"""
    db = Session()
    try:
        inventarios_list = db.query(Inventario).order_by(Inventario.criado_em.desc()).all()
        return jsonify([inv.to_dict() for inv in inventarios_list])
    finally:
        db.close()

@app.route("/api/inventarios", methods=["POST"])
@login_required
def criar_inventario():
    """API: Cria um novo inventário"""
    data = request.get_json()
    nome = data.get("nome", "").strip()
    
    if not nome:
        return jsonify({"erro": "Nome do inventário é obrigatório"}), 400
    
    db = Session()
    try:
        novo_inv = Inventario(
            nome=nome,
            status=StatusInventario.ABERTO,
            data_inicio=None,
            data_fim=None
        )
        db.add(novo_inv)
        db.commit()
        return jsonify(novo_inv.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route("/api/inventarios/<int:inv_id>/abrir", methods=["PUT"])
@login_required
def abrir_inventario(inv_id):
    """API: Abre um inventário"""
    db = Session()
    try:
        inventario = db.query(Inventario).filter_by(id=inv_id).first()
        if not inventario:
            return jsonify({"erro": "Inventário não encontrado"}), 404
        
        if inventario.status == StatusInventario.ABERTO:
            return jsonify({"erro": "Inventário já está aberto"}), 400
        
        inventario.status = StatusInventario.ABERTO
        if not inventario.data_inicio:
            inventario.data_inicio = datetime.now()
        
        db.commit()
        return jsonify(inventario.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route("/api/inventarios/<int:inv_id>/fechar", methods=["PUT"])
@login_required
def fechar_inventario(inv_id):
    """API: Fecha um inventário"""
    db = Session()
    try:
        inventario = db.query(Inventario).filter_by(id=inv_id).first()
        if not inventario:
            return jsonify({"erro": "Inventário não encontrado"}), 404
        
        if inventario.status == StatusInventario.FECHADO:
            return jsonify({"erro": "Inventário já está fechado"}), 400
        
        inventario.status = StatusInventario.FECHADO
        inventario.data_fim = datetime.now()
        
        db.commit()
        return jsonify(inventario.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route("/api/inventarios/<int:inv_id>", methods=["DELETE"])
@login_required
def deletar_inventario(inv_id):
    """API: Deleta um inventário"""
    db = Session()
    try:
        inventario = db.query(Inventario).filter_by(id=inv_id).first()
        if not inventario:
            return jsonify({"erro": "Inventário não encontrado"}), 404
        
        db.delete(inventario)
        db.commit()
        return jsonify({"mensagem": "Inventário deletado com sucesso"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True, port=8050)