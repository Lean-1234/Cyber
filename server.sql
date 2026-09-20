CREATE DATABASE IF NOT EXISTS cyberpunk_rpg;
USE cyberpunk_rpg;

DROP TABLE IF EXISTS jugadores_sala;
DROP TABLE IF EXISTS salas;
DROP TABLE IF EXISTS personajes;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    alias VARCHAR(50) NOT NULL,
    clase VARCHAR(50) NOT NULL,
    origen VARCHAR(50) NOT NULL,
    inteligencia INT DEFAULT 5,
    reflejos INT DEFAULT 5,
    destreza INT DEFAULT 5,
    tecnica INT DEFAULT 5,
    cool INT DEFAULT 5,
    atractivo INT DEFAULT 5,
    suerte INT DEFAULT 5,
    movimiento INT DEFAULT 5,
    cuerpo INT DEFAULT 5,
    empatia INT DEFAULT 5,
    hp_max INT DEFAULT 35,
    hp_actual INT DEFAULT 35,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE salas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL,
    gm_id INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVA',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gm_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE jugadores_sala (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sala_id INT NOT NULL,
    usuario_id INT NOT NULL,
    personaje_id INT NOT NULL,
    FOREIGN KEY (sala_id) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (personaje_id) REFERENCES personajes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_room (sala_id, usuario_id)
);