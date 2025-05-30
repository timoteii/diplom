from flask import Flask, request, jsonify, render_template
import psycopg2

app = Flask(__name__)

# Подключение к базе данных PostgreSQL
DB_HOST = "junction.proxy.rlwy.net"
DB_PORT = "43181"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "FKkFGzRDbzxOfdejvsbAesNwmnxOOnwq"

def get_db_connection():
    """Подключение к базе данных."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def log_request(method, endpoint, request_body, response_status, response_body):
    """Запись логов запросов и ответов в базу данных."""
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

# Инициализация базы данных
def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id SERIAL PRIMARY KEY,
            card_id VARCHAR(255) UNIQUE NOT NULL
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# Обработчик проверки карт
@app.route('/check_card', methods=['POST'])
def check_card():
    """Проверка карты в базе данных."""
    try:
        request_data = request.get_json()
        card_id = request_data.get("card_id", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM cards WHERE card_id = %s", (card_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            card_id_with_id = f"{card_id} (ID: {result[0]})"
            response = {"status": "access_granted", "card": card_id_with_id}
            status_code = 200
        else:
            response = {"status": "access_denied", "card": card_id}
            status_code = 403

        log_request("POST", "/check_card", str(request_data), status_code, str(response))
        return jsonify(response), status_code
    except Exception as e:
        response = {"error": str(e)}
        log_request("POST", "/check_card", str(request_data), 500, str(response))
        return jsonify(response), 500

# Регистрация новой карты
@app.route('/register_card', methods=['POST'])
def register_card():
    """Добавление карты в базу данных."""
    try:
        request_data = request.get_json()
        card_id = request_data.get("card_id", "")

        conn = get_db_connection()
        cur = conn.cursor()

        # Проверяем, есть ли уже такая карта
        cur.execute("SELECT COUNT(*) FROM cards WHERE card_id = %s", (card_id,))
        card_exists = cur.fetchone()[0] > 0

        if card_exists:
            response = {"status": "card_already_registered"}
            status_code = 409  # Код 409: Conflict
        else:
            cur.execute("INSERT INTO cards (card_id) VALUES (%s)", (card_id,))
            conn.commit()
            response = {"status": "card_registered"}
            status_code = 201

        cur.close()
        conn.close()

        log_request("POST", "/register_card", str(request_data), status_code, str(response))
        return jsonify(response), status_code
    except Exception as e:
        response = {"error": str(e)}
        log_request("POST", "/register_card", str(request_data), 500, str(response))
        return jsonify(response), 500

# Удаление карты
@app.route('/remove_card', methods=['POST'])
def remove_card():
    """Удаление карты из базы."""
    try:
        request_data = request.get_json()
        card_id = request_data.get("card_id", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM cards WHERE card_id = %s", (card_id,))
        conn.commit()
        cur.close()
        conn.close()

        response = {"status": "card_deleted"}
        log_request("POST", "/remove_card", str(request_data), 200, str(response))
        return jsonify(response), 200
    except Exception as e:
        response = {"error": str(e)}
        log_request("POST", "/remove_card", str(request_data), 500, str(response))
        return jsonify(response), 500

# Получение логов
@app.route('/get_logs', methods=['GET'])
def get_logs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT request_body, response_body, timestamp FROM logs ORDER BY timestamp DESC LIMIT 50")
        logs = cur.fetchall()
        cur.close()
        conn.close()

        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "request_body": log[0],
                "response_body": log[1],
                "timestamp": log[2].isoformat()  # Преобразуем в ISO формат для удобства работы
            })

        return jsonify({"logs": formatted_logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_cards', methods=['GET'])
def get_cards():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, card_id FROM cards")
        cards = [{"id": row[0], "card_id": row[1]} for row in cur.fetchall()]
        cur.close()
        conn.close()

        return jsonify({"cards": cards})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Очистка логов
@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    """Удаление всех логов."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM logs")
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "logs_cleared"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Интерфейс логов
@app.route('/logs')
def logs():
    """Выводит страницу с логами."""
    return render_template("logs.html")

# Главная страница
@app.route('/')
def home():
    return jsonify({"status": "running"}), 200

if __name__ == '__main__':
    setup_database()
    app.run(host='0.0.0.0', port=5000)


# FKkFGzRDbzxOfdejvsbAesNwmnxOOnwq