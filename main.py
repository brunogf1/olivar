import os
import json
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from sqlalchemy import text
from database import Session
# IMPORTANTE: Apenas as tabelas que existem
from models import Inventario, ItemInventario, StatusInventario
from werkzeug.security import check_password_hash
from datetime import datetime
import requests
from dotenv import load_dotenv
from functools import lru_cache

# Garante carregamento do .env e define pasta base
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
load_dotenv(env_path)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-production")

app.config.update(
    SESSION_PERMANENT=False,
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

# ============ LOG DE INICIALIZAÇÃO ============
print("="*60)
print("🚀 INICIANDO OLIVAR (CORREÇÃO INDEX)")
print(f"📂 Diretório: {basedir}")
print(f"🔗 API BARRAS: {os.getenv('API_CODIGO_BARRAS_URL')}")
print("="*60)

# ============ CONFIGURAÇÕES DE APIS ============
API_CODIGO_BARRAS_URL = os.getenv("API_CODIGO_BARRAS_URL", "")
API_ESTOQUE_URL = os.getenv("API_ESTOQUE_URL", "")
API_TOKEN = os.getenv("API_TOKEN", "")
API_ESTOQUE_CHAVE = os.getenv("API_ESTOQUE_CHAVE", "")

# ============ FUNÇÕES AUXILIARES ============

@lru_cache(maxsize=128)
def consultar_codigo_api_individual(cod_barra_busca):
    if not cod_barra_busca: return None

    try:
        print(f"🔍 [API] Buscando código: '{cod_barra_busca}'")
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "Chave": API_ESTOQUE_CHAVE, "Skip": 0, "Take": 1,
            "Parameters": [{ "Column": "cod_barra_ord", "Value": cod_barra_busca }],
            "Sorting": [{ "ByColumn": "cod_item", "Sort": "ASC" }]
        }
        
        response = requests.post(
            API_CODIGO_BARRAS_URL, headers=headers, json=payload, timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ [API] Erro HTTP {response.status_code}: {response.text}")
            return None
            
        dados_api = response.json()
        lista_itens = []
        if isinstance(dados_api, list): lista_itens = dados_api
        elif isinstance(dados_api, dict):
            if 'value' in dados_api: lista_itens = dados_api['value']
            elif 'data' in dados_api: lista_itens = dados_api['data']
            elif 'cod_item' in dados_api: lista_itens = [dados_api]
        
        if not lista_itens:
            print(f"⚠️ [API] Lista vazia para código '{cod_barra_busca}'")
            return None
            
        item = lista_itens[0]
        # Limpeza e conversão segura
        c_item = str(item.get('cod_item', '')).strip()
        t_id = item.get('tmasc_item_id')
        t_id = int(t_id) if t_id is not None else 0
        
        return {
            'cod_emp': item.get('cod_emp'),
            'etiq_id': item.get('etiq_id'),
            'cod_barra_ord': item.get('cod_barra_ord'),
            'cod_item': c_item,
            'desc_tecnica': item.get('desc_tecnica'),
            'mascara': item.get('mascara'),
            'tmasc_item_id': t_id,
            'qtde': item.get('qtde')
        }

    except Exception as e:
        print(f"❌ [API] Exceção: {e}")
        return None

# ============ AUTH ============
def verify_password(stored_hash, provided_password):
    try:
        if stored_hash and check_password_hash(stored_hash, provided_password): return True
    except: pass
    return (stored_hash or "") == (provided_password or "")

def login_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user"): return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped

# ============ ROTAS ============

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        db = Session()
        try:
            sql = text("SELECT * FROM users WHERE login = :u LIMIT 1")
            row = db.execute(sql, {"u": username}).mappings().first()
        finally: db.close()

        if not row or not verify_password(str(row.get('password') or ""), password):
            flash("Credenciais inválidas.", "danger")
            return redirect(url_for("login"))

        session["user"] = {"id": row.get('id'), "username": row.get('login')}
        return redirect(session.pop("after_login_next", url_for("index")))
    return render_template("login.html")

@app.get("/post-login")
@login_required
def post_login():
    next_url = session.pop("after_login_next", url_for("index"))
    return render_template("post_login.html", next_url=next_url)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# === CORREÇÃO DA ROTA INDEX ===
@app.route("/")
@login_required
def index():
    # Tenta carregar o result.json se existir, senão manda vazio
    # Isso evita o Erro 500 se o index.html esperar variáveis
    data = []
    columns = []
    try:
        json_file = os.path.join(basedir, "result.json")
        if os.path.exists(json_file):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data and isinstance(data, list):
                columns = list(data[0].keys())
    except Exception as e:
        print(f"⚠️ Erro ao ler result.json: {e}")
        data = []

    return render_template("index.html", data=data, columns=columns, user=session.get("user"))

@app.route("/inventarios", methods=["GET"])
@login_required
def inventarios():
    return render_template("inventarios.html", user=session.get("user"))

@app.route("/api/inventarios", methods=["GET"])
@login_required
def get_inventarios():
    db = Session()
    try:
        data = db.query(Inventario).order_by(Inventario.criado_em.desc()).all()
        return jsonify([i.to_dict() for i in data])
    finally: db.close()

@app.route("/api/inventarios", methods=["POST"])
@login_required
def criar_inventario():
    data = request.get_json()
    nome = data.get("nome", "").strip()
    if not nome: return jsonify({"erro": "Nome obrigatório"}), 400
    db = Session()
    try:
        inv = Inventario(nome=nome, status=StatusInventario.ABERTO, criado_em=datetime.now())
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return jsonify(inv.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally: db.close()

@app.route("/api/inventarios/<int:inv_id>/fechar", methods=["PUT"])
@login_required
def fechar_inventario(inv_id):
    db = Session()
    try:
        inv = db.query(Inventario).filter_by(id=inv_id).first()
        if not inv: return jsonify({"erro": "Não encontrado"}), 404
        inv.status = StatusInventario.FECHADO
        inv.data_fim = datetime.now()
        db.commit()
        return jsonify(inv.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally: db.close()

@app.route("/api/inventarios/<int:inv_id>", methods=["DELETE"])
@login_required
def deletar_inventario(inv_id):
    db = Session()
    try:
        inv = db.query(Inventario).filter_by(id=inv_id).first()
        if not inv: return jsonify({"erro": "Não encontrado"}), 404
        
        # Apaga itens antes para não dar erro de FK
        db.query(ItemInventario).filter_by(inventario_id=inv_id).delete()
        
        db.delete(inv)
        db.commit()
        return jsonify({"mensagem": "Deletado"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally: db.close()

@app.route("/inventarios/<int:inv_id>/leitura", methods=["GET"])
@login_required
def leitura_codigos(inv_id):
    db = Session()
    try:
        inv = db.query(Inventario).filter_by(id=inv_id).first()
        if not inv: return redirect(url_for("inventarios"))
        return render_template("leitura.html", inventario=inv, user=session.get("user"))
    finally: db.close()

@app.route("/inventarios/<int:inv_id>/lista", methods=["GET"])
@login_required
def lista_itens_page(inv_id):
    db = Session()
    try:
        inv = db.query(Inventario).filter_by(id=inv_id).first()
        if not inv: return redirect(url_for("inventarios"))
        return render_template("itens_lidos.html", inventario=inv, user=session.get("user"))
    finally: db.close()

@app.route("/api/inventarios/<int:inv_id>/itens", methods=["GET"])
@login_required
def get_itens_inventario(inv_id):
    db = Session()
    try:
        itens = db.query(ItemInventario).filter_by(inventario_id=inv_id).order_by(ItemInventario.timestamp.desc()).all()
        return jsonify([i.to_dict() for i in itens]), 200
    finally: db.close()

@app.route("/api/inventarios/<int:inv_id>/itens", methods=["POST"])
@login_required
def adicionar_item_inventario(inv_id):
    data = request.get_json()
    db = Session()
    try:
        inv = db.query(Inventario).filter_by(id=inv_id).first()
        if not inv or inv.status != StatusInventario.ABERTO:
            return jsonify({"erro": "Inventário inválido ou fechado"}), 400
        
        cod = data.get('cod_barra_ord', '').strip()
        if not cod: return jsonify({"erro": "Código vazio"}), 400

        item_api = consultar_codigo_api_individual(cod)
        if not item_api:
            consultar_codigo_api_individual.cache_clear()
            item_api = consultar_codigo_api_individual(cod)
            if not item_api:
                return jsonify({"erro": "Código não encontrado na API"}), 404

        raw_qtde = item_api.get('qtde')
        if raw_qtde is None: return jsonify({"erro": "Sem quantidade na API"}), 422
        try:
            qtd_real = float(raw_qtde)
            if qtd_real <= 0: return jsonify({"erro": "Quantidade inválida"}), 422
        except: return jsonify({"erro": "Erro valor quantidade"}), 422

        exists = db.query(ItemInventario).filter_by(inventario_id=inv_id, cod_barra_ord=cod).first()
        if exists: 
            return jsonify({"erro": "Código já lido"}), 409

        novo = ItemInventario(
            inventario_id=inv_id,
            cod_barra_ord=item_api['cod_barra_ord'],
            cod_item=item_api['cod_item'],
            etiq_id=item_api['etiq_id'],
            desc_tecnica=item_api['desc_tecnica'],
            mascara=item_api['mascara'],
            tmasc_item_id=item_api['tmasc_item_id'],
            quantidade=qtd_real,
            timestamp=datetime.now()
        )
        db.add(novo)
        db.commit()
        return jsonify({"sucesso": True, "dados": novo.to_dict(), "mensagem": "Adicionado"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally: db.close()

@app.route("/api/validar-codigo-barras", methods=["GET"])
@login_required
def validar_codigo_barras():
    codigo = request.args.get('codigo', '').strip()
    if not codigo: return jsonify({"erro": "Código não informado"}), 400
    try:
        item = consultar_codigo_api_individual(codigo)
        if not item: return jsonify({"sucesso": False, "erro": "Código não encontrado"}), 404
        if item.get('qtde') is None: return jsonify({"sucesso": False, "erro": "Sem quantidade"}), 422
        return jsonify({"sucesso": True, "dados": item}), 200
    except Exception as e:
        return jsonify({"erro": "Erro interno", "detalhes": str(e)}), 500

@app.route("/api/admin/status", methods=["GET"])
@login_required
def api_admin_status():
    db = Session()
    try:
        invs = db.query(Inventario).count()
        itens = db.query(ItemInventario).count()
        info = consultar_codigo_api_individual.cache_info()
        return jsonify({
            "inventarios": invs,
            "itens_lidos": itens,
            "cache": {"hits": info.hits, "misses": info.misses},
            "status": "OK"
        }), 200
    finally: db.close()

if __name__ == "__main__":
    app.run(debug=True, port=8050)
