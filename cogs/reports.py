"""
Cog de Reportes.
Maneja el ciclo de vida de una tarea completada: 
reporte -> revisión -> aprobación/rechazo.
"""
import discord
from discord import app_commands
from discord.ext import commands
from utils.db import execute_query, fetch_one, fetch_all
from utils.helpers import is_officer


class ReportsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="complete-task", description="Reporta que has completado una tarea")
    async def complete_task(
        self,
        interaction: discord.Interaction,
        task_id: int,
        evidence: str = None
    ):
        """
        Un miembro reporta que completó una tarea.
        - task_id: El ID de la tarea (obtenido de /list-tasks o del canal).
        - evidence: (Opcional) Enlace a captura, texto explicativo, etc.
        """
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        # 1. Verificar que la tarea existe y está activa
        task = await fetch_one(
            "SELECT id, name, points, repeatable FROM tasks WHERE id = %s AND server_id = %s AND active = 1",
            (task_id, server_id)
        )
        if not task:
            await interaction.response.send_message(
                "❌ Tarea no encontrada, inactiva o no existe en este servidor.",
                ephemeral=True
            )
            return

        # 2. Si no es repetible, verificar si el usuario ya la completó antes (aprobada)
        if not task['repeatable']:
            existing = await fetch_one(
                "SELECT id FROM task_reports WHERE task_id = %s AND user_id = %s AND server_id = %s AND status = 'approved'",
                (task_id, user_id, server_id)
            )
            if existing:
                await interaction.response.send_message(
                    f"❌ La tarea **{task['name']}** no es repetible y ya la completaste anteriormente.",
                    ephemeral=True
                )
                return

        # 3. Crear el reporte en estado 'pending'
        report_id = await execute_query(
            """INSERT INTO task_reports (task_id, user_id, server_id, evidence) 
               VALUES (%s, %s, %s, %s)""",
            (task_id, user_id, server_id, evidence)
        )

        await interaction.response.send_message(
            f"✅ ¡Reporte enviado! (ID #{report_id})\n"
            f"Los oficiales revisarán tu solicitud para la tarea **{task['name']}**.\n"
            f"Recibirás un mensaje privado cuando sea aprobada o rechazada.",
            ephemeral=True
        )

        # Opcional: Notificar a los oficiales en un canal de logs (lo dejamos para ampliación)

    @app_commands.command(name="review-tasks", description="Muestra los reportes pendientes de aprobación (Solo Oficiales)")
    async def review_tasks(self, interaction: discord.Interaction):
        """Los oficiales ven todos los reportes pendientes."""
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)

        reports = await fetch_all(
            """SELECT r.id, r.user_id, t.name AS task_name, r.evidence, r.submitted_at 
               FROM task_reports r
               JOIN tasks t ON r.task_id = t.id
               WHERE r.server_id = %s AND r.status = 'pending'
               ORDER BY r.submitted_at ASC""",
            (server_id,)
        )

        if not reports:
            await interaction.response.send_message("📭 No hay reportes pendientes.", ephemeral=True)
            return

        mensaje = "📋 **Reportes Pendientes de Revisión:**\n\n"
        for r in reports:
            usuario = self.bot.get_user(int(r['user_id']))
            nombre_usuario = usuario.display_name if usuario else r['user_id']
            mensaje += f"**Reporte #{r['id']}**\n"
            mensaje += f"   👤 Usuario: {nombre_usuario} (<@{r['user_id']}>)\n"
            mensaje += f"   📌 Tarea: {r['task_name']}\n"
            mensaje += f"   📎 Evidencia: {r['evidence'] or 'Sin evidencia'}\n"
            mensaje += f"   🕒 Enviado: {r['submitted_at'].strftime('%d/%m/%Y %H:%M')}\n\n"

        await interaction.response.send_message(mensaje, ephemeral=True)

    @app_commands.command(name="approve-task", description="Aprueba un reporte y otorga los puntos (Solo Oficiales)")
    async def approve_task(
        self,
        interaction: discord.Interaction,
        report_id: int,
        notes: str = None
    ):
        """Aprueba un reporte, suma puntos al usuario y le envía un DM."""
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)
        reviewer_id = str(interaction.user.id)

        # 1. Obtener el reporte con la tarea asociada
        report = await fetch_one(
            """SELECT r.id, r.user_id, r.task_id, r.status, t.points, t.name AS task_name
               FROM task_reports r
               JOIN tasks t ON r.task_id = t.id
               WHERE r.id = %s AND r.server_id = %s""",
            (report_id, server_id)
        )

        if not report:
            await interaction.response.send_message("❌ Reporte no encontrado.", ephemeral=True)
            return

        if report['status'] != 'pending':
            await interaction.response.send_message(
                f"⚠️ Este reporte ya fue {report['status']} anteriormente.",
                ephemeral=True
            )
            return

        # 2. Actualizar el estado del reporte
        await execute_query(
            """UPDATE task_reports 
               SET status = 'approved', reviewed_by = %s, reviewed_at = NOW(), notes = %s 
               WHERE id = %s""",
            (reviewer_id, notes, report_id)
        )

        # 3. Sumar puntos al usuario
        await execute_query(
            """INSERT INTO user_points (user_id, server_id, total_points) 
               VALUES (%s, %s, %s) 
               ON DUPLICATE KEY UPDATE total_points = total_points + %s""",
            (report['user_id'], server_id, report['points'], report['points'])
        )

        # 4. Enviar un Mensaje Directo al usuario
        usuario = self.bot.get_user(int(report['user_id']))
        if usuario:
            try:
                embed = discord.Embed(
                    title="✅ ¡Tarea Aprobada!",
                    description=f"Has recibido **{report['points']} puntos** por completar la tarea **{report['task_name']}**.",
                    color=discord.Color.green()
                )
                if notes:
                    embed.add_field(name="Nota del oficial", value=notes, inline=False)
                await usuario.send(embed=embed)
            except discord.Forbidden:
                # Si el usuario tiene los DMs bloqueados, no podemos hacer nada
                pass

        await interaction.response.send_message(
            f"✅ Reporte #{report_id} aprobado. Se otorgaron **{report['points']} puntos** a <@{report['user_id']}>.",
            ephemeral=True
        )

    @app_commands.command(name="reject-task", description="Rechaza un reporte (Solo Oficiales)")
    async def reject_task(
        self,
        interaction: discord.Interaction,
        report_id: int,
        reason: str
    ):
        """Rechaza un reporte, no otorga puntos y notifica al usuario el motivo."""
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)
        reviewer_id = str(interaction.user.id)

        # Obtener el reporte
        report = await fetch_one(
            """SELECT r.id, r.user_id, r.task_id, r.status, t.name AS task_name
               FROM task_reports r
               JOIN tasks t ON r.task_id = t.id
               WHERE r.id = %s AND r.server_id = %s""",
            (report_id, server_id)
        )

        if not report:
            await interaction.response.send_message("❌ Reporte no encontrado.", ephemeral=True)
            return

        if report['status'] != 'pending':
            await interaction.response.send_message(
                f"⚠️ Este reporte ya fue {report['status']} anteriormente.",
                ephemeral=True
            )
            return

        # Actualizar estado
        await execute_query(
            """UPDATE task_reports 
               SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW(), notes = %s 
               WHERE id = %s""",
            (reviewer_id, reason, report_id)
        )

        # Notificar al usuario por DM
        usuario = self.bot.get_user(int(report['user_id']))
        if usuario:
            try:
                embed = discord.Embed(
                    title="❌ Tarea Rechazada",
                    description=f"Tu reporte para la tarea **{report['task_name']}** fue rechazado.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Motivo", value=reason, inline=False)
                embed.add_field(name="Consejo", value="Revisa el motivo y vuelve a intentarlo si la tarea es repetible.", inline=False)
                await usuario.send(embed=embed)
            except discord.Forbidden:
                pass

        await interaction.response.send_message(
            f"❌ Reporte #{report_id} rechazado. Motivo enviado a <@{report['user_id']}>.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ReportsCog(bot))