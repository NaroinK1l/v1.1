import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
import asyncio
from services.config import BIRTH_CHANNEL_ID
from services.FirestoreQueryBuilder import FirestoreQueryBuilder

class BirthdayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.check_birthdays_daily())  # Запускаем задачу при инициализации

    async def check_birthdays_daily(self):
        await self.bot.wait_until_ready()  # Ждем, пока бот полностью загрузится
        while True:
            now = datetime.now()
            target_time = now.replace(hour=13, minute=0, second=0, microsecond=0)

            # Если текущее время уже после 13:00, выполняем проверку сразу
            if now >= target_time:
                print("Бот запущен после 13:00. Выполняем проверку дней рождения за сегодня.")
                await self.check_birthdays()
                # Устанавливаем время следующего запуска на 13:00 следующего дня
                target_time += timedelta(days=1)

            # Рассчитываем время ожидания до 13:00
            wait_time = (target_time - datetime.now()).total_seconds()
            print(f"Ждем до 13:00. Ожидание: {wait_time // 3600} часов и {(wait_time % 3600) // 60} минут.")
            await asyncio.sleep(wait_time)

            # Выполняем проверку дней рождения
            await self.check_birthdays()

    async def check_birthdays(self):
        today = datetime.now().date()
        today_str = today.strftime("%d.%m")  # Формируем строку текущей даты в формате "дд.мм"

        birth_channel = self.bot.get_channel(BIRTH_CHANNEL_ID)

        if not birth_channel:
            print(f"Канал с ID {BIRTH_CHANNEL_ID} не найден.")
            return

        # Инициализируем QueryBuilder для коллекции "users"
        query_builder = FirestoreQueryBuilder("users")
        try:
            users_with_birthday = query_builder.like("birth_date", today_str).execute()
        except Exception as e:
            print(f"Ошибка при выполнении запроса Firestore: {e}")
            return

        print(f"Найдено {len(users_with_birthday)} пользователей с днем рождения.")

        for user_id, user_data in users_with_birthday.items():
            username = user_data.get("username", "Неизвестный пользователь")
            birth_date_str = user_data.get("birth_date")  # Получаем дату рождения как строку

            if not birth_date_str or len(birth_date_str.split(".")) != 3:
                print(f"Неверный формат даты рождения для пользователя {username}: {birth_date_str}")
                continue

            try:
                # Извлекаем год рождения из строки
                birth_year = int(birth_date_str.split(".")[2])  # Предполагается формат "дд.мм.гггг"
                age = today.year - birth_year

                # Учитываем, был ли уже день рождения в этом году
                birth_month, birth_day = map(int, birth_date_str.split(".")[:2])
                if (today.month, today.day) < (birth_month, birth_day):
                    age -= 1
            except (ValueError, IndexError):
                print(f"Ошибка обработки даты рождения для пользователя {username}: {birth_date_str}")
                continue

            # Отправляем поздравление в канал
            await birth_channel.send(
                f"Сегодня у <@{user_id}> день рождения. Давай его поздравим, ведь ему уже {age}!"
            )
            await asyncio.sleep(1)  # Задержка для предотвращения rate limit

def setup(bot):
    bot.add_cog(BirthdayCog(bot))