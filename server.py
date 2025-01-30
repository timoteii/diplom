from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Подключение к базе данных PostgreSQL
DB_HOST = "junction.proxy.rlwy.net"
DB_PORT = "43181"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "FKkFGzRDbzxOfdejvsbAesNwmnxOOnwq"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def check_card_in_db(card_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cards WHERE card_id = %s", (card_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def add_card_to_db(card_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO cards (card_id) VALUES (%s)", (card_id,))
        conn.commit()
        success = True
    except psycopg2.IntegrityError:
        success = False
    finally:
        cur.close()
        conn.close()
    return success

@app.route('/')
def home():
    return "Server is running!"

@app.route('/check_card', methods=['GET', 'POST'])
def check_card():
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200  # Подтверждение работы маршрута
    
    data = request.get_json(force=True, silent=True)
    if not data or 'card_id' not in data:
        return jsonify({"error": "Invalid or missing card_id"}), 400
    
    card_id = data['card_id']
    
    if check_card_in_db(card_id):
        response = {"status": "access_granted"}
    else:
        response = {"status": "access_denied"}
    
    return jsonify(response)

@app.route('/register_card', methods=['POST'])
def register_card():
    data = request.get_json()
    if not data or 'card_id' not in data:
        return jsonify({"error": "Invalid or missing card_id"}), 400
    
    card_id = data['card_id']
    
    if add_card_to_db(card_id):
        response = {"status": "registration_success"}
    else:
        response = {"status": "card_already_exists"}
    
    return jsonify(response)

@app.route('/routes')
def list_routes():
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    return jsonify(routes)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
