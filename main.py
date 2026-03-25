from flask import Flask, request, jsonify
import os
import uuid
from datetime import datetime, timezone
import requests
from flask_pymongo import PyMongo

app = Flask(__name__)

mongo_host = os.environ.get("MONGO_URL")
app.config["MONGO_URI"] = f"mongodb://{mongo_host}:27017/transacao_db"

mongo = PyMongo(app)

def validate_uuid(u):
    try:
        uuid.UUID(str(u))
        return True
    except Exception:
        return False

def validate_client_id(client_id):
    url = f"http://18.228.48.67/users/{client_id}"
    try:
        response = requests.get(url, timeout=5)
        print("validate_client_id:", response.status_code, response.text)
        return response.status_code == 200
    except requests.RequestException as e:
        print("Error validating client_id:", e)
        return False
    
@app.route('/transacao', methods=['GET'])
def get_transacao():
    transacoes_cursor = mongo.db.transacoes.find().sort("created_at", -1)
    result = []
    for transacao in transacoes_cursor:
        t_out = {
            "_id": str(transacao["_id"]),
            "client_id": transacao["client_id"],
            "action_code": transacao["action_code"],
            "action_quantity": transacao["action_quantity"],
            "preco_unitario": transacao["preco_unitario"],
            "total_price": transacao["total_price"],
        }
        result.append(t_out)
    return jsonify(result), 200

@app.route('/transacao/<transacao_id>', methods=['GET'])
def get_transacao_by_id(transacao_id):
    if not validate_uuid(transacao_id):
        return jsonify({"error": "Invalid transacao ID"}), 400

    transacao = mongo.db.transacoes.find_one({"_id": uuid.UUID(transacao_id)})
    if not transacao:
        return jsonify({"error": "Transacao not found"}), 404

    t_out = {
        "_id": str(transacao["_id"]),
        "client_id": transacao["client_id"],
        "action_code": transacao["action_code"],
        "action_quantity": transacao["action_quantity"],
        "preco_unitario": transacao["preco_unitario"],
        "total_price": transacao["total_price"],
    }
    return jsonify(t_out), 200

@app.route('/transacao', methods=['POST'])
def create_transacao():    

    data = request.get_json() or {}
    client_id = data.get('client_id')
    action_code = data.get('action_code')
    action_quantity = data.get('action_quantity')
    unitary_price = data.get('preco_unitario')

    if client_id is None:
        return jsonify({"error": "client_id is required"}), 400

    if not validate_uuid(client_id):
        return jsonify({"error": "Invalid client_id format"}), 400

    if not validate_client_id(client_id):
        return jsonify({"error": "Invalid client ID"}), 404

    if action_code is None or action_quantity is None or unitary_price is None:
        return jsonify({"error": "action_code, action_quantity and preco_unitario are required"}), 400

    if not isinstance(action_quantity, (int, float)) or not isinstance(unitary_price, (int, float)):
        return jsonify({"error": "action_quantity and preco_unitario must be numeric"}), 400

    total_price = action_quantity * unitary_price
    date = datetime.now(timezone.utc)

    transacao = {
        "_id": str(uuid.uuid4()),
        "client_id": client_id,
        "action_code": action_code,
        "action_quantity": action_quantity,
        "preco_unitario": unitary_price,
        "total_price": total_price,
        "date": date.isoformat(),
    }

    mongo.db.transacoes.insert_one(transacao)
    return jsonify(transacao), 201

@app.route('/transacao/<transacao_id>', methods=['DELETE'])
def delete_transacao(transacao_id):
    if not validate_uuid(transacao_id):
        return jsonify({"error": "Invalid transacao ID"}), 400

    result = mongo.db.transacoes.delete_one({"_id": uuid.UUID(transacao_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Transacao not found"}), 404

    return jsonify({"message": "Transacao deleted successfully"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)