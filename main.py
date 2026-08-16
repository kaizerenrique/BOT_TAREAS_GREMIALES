"""
Bot de Gestión de Gremios para Albion Online.
Sistema de Tareas, Puntos y Ranking.

Autor: [Tu nombre]
Versión: 1.0.0
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Importamos nuestros módulos
from utils.db import init_db_pool

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("No se encontró DISCORD_TOKEN en el archivo .env")


# Configuramos los Intents del bot (necesario para leer miembros y enviar DMs)
intents = discord.Intents.default()
intents.message_content = False  # No necesitamos leer mensajes de texto
intents.members = True           # Necesario para obtener roles y miembros

# Creamos el bot con un prefijo (aunque usaremos slash commands, lo dejamos por si acaso)
bot = commands.Bot(
    command_prefix="!", 
    intents=intents,
    help_command=None  # Desactivamos el help por defecto, crearemos uno propio después
)


@bot.event
async def on_ready():
    """Evento que se dispara cuando el bot se conecta a Discord."""
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"📡 Conectado a {len(bot.guilds)} servidores.")
    
    # Inicializamos el pool de conexiones a MySQL
    try:
        await init_db_pool()
        print("✅ Conexión a MySQL establecida.")
    except Exception as e:
        print(f"❌ Error crítico conectando a MySQL: {e}")
        return

    # Cargamos los Cogs (módulos de comandos)
    try:
        await bot.load_extension("cogs.admin")
        await bot.load_extension("cogs.tasks")
        await bot.load_extension("cogs.reports")
        await bot.load_extension("cogs.rankings")
        print("✅ Todos los Cogs cargados correctamente.")
    except Exception as e:
        print(f"❌ Error cargando Cogs: {e}")

    # Sincronizamos los comandos Slash con Discord (solo una vez al inicio)
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Comandos slash sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Error sincronizando comandos: {e}")


if __name__ == "__main__":
    if not TOKEN:
        print("Error: No se ha definido el token. Revisa tu archivo .env")
    else:
        bot.run(TOKEN)