# 🤖 Albion Guild Tasks Bot

**Bot oficial para la gestión de tareas, puntos y ranking en gremios de Albion Online.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.4.0-blue.svg)](https://github.com/Rapptz/discord.py)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Descripción

Este bot permite a los gremios de **Albion Online** (o cualquier comunidad en Discord) implementar un **sistema de misiones y recompensas** basado en puntos. Los oficiales pueden crear tareas, los miembros reportan su cumplimiento, y el staff aprueba o rechaza las solicitudes. Todo queda registrado en una base de datos MySQL, y se genera automáticamente un **ranking público** con los puntos acumulados.

**Características clave:**
- ✅ Configuración por servidor (nombre, canales, rol de oficiales).
- ✅ Creación, edición y desactivación de tareas con puntos.
- ✅ Sistema de reportes con evidencia opcional.
- ✅ Flujo de aprobación/rechazo con notificaciones por DM.
- ✅ Ranking global y estadísticas personales.
- ✅ Comandos Slash integrados y mensajes efímeros.
- ✅ Historial completo para auditoría.

---

## 📌 Comandos disponibles

| Comando | Quién lo usa | Descripción |
|---------|--------------|-------------|
| `/setup` | Administrador | Configura el gremio (nombre, canales, rol de oficiales). |
| `/add-task` | Oficial | Crea una nueva tarea (nombre, puntos, descripción, repetible). |
| `/edit-task` | Oficial | Modifica campos de una tarea existente (parcial o total). |
| `/delete-task` | Oficial | Desactiva una tarea (ya no aparece en el listado). |
| `/list-tasks` | Todos | Muestra las tareas activas (hasta 20, con embed). |
| `/complete-task` | Miembro | Reporta la finalización de una tarea (evidencia opcional). |
| `/review-tasks` | Oficial | Lista los reportes pendientes de revisión. |
| `/approve-task` | Oficial | Aprueba un reporte, otorga puntos y envía DM. |
| `/reject-task` | Oficial | Rechaza un reporte, envía DM con el motivo. |
| `/ranking` | Todos | Muestra el Top N de jugadores con más puntos. |
| `/my-points` | Todos | Consulta tus puntos y posición en el ranking. |

---

## 🛠️ Requisitos previos

- **Python 3.10 o superior** (se recomienda 3.12, pero funciona con 3.13 con el paquete `audioop-lts`).
- **MySQL 8.0** (o MariaDB 10.5+).
- **Cuenta de Discord Developer** (para crear el bot y obtener el token).
- **Servidor Linux** (Ubuntu 22.04 recomendado) para despliegue.

---


