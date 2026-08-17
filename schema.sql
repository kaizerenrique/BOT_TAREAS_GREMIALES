-- Base de datos: Usa la que ya tengas configurada en el .env
-- Asegúrate de que el motor sea InnoDB para soportar claves foráneas.

-- 1. Configuración del servidor (un registro por gremio)
CREATE TABLE IF NOT EXISTS guild_config (
    server_id VARCHAR(20) PRIMARY KEY COMMENT 'ID del servidor de Discord',
    guild_name VARCHAR(100) NOT NULL COMMENT 'Nombre del gremio',
    ranking_channel_id VARCHAR(20) NOT NULL COMMENT 'ID del canal donde se publica el ranking',
    tasks_channel_id VARCHAR(20) NOT NULL COMMENT 'ID del canal donde se publican las tareas',
    officer_role_name VARCHAR(50) DEFAULT 'Oficial' COMMENT 'Nombre del rol que tiene permisos de staff'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Catálogo de tareas
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id VARCHAR(20) NOT NULL COMMENT 'Servidor al que pertenece la tarea',
    name VARCHAR(100) NOT NULL COMMENT 'Nombre corto de la tarea',
    description TEXT COMMENT 'Descripción detallada',
    points INT NOT NULL COMMENT 'Puntos que otorga',
    repeatable BOOLEAN DEFAULT FALSE COMMENT '¿Se puede completar varias veces?',
    active BOOLEAN DEFAULT TRUE COMMENT '¿Está disponible para los miembros?',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_server_active (server_id, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Puntos acumulados por usuario
CREATE TABLE IF NOT EXISTS user_points (
    user_id VARCHAR(20) NOT NULL,
    server_id VARCHAR(20) NOT NULL,
    total_points INT DEFAULT 0,
    PRIMARY KEY (user_id, server_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Reportes de tareas completadas (el corazón del flujo)
CREATE TABLE IF NOT EXISTS task_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL COMMENT 'ID de la tarea completada',
    user_id VARCHAR(20) NOT NULL COMMENT 'Quién la completó',
    server_id VARCHAR(20) NOT NULL COMMENT 'Servidor donde se reportó',
    evidence TEXT COMMENT 'Enlace o texto de evidencia',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(20) DEFAULT NULL COMMENT 'ID del oficial que revisó',
    reviewed_at TIMESTAMP DEFAULT NULL,
    notes TEXT COMMENT 'Comentarios de la revisión (aprobación/rechazo)',
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    INDEX idx_status_server (status, server_id),
    INDEX idx_user_server (user_id, server_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de transacciones de puntos
CREATE TABLE IF NOT EXISTS point_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    server_id VARCHAR(20) NOT NULL,
    amount INT NOT NULL COMMENT 'Positivo = suma, Negativo = resta',
    reason VARCHAR(255) NOT NULL COMMENT 'Motivo de la transacción',
    performed_by VARCHAR(20) NOT NULL COMMENT 'ID del oficial que realizó la operación',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_server (user_id, server_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;