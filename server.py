from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def check_card_in_db(card_id):
    conn = sqlite3.connect('rfid.db')
    c = conn.cursor()
    c.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_card_to_db(card_id):
    conn = sqlite3.connect('rfid.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO cards (card_id) VALUES (?)", (card_id,))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

@app.route('/')
def home():
    return "Server is running!"


@app.route('/check_card', methods=['GET','POST'])
def check_card():
    data = request.get_json()
    card_id = data.get('card_id')
    
    if check_card_in_db(card_id):
        response = {"status": "access_granted"}
    else:
        response = {"status": "access_denied"}
    
    return jsonify(response)

@app.route('/register_card', methods=['POST'])
def register_card():
    data = request.get_json()
    card_id = data.get('card_id')
    
    if add_card_to_db(card_id):
        response = {"status": "registration_success"}
    else:
        response = {"status": "card_already_exists"}
    
    return jsonify(response)

@app.route('/routes')
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(str(rule))
    return jsonify(routes)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
