"""
Cog de Administración.
Contiene el comando /setup para configurar el gremio.
"""
import discord
from discord import app_commands
from discord.ext import commands
from utils.db import execute_query, fetch_one


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configura el bot para este servidor (Solo Administrador)")
    @app_commands.default_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        guild_name: str,
        ranking_channel: discord.TextChannel,
        tasks_channel: discord.TextChannel,
        officer_role: discord.Role
    ):
        """
        Configura la información principal del gremio.
        - guild_name: Nombre visible en los rankings.
        - ranking_channel: Canal donde se publicarán los rankings automáticos.
        - tasks_channel: Canal donde se publicarán las nuevas tareas.
        - officer_role: Rol que tendrá permisos de gestión (aprobar/rechazar tareas).
        """
        server_id = str(interaction.guild_id)

        # Verificamos si ya existe una configuración para este servidor
        existing = await fetch_one(
            "SELECT server_id FROM guild_config WHERE server_id = %s",
            (server_id,)
        )

        if existing:
            # Si existe, la actualizamos (UPSERT)
            await execute_query(
                """UPDATE guild_config 
                   SET guild_name = %s, ranking_channel_id = %s, 
                       tasks_channel_id = %s, officer_role_name = %s 
                   WHERE server_id = %s""",
                (guild_name, str(ranking_channel.id), str(tasks_channel.id), officer_role.name, server_id)
            )
            mensaje = "✅ Configuración **actualizada** correctamente."
        else:
            # Si no existe, la insertamos
            await execute_query(
                """INSERT INTO guild_config 
                   (server_id, guild_name, ranking_channel_id, tasks_channel_id, officer_role_name) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (server_id, guild_name, str(ranking_channel.id), str(tasks_channel.id), officer_role.name)
            )
            mensaje = "✅ Configuración **guardada** correctamente."

        # Enviamos un mensaje de confirmación (solo visible para el admin)
        embed = discord.Embed(
            title="⚙️ Configuración del Gremio",
            description=f"**Gremio:** {guild_name}\n"
                        f"**Canal de Ranking:** {ranking_channel.mention}\n"
                        f"**Canal de Tareas:** {tasks_channel.mention}\n"
                        f"**Rol de Oficiales:** {officer_role.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(mensaje, embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))