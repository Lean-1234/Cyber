from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import random
import string
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.')
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Cybermaniaco456',  # Tu contraseña de MySQL
    'database': 'cyberpunk_rpg',
    'port': 3306
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def inicio():
    return send_from_directory('.', 'login.html')

@app.route('/<path:filename>')
def servir_archivos(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "Archivo no encontrado (404)", 404

@app.route('/api/auth/registro', methods=['POST'])
def registrar_usuario():
    try:
        data = request.json or {}
        username = str(data.get('username', '')).strip()
        email = str(data.get('email', '')).strip().lower()
        password = str(data.get('password', ''))

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "Todos los campos son obligatorios."}), 400

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM usuarios WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "El usuario o email ya está registrado."}), 400

        cursor.execute("INSERT INTO usuarios (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password_hash))
        conn.commit()
        nuevo_id = cursor.lastrowid

        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Registrado exitosamente.", "usuario": {"id": nuevo_id, "username": username, "email": email}}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_usuario():
    try:
        data = request.json or {}
        username_or_email = str(data.get('username_or_email', '')).strip()
        password = str(data.get('password', ''))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, password_hash FROM usuarios WHERE username = %s OR email = %s", (username_or_email, username_or_email))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if not usuario or not check_password_hash(usuario['password_hash'], password):
            return jsonify({"status": "error", "message": "Credenciales inválidas."}), 401

        return jsonify({"status": "success", "usuario": {"id": usuario['id'], "username": usuario['username'], "email": usuario['email']}}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/personajes/<int:usuario_id>', methods=['GET'])
def obtener_personajes(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, alias, clase, origen, hp_actual, hp_max FROM personajes WHERE usuario_id = %s", (usuario_id,))
        personajes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "personajes": personajes}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/personajes/crear', methods=['POST'])
def crear_personaje_manual():
    try:
        data = request.json or {}
        usuario_id = data.get('usuario_id')
        alias = str(data.get('alias', '')).strip()
        clase = str(data.get('clase', 'Netrunner')).strip()
        origen = str(data.get('origen', 'Neo-Tokyo')).strip()

        if not usuario_id or not alias:
            return jsonify({"status": "error", "message": "Faltan datos obligatorios."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO personajes (
                usuario_id, alias, clase, origen, inteligencia, reflejos, destreza, tecnica, cool, atractivo, suerte, movimiento, cuerpo, empatia, hp_max, hp_actual
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            usuario_id, alias, clase, origen,
            data.get('inteligencia', 11), data.get('reflejos', 10), data.get('destreza', 10),
            data.get('tecnica', 10), data.get('cool', 10), data.get('atractivo', 10),
            data.get('suerte', 10), data.get('movimiento', 9), data.get('cuerpo', 15),
            data.get('empatia', 10), data.get('hp_max', 35), data.get('hp_actual', 35)
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Personaje creado."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/salas/crear', methods=['POST'])
def crear_sala():
    try:
        data = request.json or {}
        gm_id = data.get('gm_id', 1)
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO salas (codigo, gm_id, estado) VALUES (%s, %s, 'ACTIVA')", (codigo, gm_id))
        conn.commit()
        sala_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "codigo": codigo, "sala_id": sala_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Diccionario auxiliar en memoria para guardar las alertas activas de sala (como el aviso de 5 min)
alertas_salas = {}

@app.route('/api/salas/alerta', methods=['POST'])
def enviar_alerta_sala():
    try:
        data = request.json or {}
        sala_id = data.get('sala_id')
        mensaje = data.get('mensaje')
        alertas_salas[int(sala_id)] = mensaje
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/salas/estado/<int:sala_id>', methods=['GET'])
def obtener_estado_sala(sala_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT estado FROM salas WHERE id = %s", (sala_id,))
        sala = cursor.fetchone()
        cursor.close()
        conn.close()

        if not sala or sala['estado'] != 'ACTIVA':
            return jsonify({"status": "closed", "estado": "CERRADA"}), 200

        alerta = alertas_salas.get(sala_id, None)
        return jsonify({"status": "success", "estado": "ACTIVA", "alerta_activa": alerta}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/salas/unirse', methods=['POST'])
def unirse_sala():
    try:
        data = request.json or {}
        codigo = str(data.get('codigo', '')).strip().upper()
        usuario_id = data.get('usuario_id')
        personaje_id = data.get('personaje_id')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, estado FROM salas WHERE codigo = %s AND estado = 'ACTIVA' ORDER BY id DESC LIMIT 1", (codigo,))
        sala = cursor.fetchone()

        if not sala:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "La sala no existe o se encuentra cerrada."}), 404

        cursor.execute("""
            INSERT INTO jugadores_sala (sala_id, usuario_id, personaje_id) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE personaje_id = VALUES(personaje_id)
        """, (sala['id'], usuario_id, personaje_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "sala_id": sala['id']}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/salas/desconectar', methods=['POST'])
def desconectar_sala():
    try:
        data = request.json or {}
        usuario_id = data.get('usuario_id')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jugadores_sala WHERE usuario_id = %s", (usuario_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/salas/cerrar', methods=['POST'])
def cerrar_sala():
    try:
        data = request.json or {}
        sala_id = data.get('sala_id')

        if not sala_id:
            return jsonify({"status": "error", "message": "Falta el ID de la sala."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE salas SET estado = 'CERRADA' WHERE id = %s", (sala_id,))
        cursor.execute("DELETE FROM jugadores_sala WHERE sala_id = %s", (sala_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        if sala_id in alertas_salas:
            del alertas_salas[sala_id]

        return jsonify({"status": "success", "message": "Sala cerrada correctamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/personajes/actualizar-hp', methods=['POST'])
def actualizar_hp():
    try:
        data = request.json or {}
        personaje_id = data.get('personaje_id')
        cambio = int(data.get('cambio', 0))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT hp_actual, hp_max FROM personajes WHERE id = %s", (personaje_id,))
        p = cursor.fetchone()
        
        if not p:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Personaje no encontrado."}), 404

        nuevo_hp = max(0, min(p['hp_max'], p['hp_actual'] + cambio))
        cursor.execute("UPDATE personajes SET hp_actual = %s WHERE id = %s", (nuevo_hp, personaje_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "hp_actual": nuevo_hp}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/salas/<int:sala_id>/jugadores', methods=['GET'])
def obtener_jugadores_sala(sala_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT estado FROM salas WHERE id = %s", (sala_id,))
        sala = cursor.fetchone()
        
        if not sala or sala['estado'] != 'ACTIVA':
            cursor.close()
            conn.close()
            return jsonify({"status": "closed", "message": "La sala fue cerrada por el Game Master."}), 200

        cursor.execute("""
            SELECT p.id, p.alias, p.clase, p.hp_actual, p.hp_max, u.username 
            FROM jugadores_sala js
            JOIN personajes p ON js.personaje_id = p.id
            JOIN usuarios u ON js.usuario_id = u.id
            WHERE js.sala_id = %s
        """, (sala_id,))
        jugadores = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "jugadores": jugadores}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)