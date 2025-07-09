from disnake.ext import commands
from systems.perms import permission  # Исправляем импорт
from cogs.base_cog import BaseCog
from services.config import GUILD_ID
import disnake
from models.User import User  # Импортируем модель User
from systems.Logger import Logger  # Добавляем импорт Logger

class EditUser(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.logger = Logger()  # Инициализируем Logger

    @commands.slash_command(name='edit_user', description='Редактировать пользователя', guild_ids=[GUILD_ID])
    @permission("edit_user")  # Используем декоратор
    async def edit_user(self, inter: disnake.ApplicationCommandInteraction, действие: str, атрибут: str, участник: disnake.Member, количество: int):
        user = User(str(участник.id))
        user.load()

        if атрибут == 'опыт':
            current_experience = user.experience
            experience_change = self.calculate_new_value(current_experience, количество, действие)
            user.update_experience(experience_change)
        elif атрибут == 'уровень':
            current_level = user.level
            new_level = self.calculate_new_value(current_level, количество, действие)
            user.level = new_level
            user.special_points = new_level * 40
        elif атрибут == 'спец баллы':
            current_special_points = user.special_points
            new_special_points = self.calculate_new_value(current_special_points, количество, действие)
            user.special_points = new_special_points

        user.save()
        await inter.response.send_message(f"Информация о пользователе {участник.display_name} успешно обновлена.")
        await self.logger.log(self.bot, inter)  # Упрощаем вызов логирования

    def calculate_new_value(self, current_value, количество, действие):
        if действие == 'увеличить':
            return current_value + количество
        elif действие == 'уменьшить':
            return current_value - количество
        elif действие == 'выдать':
            return количество

    @edit_user.autocomplete('действие')
    async def autocomplete_action(self, inter, string: str):
        return ['увеличить', 'уменьшить', 'выдать']

    @edit_user.autocomplete('атрибут')
    async def autocomplete_attribute(self, inter, string: str):
        return ['опыт', 'уровень', 'спец баллы']

    @edit_user.autocomplete('участник')
    async def autocomplete_member(self, inter, string: str):
        return [member.display_name for member in inter.guild.members if string.lower() in member.display_name.lower()]

def setup(bot):
    bot.add_cog(EditUser(bot))