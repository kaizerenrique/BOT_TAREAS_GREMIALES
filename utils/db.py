"""
Módulo de conexión a la base de datos MySQL usando Pool asíncrono.
Maneja todas las consultas SQL de forma no bloqueante.
"""
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración leída desde el archivo .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'db': os.getenv('DB_NAME'),
    'autocommit': True,
    'charset': 'utf8mb4'
}

# Pool de conexiones global (se inicializa al arrancar el bot)
_pool = None


async def init_db_pool():
    """Inicializa el pool de conexiones a MySQL. Debe llamarse en el setup del bot."""
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            **DB_CONFIG,
            minsize=1,      # Mínimo 1 conexión activa
            maxsize=5       # Máximo 5 conexiones concurrentes
        )
        print("[DB] Pool de conexiones creado exitosamente.")
    return _pool


async def get_pool():
    """Retorna el pool de conexiones. Lanza excepción si no está inicializado."""
    if _pool is None:
        raise RuntimeError("El pool de base de datos no ha sido inicializado.")
    return _pool


async def execute_query(query: str, params: tuple = ()) -> int:
    """
    Ejecuta una consulta que modifica datos (INSERT, UPDATE, DELETE).
    Retorna el número de filas afectadas o el ID de la última inserción.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            if query.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            return cursor.rowcount


async def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Ejecuta un SELECT y retorna un solo registro como diccionario."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchone()


async def fetch_all(query: str, params: tuple = ()) -> list:
    """Ejecuta un SELECT y retorna todos los registros como lista de diccionarios."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()