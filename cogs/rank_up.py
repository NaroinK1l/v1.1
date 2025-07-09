import disnake
from disnake.ext import commands
from cogs.base_cog import BaseCog
from systems.perms import permission 
from models.User import User  # Импортируем модель User
from systems.Logger import Logger  # Импортируем Logger
from services.config import GUILD_ID, RANK_UP_ANNOUNCEMENT_CHANNEL_ID

RANKS = {
    'Неизвестный': {"rank_id": 1295024473120182292, "price": 800, "required_rank": 736590461686382654, "name": "Неизвестный"},
    'Бродяга': {"rank_id": 580752849538121761, "price": 1100, "required_rank": 1295024473120182292, "name": "Бродяга"},
    'Молодой': {"rank_id": 580785634986295297, "price": 1700, "required_rank": 580752849538121761, "name": "Молодой"},
    'Опытний': {"rank_id": 1295024572751417417, "price": 2300, "required_rank": 580785634986295297, "name": "Опытний"},
    'Закаленный': {"rank_id": 580785920341442571, "price": 3000, "required_rank": 580785634986295297, "name": "Закаленный"},
    'Проверенный': {"rank_id": 736595830362079273, "price": 3800, "required_rank": 580785920341442571, "name": "Проверенный"},
    'Мастер': {"rank_id": 580786434601123860, "price": 4700, "required_rank": 736595830362079273, "name": "Мастер"},
    'Высший': {"rank_id": 859505346246344705, "price": 5600, "required_rank": 580786434601123860, "name": "Высший"},
    'Великий': {"rank_id": 859505858795143190, "price": 6500, "required_rank": 859505346246344705, "name": "Великий"},
    'Древний': {"rank_id": 993176597374971955, "price": 7000, "required_rank": 859505858795143190, "name": "Древний"},
    '1 тыс': {"rank_id": 993175140475080816, "price": 1000, "required_rank": 993176597374971955, "name": "Древний 1 тыс"},
    '2 тыс': {"rank_id": 993176532338094121, "price": 2000, "required_rank": 993175140475080816, "name": "Древний 2 тыс"},
    '3 тыс': {"rank_id": 993176581801529345, "price": 3000, "required_rank": 993176532338094121, "name": "Древний 3 тыс"},
    '4 тыс': {"rank_id": 993176600428417025, "price": 4000, "required_rank": 993176581801529345, "name": "Древний 4 тыс"},
    '5 тыс': {"rank_id": 993176593222606878, "price": 5000, "required_rank": 993176600428417025, "name": "Древний 5 тыс"},
    '6 тыс': {"rank_id": 1282650279585779733, "price": 6000, "required_rank": 993176593222606878, "name": "Древний 6 тыс"},
    '7 тыс': {"rank_id": 1283675232573460502, "price": 7000, "required_rank": 1282650279585779733, "name": "Древний 7 тыс"},
    '8 тыс': {"rank_id": 1284654927494254613, "price": 8000, "required_rank": 1283675232573460502, "name": "Древний 8 тыс"},
    '9 тыс': {"rank_id": 1284655649598214194, "price": 9000, "required_rank": 1284654927494254613, "name": "Древний 9 тыс"},
    '10 тыс': {"rank_id": 1284655644041023673, "price": 10000, "required_rank": 1284655649598214194, "name": "Древний 10 тыс"},
    '11 тыс': {"rank_id": 1284655693592531026, "price": 11000, "required_rank": 1284655644041023673, "name": "Древний 11 тыс"},
}

class RankUp(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.logger = Logger()  # Инициализируем Logger
        print("[DEBUG] RankUp ког инициализирован")  # Отладочное сообщение

    @commands.slash_command(name='rank_up', description='Повысить свой ранг', guild_ids=[GUILD_ID])
    @permission("RankUp")
    async def next_rang(self, inter: disnake.ApplicationCommandInteraction):
        print("[DEBUG] Команда 'rank_up' вызвана")  # Отладочное сообщение
        member = inter.author  # Получаем объект участника
        current_rank_id = None

        # Определяем текущий ранг пользователя по его ролям
        for role in member.roles:
            for rank in RANKS.values():
                if role.id == rank["rank_id"]:
                    current_rank_id = rank["rank_id"]
                    break
            if current_rank_id:
                break

        if current_rank_id is None:
            print("[DEBUG] Текущий ранг пользователя не найден")  # Отладочное сообщение
            await inter.response.send_message("Ваш текущий ранг не найден. Обратитесь к администрации.", ephemeral=True)
            return

        # Находим следующий ранг
        next_rank = None
        for rank in RANKS.values():
            if rank["required_rank"] == current_rank_id:
                next_rank = rank
                break

        if not next_rank:
            print("[DEBUG] Пользователь уже достиг максимального ранга")  # Отладочное сообщение
            await inter.response.send_message("Вы уже достигли максимального ранга.", ephemeral=True)
            return

        # Проверяем спец баллы
        user = User(str(member.id))
        user.load()
        if user.special_points < next_rank["price"]:
            print(f"[DEBUG] Недостаточно спец баллов: {user.special_points} / {next_rank['price']}")  # Отладочное сообщение
            await inter.response.send_message(
                f"Для повышения до ранга '{next_rank['name']}' требуется {next_rank['price']} спец баллов. У вас только {user.special_points}.",
                ephemeral=True
            )
            return

        # Удаляем текущий ранг и добавляем новый
        current_role = inter.guild.get_role(current_rank_id)
        next_role = inter.guild.get_role(next_rank["rank_id"])

        print(f"[DEBUG] Повышение ранга: {current_role} -> {next_role}")  # Отладочное сообщение
        await inter.author.add_roles(next_role, reason="Повышение ранга")
        await inter.author.remove_roles(current_role, reason="Повышение ранга")
        
        # Отправляем сообщение в канал анонсов
        announcement_channel = inter.guild.get_channel(RANK_UP_ANNOUNCEMENT_CHANNEL_ID)
        if announcement_channel:
            await announcement_channel.send(
                f"{member.mention} поздравляем, теперь у тебя ранг {next_role.mention}!"
            )

        # Обновляем спец баллы
        user.special_points -= next_rank["price"]
        user.save()

        await inter.response.send_message(
            f"Поздравляем! Вы повысили свой ранг до '{next_rank['name']}'. Осталось спец баллов: {user.special_points}.",
            ephemeral=True
        )
        await self.logger.log(self.bot, inter, f"Пользователь повысил ранг до '{next_rank['name']}'.")

def setup(bot):
    bot.add_cog(RankUp(bot))
