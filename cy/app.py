from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import random
import string

app = Flask(__name__)
CORS(app) # Permite peticiones desde el navegador (HTML)

# CONFIGURACIÓN DE TU BASE DE DATOS MYSQL
# (Ajusta 'user' y 'password' según tu instalación local de MySQL)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Pon tu contraseña de MySQL aquí si tienes una
    'database': 'cyberpunk_rpg'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# -------------------------------------------------------------------
# RUTAS DE LA API (ENDPOINTS)
# -------------------------------------------------------------------

# 1. Obtener personajes de un usuario específico
@app.route('/api/personajes/<int:usuario_id>', methods=['GET'])
def obtener_personajes(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, alias, clase, hp_actual, hp_max FROM personajes WHERE usuario_id = %s", (usuario_id,))
        personajes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "personajes": personajes}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 2. Crear una nueva Sala de Game Master (Código de 4 caracteres)
@app.route('/api/salas/crear', methods=['POST'])
def crear_sala():
    data = request.json or {}
    gm_id = data.get('gm_id', 1) # Por defecto usuario 1 para pruebas

    # Generar código de 4 caracteres alfanuméricos únicos
    caracteres = string.ascii_uppercase + string.digits
    codigo = ''.join(random.choices(caracteres, k=4))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO salas (codigo, gm_id) VALUES (%s, %s)", (codigo, gm_id))
        conn.commit()
        sala_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "codigo": codigo, "sala_id": sala_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 3. Unirse a una sala existente como Jugador
@app.route('/api/salas/unirse', methods=['POST'])
def unirse_sala():
    data = request.json or {}
    codigo = data.get('codigo', '').upper()
    usuario_id = data.get('usuario_id')
    personaje_id = data.get('personaje_id')

    if not codigo or not personaje_id:
        return jsonify({"status": "error", "message": "Código y personaje son requeridos"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Buscar la sala por su código de 4 letras/números
        cursor.execute("SELECT id FROM salas WHERE codigo = %s AND estado = 'ACTIVA'", (codigo,))
        sala = cursor.fetchone()

        if not sala:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "La sala no existe o está cerrada"}), 4404

        # Registrar al jugador en la sala
        cursor.execute("""
            INSERT INTO jugadores_sala (sala_id, usuario_id, personaje_id) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE personaje_id = VALUES(personaje_id)
        """, (sala['id'], usuario_id, personaje_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Conectado a la sala", "sala_id": sala['id']}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("Servidor Cyberpunk RPG corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)