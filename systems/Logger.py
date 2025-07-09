import disnake
from services.config import CHANNEL_LOG
from datetime import datetime

class Logger:

    async def log(self, bot, inter: disnake.ApplicationCommandInteraction, message: str = None):
        """
        Логирует использование команды или сообщение в канал с ID CHANNEL_LOG.
        :param bot: Экземпляр бота
        :param inter: Объект взаимодействия
        :param message: Дополнительное сообщение для логирования
        """
        log_channel = bot.get_channel(CHANNEL_LOG)  # Получаем канал по ID

        if log_channel:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = (
                f"**Пользователь:** {inter.author.display_name} (ID: {inter.author.id})\n"
                f"**Команда:** `{inter.application_command.name}`\n"
                f"**Время:** {timestamp}"
            )
            if message:
                log_message += f"\n**Сообщение:** {message}"

            await log_channel.send(log_message)

    @staticmethod
    async def log_restore(bot, user_id: int, username: str):
        """
        Логирует восстановление пользователя.
        """
        log_channel = bot.get_channel(CHANNEL_LOG)
        if log_channel:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = (
                f"**[Восстановление]**\n"
                f"**Пользователь:** {username} (ID: {user_id})\n"
                f"**Время:** {timestamp}"
            )
            await log_channel.send(log_message)

    @staticmethod
    async def log_archive(bot, user_id: int, username: str):
        """
        Логирует архивацию пользователя.
        """
        log_channel = bot.get_channel(CHANNEL_LOG)
        if log_channel:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = (
                f"**[Архивация]**\n"
                f"**Пользователь:** {username} (ID: {user_id})\n"
                f"**Время:** {timestamp}"
            )
            await log_channel.send(log_message)

    @staticmethod
    async def log_update(bot, user_id: int, username: str, reason: str):
        """
        Логирует обновление данных пользователя.
        """
        log_channel = bot.get_channel(CHANNEL_LOG)
        if log_channel:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = (
                f"**[Обновление]**\n"
                f"**Пользователь:** {username} (ID: {user_id})\n"
                f"**Причина:** {reason}\n"
                f"**Время:** {timestamp}"
            )
            await log_channel.send(log_message)