"""
Cog de Gestión de Tareas.
Permite a los oficiales crear, editar, activar/desactivar tareas, 
y a los miembros listarlas.
"""
import discord
from discord import app_commands
from discord.ext import commands
from utils.db import execute_query, fetch_all, fetch_one
from utils.helpers import is_officer


class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add-task", description="Crea una nueva tarea para el gremio (Solo Oficiales)")
    async def add_task(
        self,
        interaction: discord.Interaction,
        name: str,
        points: int,
        description: str = None,
        repeatable: bool = False
    ):
        """Comando para que los oficiales agreguen tareas."""
        if not await is_officer(interaction):
            await interaction.response.send_message(
                "❌ No tienes permiso para usar este comando. Necesitas el rol de **Oficial**.",
                ephemeral=True
            )
            return

        server_id = str(interaction.guild_id)

        task_id = await execute_query(
            """INSERT INTO tasks (server_id, name, description, points, repeatable) 
               VALUES (%s, %s, %s, %s, %s)""",
            (server_id, name, description, points, repeatable)
        )

        config = await fetch_one(
            "SELECT tasks_channel_id, guild_name FROM guild_config WHERE server_id = %s",
            (server_id,)
        )

        if not config:
            await interaction.response.send_message(
                "❌ El bot no está configurado en este servidor. Ejecuta `/setup` primero.",
                ephemeral=True
            )
            return

        tasks_channel = self.bot.get_channel(int(config['tasks_channel_id']))
        if tasks_channel:
            embed = discord.Embed(
                title=f"📌 Nueva Tarea: {name}",
                description=description or "Sin descripción adicional.",
                color=discord.Color.blue()
            )
            embed.add_field(name="ID", value=f"`{task_id}`", inline=True)
            embed.add_field(name="Puntos", value=f"**{points}**", inline=True)
            embed.add_field(name="Repetible", value="Sí" if repeatable else "No", inline=True)
            embed.set_footer(text=f"Gremio: {config['guild_name']}")

            await tasks_channel.send(embed=embed)

        await interaction.response.send_message(
            f"✅ Tarea **{name}** creada con ID #{task_id}. Publicada en {tasks_channel.mention}.",
            ephemeral=True
        )

    @app_commands.command(name="list-tasks", description="Muestra la lista de tareas activas disponibles")
    async def list_tasks(self, interaction: discord.Interaction):
        """Lista todas las tareas activas."""
        server_id = str(interaction.guild_id)

        tasks = await fetch_all(
            "SELECT id, name, description, points, repeatable FROM tasks WHERE server_id = %s AND active = 1",
            (server_id,)
        )

        if not tasks:
            await interaction.response.send_message(
                "📭 No hay tareas activas en este momento.",
                ephemeral=True
            )
            return

        mensaje = "📋 **Lista de Tareas Activas:**\n\n"
        for t in tasks:
            mensaje += f"**ID #{t['id']}** - {t['name']}\n"
            mensaje += f"   └ Puntos: {t['points']} | Repetible: {'✅' if t['repeatable'] else '❌'}\n"
            if t['description']:
                mensaje += f"   └ Detalle: {t['description']}\n"
            mensaje += "\n"

        await interaction.response.send_message(mensaje, ephemeral=True)

    @app_commands.command(name="disable-task", description="Desactiva una tarea (no se podrá completar) - Solo Oficiales")
    async def disable_task(self, interaction: discord.Interaction, task_id: int):
        """Desactiva una tarea existente."""
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)

        task = await fetch_one(
            "SELECT id, name, active FROM tasks WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )
        if not task:
            await interaction.response.send_message("❌ Tarea no encontrada.", ephemeral=True)
            return

        if task['active'] == 0:
            await interaction.response.send_message(f"⚠️ La tarea **{task['name']}** ya está desactivada.", ephemeral=True)
            return

        await execute_query(
            "UPDATE tasks SET active = 0 WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )

        config = await fetch_one(
            "SELECT tasks_channel_id FROM guild_config WHERE server_id = %s",
            (server_id,)
        )
        if config:
            channel = self.bot.get_channel(int(config['tasks_channel_id']))
            if channel:
                await channel.send(f"🚫 La tarea **{task['name']}** (ID #{task_id}) ha sido desactivada por {interaction.user.mention}.")

        await interaction.response.send_message(
            f"✅ Tarea **{task['name']}** (ID #{task_id}) desactivada correctamente.",
            ephemeral=True
        )

    @app_commands.command(name="enable-task", description="Re-activa una tarea previamente desactivada - Solo Oficiales")
    async def enable_task(self, interaction: discord.Interaction, task_id: int):
        """Re-activa una tarea desactivada."""
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)

        task = await fetch_one(
            "SELECT id, name, active FROM tasks WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )
        if not task:
            await interaction.response.send_message("❌ Tarea no encontrada.", ephemeral=True)
            return

        if task['active'] == 1:
            await interaction.response.send_message(f"⚠️ La tarea **{task['name']}** ya está activa.", ephemeral=True)
            return

        await execute_query(
            "UPDATE tasks SET active = 1 WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )

        config = await fetch_one(
            "SELECT tasks_channel_id FROM guild_config WHERE server_id = %s",
            (server_id,)
        )
        if config:
            channel = self.bot.get_channel(int(config['tasks_channel_id']))
            if channel:
                await channel.send(f"✅ La tarea **{task['name']}** (ID #{task_id}) ha sido reactivada por {interaction.user.mention}.")

        await interaction.response.send_message(
            f"✅ Tarea **{task['name']}** (ID #{task_id}) reactivada correctamente.",
            ephemeral=True
        )

    @app_commands.command(name="edit-task", description="Edita los campos de una tarea existente - Solo Oficiales")
    @app_commands.describe(
        task_id="ID de la tarea a editar",
        name="Nuevo nombre (opcional)",
        points="Nuevos puntos (opcional)",
        description="Nueva descripción (opcional)",
        repeatable="¿Es repetible? (opcional)"
    )
    async def edit_task(
        self,
        interaction: discord.Interaction,
        task_id: int,
        name: str = None,
        points: int = None,
        description: str = None,
        repeatable: bool = None
    ):
        """Edita uno o varios campos de una tarea."""
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)

        task = await fetch_one(
            "SELECT id, name, points, description, repeatable FROM tasks WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )
        if not task:
            await interaction.response.send_message("❌ Tarea no encontrada.", ephemeral=True)
            return

        updates = []
        params = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if points is not None:
            updates.append("points = %s")
            params.append(points)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if repeatable is not None:
            updates.append("repeatable = %s")
            params.append(1 if repeatable else 0)

        if not updates:
            await interaction.response.send_message("❌ No especificaste ningún campo para editar.", ephemeral=True)
            return

        params.append(task_id)
        params.append(server_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s AND server_id = %s"

        await execute_query(query, tuple(params))

        config = await fetch_one(
            "SELECT tasks_channel_id FROM guild_config WHERE server_id = %s",
            (server_id,)
        )
        if config:
            channel = self.bot.get_channel(int(config['tasks_channel_id']))
            if channel:
                cambios = []
                if name is not None:
                    cambios.append(f"nombre → **{name}**")
                if points is not None:
                    cambios.append(f"puntos → **{points}**")
                if description is not None:
                    cambios.append("descripción actualizada")
                if repeatable is not None:
                    cambios.append(f"repetible → **{'Sí' if repeatable else 'No'}**")
                await channel.send(
                    f"✏️ La tarea **{task['name']}** (ID #{task_id}) fue editada por {interaction.user.mention}.\n"
                    f"Cambios: {', '.join(cambios)}."
                )

        await interaction.response.send_message(
            f"✅ Tarea **{task['name']}** (ID #{task_id}) actualizada correctamente.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TasksCog(bot))