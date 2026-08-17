"""
Cog de Ranking y Puntos Personales.
Muestra la clasificación general, los puntos individuales y permite gastar puntos.
"""
import discord
from discord import app_commands
from discord.ext import commands
from utils.db import execute_query, fetch_all, fetch_one
from utils.helpers import is_officer


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

    @app_commands.command(name="spend-points", description="Resta puntos a un miembro (canje de recompensa) (Solo Oficiales)")
    async def spend_points(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
        reason: str
    ):
        """
        Descuenta puntos de un miembro. Útil para canjes de recompensas.
        - member: El miembro al que se le restarán puntos.
        - amount: Cantidad de puntos a restar (debe ser positivo).
        - reason: Motivo del gasto (ej: 'Canje de objeto épico').
        """
        # Verificar permisos de oficial
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)
        user_id = str(member.id)

        # Validar que el monto sea positivo
        if amount <= 0:
            await interaction.response.send_message("❌ El monto a restar debe ser un número positivo.", ephemeral=True)
            return

        # Verificar que el usuario tenga suficientes puntos
        user_data = await fetch_one(
            "SELECT total_points FROM user_points WHERE user_id = %s AND server_id = %s",
            (user_id, server_id)
        )

        current_points = user_data['total_points'] if user_data else 0

        if current_points < amount:
            await interaction.response.send_message(
                f"❌ **{member.display_name}** solo tiene **{current_points} puntos**. No puede gastar {amount}.",
                ephemeral=True
            )
            return

        # Restar puntos
        new_total = current_points - amount
        await execute_query(
            """INSERT INTO user_points (user_id, server_id, total_points) 
               VALUES (%s, %s, %s) 
               ON DUPLICATE KEY UPDATE total_points = %s""",
            (user_id, server_id, new_total, new_total)
        )

        # Registrar la transacción en el historial
        await execute_query(
            """INSERT INTO point_transactions (user_id, server_id, amount, reason, performed_by) 
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, server_id, -amount, reason, str(interaction.user.id))
        )

        # Enviar DM al usuario notificando el gasto
        try:
            embed = discord.Embed(
                title="💰 Puntos Gastados",
                description=f"Has gastado **{amount} puntos** en: **{reason}**",
                color=discord.Color.orange()
            )
            embed.add_field(name="Puntos restantes", value=f"**{new_total}**", inline=False)
            embed.set_footer(text=f"Realizado por {interaction.user.display_name}")
            await member.send(embed=embed)
        except discord.Forbidden:
            pass  # El usuario tiene DMs bloqueados

        # Responder al oficial
        await interaction.response.send_message(
            f"✅ Se han restado **{amount} puntos** a **{member.mention}**. Motivo: {reason}\n"
            f"**Puntos restantes:** {new_total}",
            ephemeral=True
        )

    @app_commands.command(name="add-points", description="Añade puntos manualmente a un miembro (Solo Oficiales)")
    async def add_points(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
        reason: str
    ):
        """
        Añade puntos manualmente a un miembro. Útil para ajustes o bonificaciones.
        - member: El miembro que recibirá los puntos.
        - amount: Cantidad de puntos a añadir (debe ser positivo).
        - reason: Motivo del añadido (ej: 'Bonificación por evento').
        """
        # Verificar permisos de oficial
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)
        user_id = str(member.id)

        # Validar que el monto sea positivo
        if amount <= 0:
            await interaction.response.send_message("❌ El monto a añadir debe ser un número positivo.", ephemeral=True)
            return

        # Obtener puntos actuales
        user_data = await fetch_one(
            "SELECT total_points FROM user_points WHERE user_id = %s AND server_id = %s",
            (user_id, server_id)
        )

        current_points = user_data['total_points'] if user_data else 0
        new_total = current_points + amount

        # Actualizar puntos
        await execute_query(
            """INSERT INTO user_points (user_id, server_id, total_points) 
               VALUES (%s, %s, %s) 
               ON DUPLICATE KEY UPDATE total_points = %s""",
            (user_id, server_id, new_total, new_total)
        )

        # Registrar la transacción
        await execute_query(
            """INSERT INTO point_transactions (user_id, server_id, amount, reason, performed_by) 
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, server_id, amount, reason, str(interaction.user.id))
        )

        # Enviar DM al usuario
        try:
            embed = discord.Embed(
                title="⭐ Puntos Añadidos",
                description=f"Has recibido **{amount} puntos** adicionales.",
                color=discord.Color.green()
            )
            embed.add_field(name="Motivo", value=reason, inline=False)
            embed.add_field(name="Nuevo total", value=f"**{new_total}**", inline=False)
            embed.set_footer(text=f"Realizado por {interaction.user.display_name}")
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"✅ Se han añadido **{amount} puntos** a **{member.mention}**. Motivo: {reason}\n"
            f"**Nuevo total:** {new_total}",
            ephemeral=True
        )

    @app_commands.command(name="points-history", description="Muestra el historial de transacciones de un miembro (Solo Oficiales)")
    async def points_history(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        limit: int = 10
    ):
        """
        Muestra el historial de movimientos de puntos de un miembro.
        - member: El miembro a consultar.
        - limit: (Opcional) Número de transacciones a mostrar (default 10, máximo 25).
        """
        if not await is_officer(interaction):
            await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)
            return

        if limit > 25:
            limit = 25

        server_id = str(interaction.guild_id)
        user_id = str(member.id)

        transactions = await fetch_all(
            """SELECT amount, reason, performed_by, created_at 
               FROM point_transactions 
               WHERE user_id = %s AND server_id = %s 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (user_id, server_id, limit)
        )

        if not transactions:
            await interaction.response.send_message(
                f"📭 **{member.display_name}** no tiene transacciones registradas.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📜 Historial de {member.display_name}",
            description=f"Últimas {len(transactions)} transacciones:",
            color=discord.Color.blurple()
        )

        for t in transactions:
            signo = "+" if t['amount'] > 0 else ""
            emoji = "➕" if t['amount'] > 0 else "➖"
            embed.add_field(
                name=f"{emoji} {signo}{t['amount']} pts",
                value=f"📝 {t['reason']}\n👤 Por: <@{t['performed_by']}>\n🕒 {t['created_at'].strftime('%d/%m/%Y %H:%M')}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RankingsCog(bot))