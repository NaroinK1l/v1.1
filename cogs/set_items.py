import disnake
from disnake.ext import commands
from systems.perms import permission  # Исправляем импорт
from cogs.base_cog import BaseCog
import os
from services.config import GUILD_ID, BASE_DIR
from models.User import User  # Импортируем модель User
from systems.Logger import Logger  # Добавляем импорт Logger

class SetItems(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.logger = Logger()  # Инициализируем Logger

    @commands.slash_command(
        name='set_items',
        description='Назначить список картинок участникам',
        guild_ids=[GUILD_ID]
    )
    @permission("set")  # Используем декоратор
    async def set_items(
        self,
        inter: disnake.ApplicationCommandInteraction,
        участник: disnake.Member = commands.Param(description="Выберите участника"),
        картинка: str = commands.Param(description="Выберите картинку")
    ):
        await inter.response.defer(ephemeral=True)  # Отсрочка ответа

        # Логика назначения картинки участнику
        user = User(str(участник.id))
        user.load()
        if not user:
            await inter.edit_original_message(
                content=f"Пользователь {участник.display_name} не найден в базе данных."
            )
            return

        user.emblems = картинка
        user.save()

        await inter.edit_original_message(
            content=f"Участнику {участник.display_name} назначена картинка: {картинка}."
        )

        # Логируем действие
        await self.logger.log(self.bot, inter)

    @set_items.autocomplete('участник')
    async def autocomplete_member(self, inter, string: str):
        return [member.display_name for member in inter.guild.members if string.lower() in member.display_name.lower()]

    @set_items.autocomplete('картинка')
    async def autocomplete_image(self, inter, string: str):
        available_items = self.get_available_items()
        return [item for item in available_items if string.lower() in item.lower()]

    def get_choices(self):
        return self.get_available_items()

    @staticmethod
    def get_available_items():
        # Путь к папке с эмблемами
        item_dir = os.path.join(BASE_DIR, "images", "emblems")
        if not os.path.exists(item_dir):
            return []

        # Получаем список доступных PNG-файлов
        return [f for f in os.listdir(item_dir) if f.endswith(".png") and os.path.isfile(os.path.join(item_dir, f))]

def setup(bot):
    bot.add_cog(SetItems(bot))

    # Закомментирован выбор звезды
    # @commands.slash_command(name='set', description='Назначить звезду или эмблему пользователю', guild_ids=[GUILD_ID])
    # @permission("set")  # Используем декоратор
    # async def set_item(self, inter: disnake.ApplicationCommandInteraction, тип_предмета: str, участник: disnake.Member = None):
    #     await inter.response.defer(ephemeral=True)  # Отсрочка ответа

    #     if участник is None:
    #         участник = inter.author

    #     if тип_предмета not in ['звезда', 'эмблема']:
    #         await inter.edit_original_message(content="Неверный тип предмета. Используйте 'звезда' или 'эмблема'.")
    #         return

    #     # Получаем абсолютный путь к папке images
    #     item_dir = os.path.join(BASE_DIR, "images", "stars" if тип_предмета == "звезда" else "emblems")
    #     if not ос.path.exists(item_dir):
    #         await inter.edit_original_message(content=f"Папка для {тип_предмета} не найдена.")
    #         return

    #     items = [f for f in os.listdir(item_dir) if os.path.isfile(os.path.join(item_dir, f))]
    #     if not items:
    #         await inter.edit_original_message(content=f"Нет доступных {тип_предмета} для выбора.")
    #         return

    #     user = User(str(участник.id))
    #     user.load()
    #     if not user:
    #         await inter.edit_original_message(content=f"Извините, но этот пользователь ({участник.display_name}) не найден в базе данных, обратитесь к Главе сервера.")
    #         return

    #     options = [disnake.SelectOption(label=item, value=item) for item in items]
    #     select = disnake.ui.Select(placeholder="Выберите файл", options=options)

    #     async def select_callback(interaction):
    #         selected_item = select.values[0]
    #         if тип_предмета == "звезда":
    #             user.star_images = selected_item
    #         else:
    #             user.emblems = selected_item

    #         user.save()
    #         await interaction.response.send_message(f"{тип_предмета.capitalize()} '{selected_item}' успешно назначена пользователю {участник.display_name}.", ephemeral=True)
    #         select.disabled = True
    #         await interaction.edit_original_message(view=view)

    #     select.callback = select_callback
    #     view = disnake.ui.View()
    #     view.add_item(select)
    #     await inter.edit_original_message(content="Выберите файл из списка:", view=view)
    #     await self.logger.log(self.bot, inter)  # Упрощаем вызов логирования

def setup(bot):
    bot.add_cog(SetItems(bot))