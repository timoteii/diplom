from flask import Flask, request, jsonify, render_template
import psycopg2
import os

# Инициализация Flask
app = Flask(__name__)

# Подключение к базе данных PostgreSQL
DB_HOST = "junction.proxy.rlwy.net"
DB_PORT = "43181"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "FKkFGzRDbzxOfdejvsbAesNwmnxOOnwq"

def get_db_connection():
    """Функция для подключения к базе данных PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def log_request(method, endpoint, request_body, response_status, response_body):
    """Функция для записи логов запросов и ответов в базу данных."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (request_method, endpoint, request_body, response_status, response_body) VALUES (%s, %s, %s, %s, %s)",
            (method, endpoint, request_body, response_status, response_body)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при записи лога: {e}")

# Создание таблицы logs при запуске
def setup_database():
    """Создает таблицы в базе данных, если они не существуют."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Таблица логов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            request_method VARCHAR(10) NOT NULL,
            endpoint VARCHAR(255) NOT NULL,
            request_body TEXT,
            response_status INTEGER NOT NULL,
            response_body TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица карт
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id SERIAL PRIMARY KEY,
            card_id VARCHAR(255) UNIQUE NOT NULL
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# Проверка карты в базе
def check_card_in_db(card_id):
    """Функция проверки, существует ли карта в базе."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cards WHERE card_id = %s", (card_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

# Добавление карты
@app.route('/register_card', methods=['POST'])
def register_card():
    """Регистрация новой карты."""
    try:
        request_data = request.get_json()
        card_id = request_data.get("card_id", "")

        if not card_id:
            response = {"error": "card_id is required"}
            log_request("POST", "/register_card", str(request_data), 400, str(response))
            return jsonify(response), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO cards (card_id) VALUES (%s) ON CONFLICT DO NOTHING", (card_id,))
        conn.commit()
        cur.close()
        conn.close()

        response = {"status": "card_registered"}
        log_request("POST", "/register_card", str(request_data), 201, str(response))
        return jsonify(response), 201
    except Exception as e:
        response = {"error": str(e)}
        log_request("POST", "/register_card", str(request_data), 500, str(response))
        return jsonify(response), 500

# Удаление карты
@app.route('/delete_card', methods=['POST'])
def delete_card():
    """Удаление карты из базы."""
    try:
        request_data = request.get_json()
        card_id = request_data.get("card_id", "")

        if not card_id:
            response = {"error": "card_id is required"}
            log_request("POST", "/delete_card", str(request_data), 400, str(response))
            return jsonify(response), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM cards WHERE card_id = %s", (card_id,))
        conn.commit()
        cur.close()
        conn.close()

        response = {"status": "card_deleted"}
        log_request("POST", "/delete_card", str(request_data), 200, str(response))
        return jsonify(response), 200
    except Exception as e:
        response = {"error": str(e)}
        log_request("POST", "/delete_card", str(request_data), 500, str(response))
        return jsonify(response), 500

# Проверка карты
@app.route('/check_card', methods=['POST'])
def check_card():
    """Обработчик проверки карты."""
    try:
        request_data = request.get_json()
        card_id = request_data.get("card_id", "")

        if check_card_in_db(card_id):
            response = {"status": "access_granted"}
            status_code = 200
        else:
            response = {"status": "access_denied"}
            status_code = 403

        log_request("POST", "/check_card", str(request_data), status_code, str(response))
        return jsonify(response), status_code
    except Exception as e:
        response = {"error": str(e)}
        log_request("POST", "/check_card", str(request_data), 500, str(response))
        return jsonify(response), 500

# Список всех карт
@app.route('/list_cards', methods=['GET'])
def list_cards():
    """Получение списка всех зарегистрированных карт."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT card_id FROM cards")
        cards = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        response = {"cards": cards}
        log_request("GET", "/list_cards", "{}", 200, str(response))
        return jsonify(response), 200
    except Exception as e:
        response = {"error": str(e)}
        log_request("GET", "/list_cards", "{}", 500, str(response))
        return jsonify(response), 500

@app.route('/logs')
def logs():
    """Выводит веб-страницу с логами запросов"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT request_body, response_body, timestamp FROM logs ORDER BY timestamp DESC LIMIT 50")
        logs = cur.fetchall()
        cur.close()
        conn.close()

        return render_template("logs.html", logs=logs)
    except Exception as e:
        return f"Ошибка загрузки логов: {e}"

# Проверка сервера
@app.route('/', methods=['GET'])
def home():
    """Статус сервера."""
    response = {"status": "running"}
    log_request("GET", "/", "{}", 200, str(response))
    return jsonify(response), 200

if __name__ == '__main__':
    setup_database()  # Создание таблиц при запуске
    app.run(host='0.0.0.0', port=5000)
