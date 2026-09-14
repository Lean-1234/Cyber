from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import random
import string
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.')
CORS(app)  # Permite peticiones desde el navegador frontend

# ==============================================================================
# CONFIGURACIÓN DE CONEXIÓN A MYSQL
# ==============================================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Cybermaniaco456',  # <-- Tu contraseña de MySQL
    'database': 'cyberpunk_rpg',
    'port': 3306
}

def get_db_connection():
    """Establece conexión con MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


# ==============================================================================
# RUTAS PARA MOSTRAR LAS PÁGINAS HTML EN EL NAVEGADOR
# ==============================================================================

@app.route('/')
def inicio():
    """Al entrar a localhost:5000, carga directamente la pantalla de Login."""
    return send_from_directory('.', 'login.html')

@app.route('/<path:filename>')
def servir_archivos(filename):
    """Permite cargar el resto de las páginas (index.html, gm-dashboard.html, etc)."""
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "Archivo no encontrado (404)", 404


# ==============================================================================
# AUTENTICACIÓN: REGISTRO E INICIO DE SESIÓN (API)
# ==============================================================================

# 1. REGISTRAR USUARIO (SIN PERSONAJE AUTOMÁTICO)
@app.route('/api/auth/registro', methods=['POST'])
def registrar_usuario():
    try:
        data = request.json or {}
        username = str(data.get('username', '')).strip()
        email = str(data.get('email', '')).strip().lower()
        password = str(data.get('password', ''))

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "Todos los campos son obligatorios."}), 400

        # Encriptar la contraseña antes de guardar en MySQL
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verificar si ya existe usuario o email
        cursor.execute("SELECT id FROM usuarios WHERE username = %s OR email = %s", (username, email))
        existe = cursor.fetchone()
        if existe:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "El nombre de usuario o email ya está registrado."}), 400

        # Insertar nuevo usuario (Limpiando registros basura anteriores)
        cursor.execute("""
            INSERT INTO usuarios (username, email, password_hash) 
            VALUES (%s, %s, %s)
        """, (username, email, password_hash))
        
        conn.commit()
        nuevo_id = cursor.lastrowid

        # ELIMINADO: Ya no creamos personajes automáticos aquí para evitar "V_Solitary"

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Usuario registrado exitosamente.",
            "usuario": {"id": nuevo_id, "username": username, "email": email}
        }), 201

    except mysql.connector.Error as db_err:
        return jsonify({"status": "error", "message": f"Error en BD: {str(db_err)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error del servidor: {str(e)}"}), 500


# 2. INICIAR SESIÓN (LOGIN)
@app.route('/api/auth/login', methods=['POST'])
def login_usuario():
    try:
        data = request.json or {}
        username_or_email = str(data.get('username_or_email', '')).strip()
        password = str(data.get('password', ''))

        if not username_or_email or not password:
            return jsonify({"status": "error", "message": "Por favor ingresa usuario y contraseña."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Buscar usuario por Username o Email
        cursor.execute("""
            SELECT id, username, email, password_hash 
            FROM usuarios 
            WHERE username = %s OR email = %s
        """, (username_or_email, username_or_email))
        usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        if not usuario or not check_password_hash(usuario['password_hash'], password):
            return jsonify({"status": "error", "message": "Credenciales inválidas."}), 401

        return jsonify({
            "status": "success",
            "message": "Inicio de sesión correcto.",
            "usuario": {
                "id": usuario['id'],
                "username": usuario['username'],
                "email": usuario['email']
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error inesperado: {str(e)}"}), 500


# ==============================================================================
# GESTIÓN DE SALAS Y PERSONAJES
# ==============================================================================

# OBTENER PERSONAJES DE UN USUARIO
@app.route('/api/personajes/<int:usuario_id>', methods=['GET'])
def obtener_personajes(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, alias, clase, origen, hp_actual, hp_max 
            FROM personajes 
            WHERE usuario_id = %s
        """, (usuario_id,))
        personajes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "personajes": personajes}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# CREAR SALA (GM)
@app.route('/api/salas/crear', methods=['POST'])
def crear_sala():
    try:
        data = request.json or {}
        gm_id = data.get('gm_id', 1)

        caracteres = string.ascii_uppercase + string.digits
        codigo = ''.join(random.choices(caracteres, k=4))

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


# UNIRSE A LA SALA
@app.route('/api/salas/unirse', methods=['POST'])
def unirse_sala():
    try:
        data = request.json or {}
        codigo = str(data.get('codigo', '')).strip().upper()
        usuario_id = data.get('usuario_id')
        personaje_id = data.get('personaje_id')

        if not codigo or not usuario_id or not personaje_id:
            return jsonify({"status": "error", "message": "Datos incompletos para unirse a la sala."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id FROM salas 
            WHERE codigo = %s AND estado = 'ACTIVA' 
            ORDER BY id DESC LIMIT 1
        """, (codigo,))
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

        return jsonify({"status": "success", "message": "Conectado exitosamente a la sala.", "sala_id": sala['id']}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# OBTENER JUGADORES CONECTADOS A LA SALA
@app.route('/api/salas/<int:sala_id>/jugadores', methods=['GET'])
def obtener_jugadores_sala(sala_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
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
    print("\n========================================================")
    print(" SERVIDOR CYBERPUNK RPG INICIADO EN http://localhost:5000 ")
    print("========================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True)