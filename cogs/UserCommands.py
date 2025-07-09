import disnake
from disnake.ext import commands
from systems.perms import permission  # Исправляем импорт
from cogs.base_cog import BaseCog
from models.User import User  # Импортируем модель User
import os
from services.config import GUILD_ID
from datetime import datetime
from systems.Logger import Logger  # Добавляем импорт Logger

class UserCommands(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.logger = Logger()  # Инициализируем Logger

    @commands.slash_command(name='user', description='Получить информацию о пользователе', guild_ids=[GUILD_ID])
    @permission("user")  # Используем декоратор
    async def user_info(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        if member is None:
            member = inter.author

        user = User(str(member.id))
        user.load()
        if not user:
            await inter.response.send_message("Пользователь не найден в базе данных.")
            return

        embed = disnake.Embed(title=f"Информация о пользователе {member.display_name}")
        embed.add_field(name="Имя на сервере", value=user.name, inline=False)
        embed.add_field(name="Количество спец баллов", value=user.special_points, inline=False)
        embed.add_field(name="Уровень", value=user.level, inline=False)
        embed.add_field(name="Опыт", value=f"{int(user.experience)}/1000", inline=False)

        join_date = user.join_date.strftime('%d.%m.%Y') if user.join_date else 'Нет данных'
        embed.add_field(name="Дата вступления", value=join_date, inline=False)

        birth_date = user.birth_date.strftime('%d.%m.%Y') if user.birth_date else 'Нет данных'
        embed.add_field(name="Дата рождения", value=birth_date, inline=False)

        # Проверка наличия изображений
        star_image_path = f"images/stars/{user.star_images}"
        emblem_image_path = f"images/emblems/{user.emblems}"

        if user.star_images == 'Нет данных' or not os.path.exists(star_image_path):
            embed.add_field(name="Звезда", value="Звезда недоступна, обратитесь к администрации.", inline=False)
        else:
            file_star = disnake.File(star_image_path, filename="star.png")
            embed.set_thumbnail(url="attachment://star.png")

        if user.emblems == 'Нет данных' or not os.path.exists(emblem_image_path):
            embed.add_field(name="Эмблема", value="Эмблема недоступна, обратитесь к администрации.", inline=False)
        else:
            file_emblem = disnake.File(emblem_image_path, filename="emblem.png")
            embed.set_image(url="attachment://emblem.png")

        files = []
        if user.star_images != 'Нет данных' and os.path.exists(star_image_path):
            files.append(file_star)
        if user.emblems != 'Нет данных' and os.path.exists(emblem_image_path):
            files.append(file_emblem)

        await inter.response.send_message(embed=embed, files=files)
        await self.logger.log(self.bot, inter)  # Упрощаем вызов логирования

def setup(bot):
    bot.add_cog(UserCommands(bot))