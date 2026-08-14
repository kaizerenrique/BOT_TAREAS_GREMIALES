"""
Helpers para la lógica del bot: verificación de roles, formateo de mensajes, etc.
"""
import discord


async def is_officer(interaction: discord.Interaction) -> bool:
    """
    Verifica si el usuario que ejecuta el comando tiene el rol de 'Oficial'
    definido en la configuración del servidor.
    """
    # Importamos db aquí para evitar dependencias circulares al inicio
    from utils.db import fetch_one

    config = await fetch_one(
        "SELECT officer_role_name FROM guild_config WHERE server_id = %s",
        (str(interaction.guild_id),)
    )
    
    if not config:
        # Si no hay configuración, asumimos que solo el admin puede usarlo
        # o denegamos el permiso. En este caso, denegamos si no hay setup.
        return False

    role_name = config['officer_role_name']
    # Buscamos el rol en el servidor por nombre (sensible a mayúsculas)
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    
    if not role:
        # Si el rol no existe físicamente en el servidor, denegamos.
        return False
        
    return role in interaction.user.roles


def format_ranking(users_data: list, guild_name: str) -> str:
    """
    Formatea una lista de usuarios (con user_id y total_points) en una tabla.
    """
    if not users_data:
        return f"🏆 **Ranking de {guild_name}**\nAún no hay puntos registrados."

    header = f"🏆 **Ranking de {guild_name}**\n"
    lines = []
    for idx, row in enumerate(users_data, 1):
        # Nota: El nombre lo obtendremos desde Discord en el comando, 
        # aquí solo armamos la estructura base.
        lines.append(f"{idx}. <@{row['user_id']}> → **{row['total_points']} pts**")
    
    return header + "\n".join(lines)