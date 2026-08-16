"""
Cog de Gestión de Tareas.
Permite a los oficiales crear tareas y a los miembros listarlas.
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
        """
        Comando para que los oficiales agreguen tareas.
        - name: Nombre corto de la tarea (ej: 'Recolectar 500 de Piedra')
        - points: Puntos que otorga (ej: 15)
        - description: (Opcional) Detalles adicionales.
        - repeatable: (Opcional) Si es True, se puede completar varias veces.
        """
        # Verificar permisos
        if not await is_officer(interaction):
            await interaction.response.send_message(
                "❌ No tienes permiso para usar este comando. Necesitas el rol de **Oficial**.",
                ephemeral=True
            )
            return

        server_id = str(interaction.guild_id)

        # Insertamos la tarea en la base de datos
        task_id = await execute_query(
            """INSERT INTO tasks (server_id, name, description, points, repeatable) 
               VALUES (%s, %s, %s, %s, %s)""",
            (server_id, name, description, points, repeatable)
        )

        # Obtenemos la configuración del servidor para saber dónde publicar
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

        # Publicamos la tarea en el canal designado
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
        """Lista todas las tareas activas para que los miembros las vean."""
        server_id = str(interaction.guild_id)

        tasks = await fetch_all(
            "SELECT id, name, description, points, repeatable FROM tasks WHERE server_id = %s AND active = 1 ORDER BY id ASC",
            (server_id,)
        )

        if not tasks:
            await interaction.response.send_message(
                "📭 No hay tareas activas en este momento.",
                ephemeral=True
            )
            return

        # Limitar a 20 tareas para evitar mensajes largos
        max_display = 20
        total_tasks = len(tasks)
        tasks_to_show = tasks[:max_display]

        # Crear un embed
        embed = discord.Embed(
            title="📋 Lista de Tareas Activas",
            description=f"Total: **{total_tasks}** tareas disponibles.",
            color=discord.Color.blue()
        )

        # Agrupar en campos para mejor visualización
        for t in tasks_to_show:
            # Formato: ID, Nombre, Puntos, Repetible
            name = f"ID #{t['id']} - {t['name']}"
            value = f"🏅 **{t['points']} pts** | Repetible: {'✅' if t['repeatable'] else '❌'}"
            if t['description']:
                value += f"\n📝 {t['description'][:100]}"  # Trunca descripciones largas
            embed.add_field(name=name, value=value, inline=False)

        if total_tasks > max_display:
            embed.set_footer(text=f"Mostrando {max_display} de {total_tasks} tareas. Usa /list-tasks con filtros para más.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="delete-task", description="Desactiva una tarea (ya no estará disponible) (Solo Oficiales)")
    async def delete_task(self, interaction: discord.Interaction, task_id: int):
        """
        Desactiva una tarea existente. No la elimina físicamente para mantener el historial.
        - task_id: ID de la tarea a desactivar.
        """
        # Verificar permisos de oficial
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)

        # Verificar que la tarea existe y está activa
        task = await fetch_one(
            "SELECT id, name, active FROM tasks WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )

        if not task:
            await interaction.response.send_message("❌ Tarea no encontrada.", ephemeral=True)
            return

        if task['active'] == 0:
            await interaction.response.send_message(
                f"⚠️ La tarea **{task['name']}** ya está desactivada.",
                ephemeral=True
            )
            return

        # Desactivar la tarea
        await execute_query(
            "UPDATE tasks SET active = 0 WHERE id = %s",
            (task_id,)
        )

        await interaction.response.send_message(
            f"✅ Tarea **{task['name']}** (ID #{task_id}) ha sido desactivada. Ya no aparecerá en `/list-tasks`.",
            ephemeral=True
        )

    @app_commands.command(name="edit-task", description="Edita una tarea existente (Solo Oficiales)")
    async def edit_task(
        self,
        interaction: discord.Interaction,
        task_id: int,
        name: str = None,
        points: int = None,
        description: str = None,
        repeatable: bool = None
    ):
        """
        Modifica los campos de una tarea. Solo se actualizan los parámetros que se proporcionen.
        - task_id: ID de la tarea a editar.
        - name: Nuevo nombre (opcional)
        - points: Nuevos puntos (opcional)
        - description: Nueva descripción (opcional)
        - repeatable: Nuevo valor (opcional)
        """
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)

        # Verificar que la tarea existe y pertenece al servidor
        task = await fetch_one(
            "SELECT id, name, points, description, repeatable FROM tasks WHERE id = %s AND server_id = %s",
            (task_id, server_id)
        )

        if not task:
            await interaction.response.send_message("❌ Tarea no encontrada.", ephemeral=True)
            return

        # Construir la consulta de actualización dinámica
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
            params.append(repeatable)

        if not updates:
            await interaction.response.send_message(
                "⚠️ No se proporcionó ningún campo para actualizar.",
                ephemeral=True
            )
            return

        # Añadir el ID al final de los parámetros
        params.append(task_id)

        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
        await execute_query(query, tuple(params))

        # Obtener la tarea actualizada para mostrar los cambios
        updated_task = await fetch_one(
            "SELECT name, points, description, repeatable FROM tasks WHERE id = %s",
            (task_id,)
        )

        embed = discord.Embed(
            title="✏️ Tarea Actualizada",
            description=f"**ID #{task_id}**",
            color=discord.Color.orange()
        )
        embed.add_field(name="Nombre", value=updated_task['name'], inline=True)
        embed.add_field(name="Puntos", value=updated_task['points'], inline=True)
        embed.add_field(name="Repetible", value="Sí" if updated_task['repeatable'] else "No", inline=True)
        if updated_task['description']:
            embed.add_field(name="Descripción", value=updated_task['description'], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TasksCog(bot))