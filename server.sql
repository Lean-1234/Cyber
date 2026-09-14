-- 1. Crear la base de datos y seleccionarla
CREATE DATABASE IF NOT EXISTS cyberpunk_rpg
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE cyberpunk_rpg;

-- 2. Tabla de Usuarios (Perfiles)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Tabla de Personajes (Fichas)
CREATE TABLE IF NOT EXISTS personajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    alias VARCHAR(50) NOT NULL,
    clase ENUM('SOLO', 'NETRUNNER', 'TECHIE') NOT NULL,
    origen VARCHAR(50) DEFAULT 'Street',
    hp_actual INT DEFAULT 100,
    hp_max INT DEFAULT 100,
    ram_actual INT DEFAULT 20,
    ram_max INT DEFAULT 20,
    reflejos INT DEFAULT 8,
    inteligencia INT DEFAULT 9,
    tecnica INT DEFAULT 6,
    sangre_fria INT DEFAULT 7,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Tabla de Salas (Gestionadas por el Game Master)
CREATE TABLE IF NOT EXISTS salas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(4) NOT NULL UNIQUE,
    gm_id INT NOT NULL,
    estado ENUM('ACTIVA', 'CERRADA') DEFAULT 'ACTIVA',
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gm_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Tabla Intermedia: Jugadores Conectados en una Sala
CREATE TABLE IF NOT EXISTS jugadores_sala (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sala_id INT NOT NULL,
    usuario_id INT NOT NULL,
    personaje_id INT NOT NULL,
    conectado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sala_id) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (personaje_id) REFERENCES personajes(id) ON DELETE CASCADE,
    UNIQUE KEY usuario_sala_unica (sala_id, usuario_id) 
) ENGINE=InnoDB;

-- ==============================================================================
-- LIMPIEZA DE DATOS: Borrar registros o personajes de prueba anteriores
-- ==============================================================================
DELETE js FROM jugadores_sala js
JOIN personajes p ON js.personaje_id = p.id
WHERE p.alias LIKE '%Solitary%';

DELETE FROM personajes 
WHERE alias LIKE '%Solitary%';

DELETE FROM salas;