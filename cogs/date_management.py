import disnake
from disnake.ext import commands
from models.User import User
from systems.perms import permission  # Исправляем импорт
from services.config import GUILD_ID
from cogs.base_cog import BaseCog
from systems.Logger import Logger  # Добавляем импорт Logger
import re  # Для проверки формата даты
from datetime import datetime  # Добавляем импорт datetime

class DateManagement(BaseCog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger()  # Инициализируем Logger

    @commands.slash_command(name='edit_date', description='Изменить дату вступления или дату рождения пользователя', guild_ids=[GUILD_ID])
    @permission("edit_date")  # Используем декоратор
    async def edit_date(self, inter: disnake.ApplicationCommandInteraction, date_type: str, member: disnake.Member, date: str):
        # Проверка формата даты
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date):
            await inter.response.send_message("Неверный формат даты. Используйте формат ДД.ММ.ГГГГ.", ephemeral=True)
            return

        try:
            date_obj = datetime.strptime(date, "%d.%m.%Y")  # Преобразуем строку в объект datetime
        except ValueError:
            await inter.response.send_message("Ошибка при обработке даты. Проверьте формат.", ephemeral=True)
            return

        user = User(str(member.id))
        user.load()

        if date_type == 'Дата вступления':
            user.set_join_date(date_obj)  # Передаем объект datetime
            user.save()
            await inter.response.send_message(f"Дата вступления пользователя {member.display_name} успешно установлена на {date}.")
        elif date_type == 'Дата рождения':
            user.set_birth_date(date_obj)  # Передаем объект datetime
            user.save()
            await inter.response.send_message(f"Дата рождения пользователя {member.display_name} успешно установлена на {date}.")
        else:
            await inter.response.send_message(f"Неверный тип даты: {date_type}. Используйте 'Дата вступления' или 'Дата рождения'.", ephemeral=True)
        
        await self.logger.log(self.bot, inter)  # Упрощаем вызов логирования

    @edit_date.autocomplete('date_type')
    async def autocomplete_date_type(self, inter: disnake.ApplicationCommandInteraction, string: str):
        return ['Дата вступления', 'Дата рождения']

def setup(bot):
    bot.add_cog(DateManagement(bot))
