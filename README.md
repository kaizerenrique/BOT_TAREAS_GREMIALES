# 🤖 Albion Guild Tasks Bot

**Bot oficial para la gestión de tareas, puntos y ranking en gremios de Albion Online.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.4.0-blue.svg)](https://github.com/Rapptz/discord.py)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Descripción

Este bot permite a los gremios de **Albion Online** (o cualquier comunidad en Discord) implementar un **sistema de misiones y recompensas** basado en puntos. Los oficiales pueden crear tareas, los miembros reportan su cumplimiento, y el staff aprueba o rechaza las solicitudes. Todo queda registrado en una base de datos MySQL, y se genera automáticamente un **ranking público** con los puntos acumulados.

---

## ✨ Características principales

- ✅ **Configuración por servidor** – Cada gremio tiene su propio nombre, canales y rol de oficiales.
- ✅ **Creación de tareas** – Oficiales definen nombre, puntos, descripción y si es repetible.
- ✅ **Edición y desactivación** – Permite modificar tareas existentes o darlas de baja sin perder el historial.
- ✅ **Sistema de reportes** – Los miembros reportan tareas completadas con evidencia opcional.
- ✅ **Flujo de aprobación** – Oficiales revisan, aprueban o rechazan los reportes con notificaciones por DM.
- ✅ **Ranking automático** – Clasificación global de los miembros según puntos acumulados.
- ✅ **Estadísticas personales** – Cada miembro consulta sus puntos y posición en el ranking.
- ✅ **Comandos Slash** – Totalmente integrado con la interfaz moderna de Discord.
- ✅ **Mensajes Directos (DM)** – Notificaciones automáticas al aprobar o rechazar tareas.
- ✅ **Historial completo** – Todas las transacciones quedan registradas para auditoría.

---

## 📌 Comandos disponibles

| Comando | Quién lo usa | Descripción |
|---------|--------------|-------------|
| `/setup` | Administrador | Configura el gremio (nombre, canales, rol de oficiales). |
| `/add-task` | Oficial | Crea una nueva tarea (nombre, puntos, descripción, repetible). |
| `/edit-task` | Oficial | Modifica los campos de una tarea existente (parcial o totalmente). |
| `/delete-task` | Oficial | Desactiva una tarea (ya no aparece en el listado). |
| `/list-tasks` | Todos | Muestra todas las tareas activas disponibles. |
| `/complete-task` | Miembro | Reporta la finalización de una tarea (con evidencia opcional). |
| `/review-tasks` | Oficial | Lista todos los reportes pendientes de revisión. |
| `/approve-task` | Oficial | Aprueba un reporte, otorga puntos y envía DM al usuario. |
| `/reject-task` | Oficial | Rechaza un reporte, envía DM con el motivo al usuario. |
| `/ranking` | Todos | Muestra el Top N de jugadores con más puntos. |
| `/my-points` | Todos | Consulta tus puntos acumulados y tu posición en el ranking. |
| `/sync` | Administrador | Sincroniza los comandos slash manualmente (útil tras actualizaciones). |

---

## 🛠️ Requisitos previos

- **Python 3.10 o superior**
- **MySQL 8.0** (o MariaDB 10.5+)
- **Cuenta de Discord Developer** (para crear el bot y obtener el token)
- **Servidor de pruebas o producción** (local o VPS con Ubuntu 22.04)

---

