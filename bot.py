from disnake.ext import commands, tasks
from services.config import DISCORD_TOKEN, GUILD_ID, bot, CHANNELS_WITHOUT_EXP, NEW_USER_CHANNEL_ID, ADMIN_ID, NEW_USER_ROLE_ID
from systems.perms import roles_permissions, Permissions
from models.User import User
from models.ArchivedUser import ArchivedUser
import disnake
import asyncio
from datetime import datetime, timedelta
from asyncio import sleep
from systems.user_manager import check_and_update_users, archive_user, handle_role_update, restore_user, update_user_data

voice_channel_times = {}

async def reset_levels_and_experience():
    """Сбрасывает уровни и опыт только для пользователей, которые есть в базе данных или архиве."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("[ERROR] Гильдия не найдена.")
        return

    low_level_users = []
    existing_users = User.get_all_document_ids()  # Получаем всех пользователей из базы данных
    archived_users = ArchivedUser.get_all_document_ids()  # Получаем всех пользователей из архива

    for member in guild.members:
        if member.bot:
            continue

        user_id = str(member.id)
        if user_id not in existing_users:
            continue  # Пропускаем пользователей, которых нет в базе данных

        user = User.get_user_by_id(user_id)
        if user and user.level < 15:
            low_level_users.append(member)

    admin = guild.get_member(ADMIN_ID)
    if admin and low_level_users:
        embed = disnake.Embed(
            title="Список участников с уровнем ниже 15",
            description="\n".join([f"{member.display_name} (ID: {member.id})" for member in low_level_users]),
            color=disnake.Color.orange()
        )
        await admin.send(embed=embed)  # Отправляем список без реакций

    # Сбрасываем уровни и опыт только для пользователей в базе данных
    for user_id in existing_users:
        user = User.get_user_by_id(user_id)
        if user:
            user.level = 1
            user.experience = 0
            user.save()

    # Сбрасываем уровни и опыт в архиве
    for user_id in archived_users:
        archived_user = ArchivedUser(document_id=user_id)
        archived_user.load()
        archived_user.level = 1
        archived_user.special_points = 0
        archived_user.save()

@bot.event
async def on_ready():    
    GUILD = bot.get_guild(GUILD_ID)
    print(f"Logged in as {bot.user}")
    base_cog = bot.get_cog('BaseCog')
    if base_cog:
        await base_cog.sync_commands()
    await bot.change_presence(status=disnake.Status.dnd, activity=disnake.Game("V1.0"))
    if not award_voice_experience.is_running():
        award_voice_experience.start()        
    ArchivedUser.cleanup_old_archived_users()
    await check_and_update_users(bot)
    if not reset_levels_task.is_running():
        reset_levels_task.start()

    # Проверяем, если бот был запущен позже 1 числа
    now = datetime.now()
    if now.day > 1:
        admin = bot.get_user(ADMIN_ID)
        if admin:
            message = await admin.send(
                "Бот был запущен позже 1 числа. Выполнить сброс уровней и опыта?",
            )
            await message.add_reaction("✅")  # Реакция для выполнения сброса
            await message.add_reaction("❌")  # Реакция для отмены

            def check(reaction, user):
                return user.id == ADMIN_ID and str(reaction.emoji) in ["✅", "❌"]

            try:
                reaction, _ = await bot.wait_for("reaction_add", timeout=86400, check=check)
                if str(reaction.emoji) == "✅":
                    await reset_levels_and_experience()  # Вызываем функцию сброса
                elif str(reaction.emoji) == "❌":
                    print("[INFO] Сброс уровней отменен.")
            except asyncio.TimeoutError:
                print("[INFO] Время ожидания реакции истекло.")

@bot.event
async def on_member_update(before, after):
    """Обрабатывает изменения пользователя, такие как роли или ник."""
    # Проверяем изменение ролей
    await handle_role_update(bot, before, after)

    # Обновляем данные пользователя (ник и ранг)
    await update_user_data(before, after)

@bot.event
async def on_member_remove(member):
    """Обрабатывает событие выхода пользователя из сервера."""
    await archive_user(member)  # Убираем лишний аргумент bot

@bot.event
async def on_member_kick(guild, member):
    """Обрабатывает событие кика пользователя с сервера."""
    await archive_user(member)  # Убираем лишний аргумент bot

@bot.event
async def on_message(message): 
    if message.author == bot.user or message.channel.id in CHANNELS_WITHOUT_EXP:
        return

    user = User.get_user_by_id(str(message.author.id))
    if not user:
        return

    role_ids = [role.id for role in message.author.roles]
    if Permissions.check_permission(role_ids, "count_exp"):
        word_count = len(message.content.split())
        user.add_experience(15 * word_count)
        user.save()

    await bot.process_commands(message)

@tasks.loop(seconds=60)
async def award_voice_experience():
    # Пауза перед первым запуском
    if not hasattr(award_voice_experience, "_initialized"):
        await asyncio.sleep(5)  # Задержка в 10 секунд
        award_voice_experience._initialized = True
        print("[SYSTEM] Начисление опыта началось.")
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    for voice_channel in guild.voice_channels:
        for member in voice_channel.members:
            if member.bot or voice_channel.id in CHANNELS_WITHOUT_EXP:
                continue

            role_ids = [role.id for role in member.roles]
            if not Permissions.check_permission(role_ids, "count_exp"):
                continue    

            user = User.get_user_by_id(str(member.id))
            if not user:
                continue

            user.add_experience(8)
            user.save()

            # Проверка на конфликтующие роли
            conflicting_roles = [role_id for role_id in role_ids if role_id in Permissions.get_all_role_ids()]
            if len(conflicting_roles) > 1:
                admin = guild.get_member(ADMIN_ID)
                if admin:
                    await asyncio.sleep(10)  # Задержка перед отправкой сообщения
                    await admin.send(f"У пользователя {member.display_name} обнаружены конфликтующие роли.")

@tasks.loop(hours=24)
async def reset_levels_task():
    """Задача для сброса уровней и опыта 1 числа каждого месяца."""
    now = datetime.now()
    if now.day == 1:
        await reset_levels_and_experience()

bot.run(DISCORD_TOKEN)