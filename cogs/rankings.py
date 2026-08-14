"""
Cog de Ranking y Puntos Personales.
Muestra la clasificación general y los puntos individuales.
"""
import discord
from discord import app_commands
from discord.ext import commands
from utils.db import fetch_all, fetch_one


class RankingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="Muestra el ranking de puntos del gremio")
    async def ranking(self, interaction: discord.Interaction, top: int = 10):
        """
        Muestra el Top N de jugadores con más puntos.
        - top: (Opcional) Cantidad de jugadores a mostrar (default 10, máximo 25).
        """
        server_id = str(interaction.guild_id)

        # Limitar el top a 25 para evitar mensajes muy largos
        if top > 25:
            top = 25

        # Obtener la configuración para el nombre del gremio
        config = await fetch_one(
            "SELECT guild_name FROM guild_config WHERE server_id = %s",
            (server_id,)
        )
        guild_name = config['guild_name'] if config else "Gremio"

        # Obtener los puntos ordenados
        rows = await fetch_all(
            """SELECT user_id, total_points 
               FROM user_points 
               WHERE server_id = %s 
               ORDER BY total_points DESC 
               LIMIT %s""",
            (server_id, top)
        )

        if not rows:
            await interaction.response.send_message(
                f"🏆 **Ranking de {guild_name}**\nAún no hay puntos registrados.",
                ephemeral=True
            )
            return

        # Construir el mensaje
        mensaje = f"🏆 **Ranking de {guild_name}**\n\n"
        for idx, row in enumerate(rows, 1):
            # Mencionamos al usuario directamente
            mensaje += f"**{idx}.** <@{row['user_id']}> → **{row['total_points']} pts**\n"

        await interaction.response.send_message(mensaje)

    @app_commands.command(name="my-points", description="Muestra tus puntos acumulados y tu posición en el ranking")
    async def my_points(self, interaction: discord.Interaction):
        """Consulta personal de puntos y posición."""
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        # Obtener puntos del usuario
        user_data = await fetch_one(
            "SELECT total_points FROM user_points WHERE user_id = %s AND server_id = %s",
            (user_id, server_id)
        )

        total = user_data['total_points'] if user_data else 0

        # Calcular posición (contar cuántos tienen más puntos)
        if total > 0:
            position_data = await fetch_one(
                "SELECT COUNT(*) + 1 AS pos FROM user_points WHERE server_id = %s AND total_points > %s",
                (server_id, total)
            )
            pos = position_data['pos'] if position_data else "sin clasificar"
        else:
            pos = "sin clasificar"

        # Obtener el nombre del gremio para personalizar
        config = await fetch_one(
            "SELECT guild_name FROM guild_config WHERE server_id = %s",
            (server_id,)
        )
        guild_name = config['guild_name'] if config else "Gremio"

        embed = discord.Embed(
            title=f"📊 Tus Puntos en {guild_name}",
            description=f"Acumulas un total de **{total} puntos**.",
            color=discord.Color.purple()
        )
        embed.add_field(name="Posición en el Ranking", value=f"#{pos}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RankingsCog(bot))