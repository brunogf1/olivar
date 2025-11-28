import os
import json
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from sqlalchemy import text
from database import Session
from models import Inventario, ItemInventario, StatusInventario
from werkzeug.security import check_password_hash
from datetime import datetime
import requests
from dotenv import load_dotenv
from functools import lru_cache

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-production")

app.config.update(
    SESSION_PERMANENT=False,
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

# ============ CONFIGURAÇÕES DE APIS ============
API_CODIGO_BARRAS_URL = os.getenv("API_CODIGO_BARRAS_URL", "")
API_ESTOQUE_URL = os.getenv("API_ESTOQUE_URL", "")
API_TOKEN = os.getenv("API_TOKEN", "")
API_ESTOQUE_CHAVE = os.getenv("API_ESTOQUE_CHAVE", "")

# ============ FUNÇÕES AUXILIARES DE API (LIVE) ============

@lru_cache(maxsize=128)
def consultar_codigo_api_individual(cod_barra_busca):
    """
    Busca APENAS o código de barras específico na API.
    Retorna exatamente o que vier no campo 'qtde'.
    """
    if not cod_barra_busca:
        return None

    try:
        print(f"🔍 Buscando na API (Live) código: {cod_barra_busca}")
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "Chave": API_ESTOQUE_CHAVE,
            "Skip": 0,
            "Take": 1, 
            "Parameters": [ 
                {
                    "Column": "cod_barra_ord", 
                    "Value": cod_barra_busca
                }
            ],
            "Sorting": [
                {
                    "ByColumn": "cod_item",
                    "Sort": "ASC"
                }
            ]
        }
        
        response = requests.post(
            API_CODIGO_BARRAS_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Erro API: {response.status_code} - {response.text}")
            return None
            
        dados_api = response.json()
        
        lista_itens = []
        if isinstance(dados_api, list):
            lista_itens = dados_api
        elif isinstance(dados_api, dict):
            if 'value' in dados_api: lista_itens = dados_api['value']
            elif 'data' in dados_api: lista_itens = dados_api['data']
            elif 'cod_item' in dados_api: lista_itens = [dados_api]
        
        if not lista_itens:
            return None
            
        item = lista_itens[0]
        
        # Mapeamento ESTRITO do campo qtde
        return {
            'cod_emp': item.get('cod_emp'),
            'etiq_id': item.get('etiq_id'),
            'cod_barra_ord': item.get('cod_barra_ord'),
            'cod_item': item.get('cod_item'),
            'desc_tecnica': item.get('desc_tecnica'),
            'mascara': item.get('mascara'),
            'tmasc_item_id': item.get('tmasc_item_id'),
            'qtde': item.get('qtde') # Pode ser None
        }

    except Exception as e:
        print(f"❌ Erro na requisição API: {e}")
        return None

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
    return render_template("inventarios.html", user=session.get("user"))

@app.route("/api/inventarios", methods=["GET"])
@login_required
def get_inventarios():
    db = Session()
    try:
        inventarios_list = db.query(Inventario).order_by(Inventario.criado_em.desc()).all()
        return jsonify([inv.to_dict() for inv in inventarios_list])
    finally:
        db.close()

@app.route("/api/inventarios", methods=["POST"])
@login_required
def criar_inventario():
    data = request.get_json()
    nome = data.get("nome", "").strip()
    
    if not nome:
        return jsonify({"erro": "Nome do inventário é obrigatório"}), 400
    
    db = Session()
    try:
        novo_inv = Inventario(
            nome=nome,
            status=StatusInventario.ABERTO,
            data_inicio=datetime.now(),
            data_fim=None,
            criado_em=datetime.now()
        )
        db.add(novo_inv)
        db.commit()
        db.refresh(novo_inv)
        return jsonify(novo_inv.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route("/api/inventarios/<int:inv_id>/fechar", methods=["PUT"])
@login_required
def fechar_inventario(inv_id):
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
        db.refresh(inventario)
        return jsonify(inventario.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route("/api/inventarios/<int:inv_id>", methods=["DELETE"])
@login_required
def deletar_inventario(inv_id):
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

@app.route("/inventarios/<int:inv_id>/leitura", methods=["GET"])
@login_required
def leitura_codigos(inv_id):
    db = Session()
    try:
        inventario = db.query(Inventario).filter_by(id=inv_id).first()
        if not inventario:
            return redirect(url_for("inventarios"))
        
        if inventario.status != StatusInventario.ABERTO:
            flash("Este inventário não está aberto para leitura!", "danger")
            return redirect(url_for("inventarios"))
        
        return render_template("leitura.html", inventario=inventario, user=session.get("user"))
    finally:
        db.close()

# ============ ROTAS DE VALIDAÇÃO ============
@app.route("/api/validar-codigo-barras", methods=["GET"])
@login_required
def validar_codigo_barras():
    codigo = request.args.get('codigo', '').strip()
    
    if not codigo:
        return jsonify({"erro": "Código não informado"}), 400
    
    try:
        item = consultar_codigo_api_individual(codigo)
        
        if not item:
            return jsonify({
                "sucesso": False,
                "erro": f"Código de barras '{codigo}' não encontrado na API"
            }), 404

        if item.get('qtde') is None:
             return jsonify({
                "sucesso": False,
                "erro": f"Item encontrado, mas sem campo 'qtde' definido na API."
            }), 422
        
        return jsonify({
            "sucesso": True,
            "dados": item
        }), 200
        
    except Exception as e:
        return jsonify({
            "erro": "Erro ao validar código",
            "detalhes": str(e)
        }), 500

# ============ ROTAS DE ITENS INVENTÁRIO ============
@app.route("/api/inventarios/<int:inv_id>/itens", methods=["GET"])
@login_required
def get_itens_inventario(inv_id):
    db = Session()
    try:
        inventario = db.query(Inventario).filter_by(id=inv_id).first()
        if not inventario:
            return jsonify({"erro": "Inventário não encontrado"}), 404
        
        itens = db.query(ItemInventario).filter_by(inventario_id=inv_id).order_by(
            ItemInventario.timestamp.desc()
        ).all()
        
        return jsonify([item.to_dict() for item in itens]), 200
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route("/api/inventarios/<int:inv_id>/itens", methods=["POST"])
@login_required
def adicionar_item_inventario(inv_id):
    """
    Adiciona um item.
    1. OBRIGATÓRIO TER 'qtde' NA API.
    2. PROIBIDO DUPLICIDADE (Retorna erro se já existir).
    """
    data = request.get_json()
    
    db = Session()
    try:
        inventario = db.query(Inventario).filter_by(id=inv_id).first()
        if not inventario:
            return jsonify({"erro": "Inventário não encontrado"}), 404
        
        if inventario.status != StatusInventario.ABERTO:
            return jsonify({"erro": "Inventário não está aberto"}), 400
        
        cod_barra = data.get('cod_barra_ord', '').strip()
        
        if not cod_barra:
            return jsonify({"erro": "Código de barras não informado"}), 400
        
        # 1. Busca na API
        item_api = consultar_codigo_api_individual(cod_barra)
        
        if not item_api:
            # Tenta limpar cache e buscar de novo
            consultar_codigo_api_individual.cache_clear()
            item_api = consultar_codigo_api_individual(cod_barra)
            
            if not item_api:
                return jsonify({"erro": "Código de barras não encontrado na API"}), 404

        # 2. VALIDAÇÃO ESTRITA DE 'qtde'
        raw_qtde = item_api.get('qtde')
        
        if raw_qtde is None:
             return jsonify({
                 "erro": "Campo 'qtde' não encontrado na API. Gravação bloqueada."
             }), 422 
        
        try:
            quantidade_real = float(raw_qtde)
            if quantidade_real <= 0:
                return jsonify({
                    "erro": f"Quantidade inválida ({quantidade_real}). Item não será gravado."
                }), 422
        except (ValueError, TypeError):
             return jsonify({
                 "erro": f"Valor de 'qtde' inválido na API: {raw_qtde}"
             }), 422

        # 3. VERIFICAÇÃO DE DUPLICIDADE (BLOQUEIO TOTAL)
        item_existente = db.query(ItemInventario).filter_by(
            inventario_id=inv_id,
            cod_barra_ord=cod_barra
        ).first()
        
        if item_existente:
            # BLOQUEIA: Item já lido. Não grava, não incrementa.
            return jsonify({
                "erro": f"ERRO: A etiqueta '{cod_barra}' JÁ FOI LIDA neste inventário."
            }), 409 # Status 409 Conflict indica conflito de dados (duplicidade)

        # 4. Se não existe, cria novo (único caminho possível)
        novo_item = ItemInventario(
            inventario_id=inv_id,
            cod_barra_ord=item_api['cod_barra_ord'],
            cod_item=item_api['cod_item'],
            etiq_id=item_api['etiq_id'],
            desc_tecnica=item_api['desc_tecnica'],
            mascara=item_api['mascara'],
            tmasc_item_id=item_api['tmasc_item_id'],
            quantidade=quantidade_real,
            timestamp=datetime.now()
        )
        db.add(novo_item)
        db.commit()
        db.refresh(novo_item)
        return jsonify({
            "sucesso": True,
            "mensagem": "Item adicionado",
            "dados": novo_item.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

# ============ ROTAS DE ADMIN/STATUS ============
@app.route("/api/admin/status", methods=["GET"])
@login_required
def api_admin_status():
    db = Session()
    try:
        total_inventarios = db.query(Inventario).count()
        total_itens_lidos = db.query(ItemInventario).count()
        
        info_cache = consultar_codigo_api_individual.cache_info()
        
        return jsonify({
            "inventarios_criados": total_inventarios,
            "itens_lidos_total": total_itens_lidos,
            "modo": "LIVE API (Strict 'qtde' + No Duplicates)",
            "cache_status": {
                "hits": info_cache.hits,
                "misses": info_cache.misses,
                "capacidade_max": info_cache.maxsize
            },
            "status": "✅ Sistema operacional"
        }), 200
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True, port=8050)