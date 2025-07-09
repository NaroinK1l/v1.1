import asyncio
import time
from datetime import datetime
from disnake.ext import commands
from services.config import GUILD_ID
from systems.perms import Permissions
from models.User import User
from models.ArchivedUser import ArchivedUser
from systems.Logger import Logger  # Импортируем Logger

restored_users = {}  # Словарь для отслеживания недавно восстановленных пользователей
is_restoring_users = False  # Флаг для отслеживания процесса восстановления

# Словарь для индивидуальных блокировок пользователей
user_locks = {}

def get_user_lock(user_id):
    """Получить или создать Lock для конкретного пользователя."""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

async def check_and_update_users(bot):
    global is_restoring_users

    if is_restoring_users:
        print("[INFO] Пропускаем проверку пользователей, так как идет процесс восстановления.")
        return

    guild = bot.get_guild(int(GUILD_ID))
    if not guild:
        print("[ERROR] Гильдия не найдена.")
        return

    role_ids = Permissions.get_all_role_ids()  # Список ID ролей, которые считаются рангами
    existing_users = User.get_all_document_ids()

    print(f"[INFO] Начинаем проверку пользователей в гильдии: {guild.name} ({guild.id})")

    for member in guild.members:
        user_id = str(member.id)

        # Получаем роли пользователя, которые являются рангами
        member_roles = {role.id for role in member.roles}
        rang_roles = member_roles & role_ids  # Роли, которые являются рангами

        if len(rang_roles) > 1:
            print(f"[WARNING] У пользователя {member.display_name} (ID: {user_id}) несколько рангов. Это конфликт!")
            continue  # Пропускаем обработку, если конфликт ролей

        if rang_roles:  # Пользователь имеет ровно одну роль-ранг
            rang_role_id = list(rang_roles)[0]  # Берем единственный найденный ранг
            if user_id in existing_users:
                # Пользователь уже есть в базе, проверяем и обновляем данные
                user = User.get_user_by_id(user_id)
                if user:
                    if user.rang != str(rang_role_id):
                        user.set_rang(str(rang_role_id))  # Обновляем ранг
                        print(f"[INFO] Обновлен ранг пользователя {member.display_name} (ID: {user_id}).")
                    if user.name != member.display_name:
                        user.name = member.display_name  # Обновляем ник
                        print(f"[INFO] Обновлен ник пользователя {member.display_name} (ID: {user_id}).")
                    user.save()
            else:
                # Пользователя нет в базе, проверяем архив
                archived_user = ArchivedUser.get_user_by_id(user_id)
                if archived_user:
                    await restore_user(member)  # Восстанавливаем пользователя
                else:
                    # Создаем нового пользователя
                    new_user = User(user_id)
                    new_user.name = member.display_name or member.name
                    new_user.set_join_date(member.joined_at)
                    new_user.set_rang(str(rang_role_id))  # Устанавливаем ранг
                    new_user.save()
                    print(f"[INFO] Создан новый пользователь: {new_user.name} (ID: {user_id}) с рангом {rang_role_id}.")
        else:
            if user_id in existing_users:
                await archive_user(member)  # Архивируем пользователя

    print("[INFO] Проверка пользователей завершена.")

async def archive_user(member):
    user_lock = get_user_lock(member.id)  # Получаем Lock для конкретного пользователя
    async with user_lock:  # Блокируем операции для этого пользователя
        # Проверяем, не был ли пользователь недавно восстановлен
        if member.id in restored_users and time.time() - restored_users[member.id] < 15:
            print(f"[INFO] Пропускаем архивацию для пользователя {member.display_name} ({member.id}) из-за недавнего восстановления.")
            return

        user = User.get_user_by_id(str(member.id))
        if not user:
            print(f"[INFO] Пользователь {member.id} не найден в базе. Архивация не требуется.")
            return

        archived_user = ArchivedUser(document_id=str(member.id))
        archived_user.name = member.display_name or member.name
        archived_user.level = user.level
        archived_user.special_points = user.special_points
        archived_user.emblems = user.emblems
        archived_user.set_join_date(user.join_date)
        archived_user.set_birth_date(user.birth_date)
        archived_user.set_rang(user.rang)  # Сохраняем Rang

        other_roles = [role.id for role in member.roles if role.id not in Permissions.get_all_role_ids()]
        archived_user.set_roles(other_roles)  # Сохраняем роли как список

        archived_user.save()
        user.delete()

        # Логируем архивацию
        await Logger.log_archive(member.guild._state._get_client(), member.id, member.display_name)

async def restore_user(member):
    user_lock = get_user_lock(member.id)  # Получаем Lock для конкретного пользователя
    async with user_lock:  # Блокируем операции для этого пользователя
        global is_restoring_users
        global restored_users
        is_restoring_users = True  # Устанавливаем флаг

        try:
            archived_user = ArchivedUser(document_id=str(member.id))
            archived_user.load()
            if archived_user.name != 'Нет данных':
                user = User(document_id=str(member.id))
                user.name = member.display_name or member.name
                user.level = archived_user.level
                user.special_points = archived_user.special_points
                user.emblems = archived_user.emblems
                user.set_join_date(archived_user.join_date)
                user.set_birth_date(archived_user.birth_date)  # Восстанавливаем дату рождения
                user.set_rang(archived_user.rang)  # Восстанавливаем Rang
                user.save()

                guild = member.guild
                current_roles = {role.id for role in member.roles}
                archived_roles = {int(role_id) for role_id in archived_user.roles}

                # Удаляем роли, которые не соответствуют архивным данным
                roles_to_remove = [
                    role for role in member.roles
                    if role.id not in archived_roles and str(role.id) != archived_user.rang
                ]
                for role in roles_to_remove:
                    await member.remove_roles(role, reason="Removing invalid roles during restoration")
                    print(f"[INFO] Роль {role.name} удалена у пользователя {member.display_name}, так как она не соответствует архивным данным.")

                # Сначала восстанавливаем ранг
                if archived_user.rang and int(archived_user.rang) not in current_roles:
                    rang_role = guild.get_role(int(archived_user.rang))
                    if rang_role:
                        await member.add_roles(rang_role, reason="Restoring Rang role from archive")
                        print(f"[INFO] Ранг {rang_role.name} восстановлен для пользователя {member.display_name}.")

                # Затем восстанавливаем остальные роли
                roles_to_add = [
                    guild.get_role(role_id)
                    for role_id in archived_roles
                    if role_id not in current_roles and guild.get_role(role_id) and str(role_id) != archived_user.rang
                ]
                for role in roles_to_add:
                    await member.add_roles(role, reason="Restoring roles from archive")
                    print(f"[INFO] Роль {role.name} восстановлена для пользователя {member.display_name}.")

                # Удаляем архивные данные
                archived_user.delete()

                # Логируем восстановление
                await Logger.log_restore(member.guild._state._get_client(), member.id, member.display_name)

                # Добавляем пользователя в список недавно восстановленных
                restored_users[member.id] = time.time()
                print(f"[INFO] Пользователь {member.display_name} (ID: {member.id}) восстановлен.")
        finally:
            is_restoring_users = False  # Сбрасываем флаг

async def handle_role_update(bot, before, after):
    global is_restoring_users

    # Если идет процесс восстановления, игнорируем изменения ролей
    if is_restoring_users:
        print(f"[INFO] Игнорируем изменения ролей для пользователя {after.display_name} ({after.id}) из-за восстановления.")
        return

    role_ids_before = {role.id for role in before.roles}
    role_ids_after = {role.id for role in after.roles}

    added_roles = role_ids_after - role_ids_before
    removed_roles = role_ids_before - role_ids_after

    user_id = str(after.id)

    # Проверяем таймер восстановления
    if after.id in restored_users and time.time() - restored_users[after.id] < 15:
        print(f"[INFO] Игнорируем изменения ролей для пользователя {after.display_name} ({after.id}) из-за таймера.")
        return

    # Если добавлены роли из списка рангов, восстанавливаем пользователя
    if any(role_id in Permissions.get_all_role_ids() for role_id in added_roles):
        archived_user = ArchivedUser(document_id=user_id)
        archived_user.load()
        if archived_user.name != 'Нет данных':
            print(f"[Auto-Restore] Восстанавливаем пользователя {after.display_name}.")
            await restore_user(after)
    # Если все ранговые роли удалены, проверяем задержку перед архивацией
    elif not any(role_id in Permissions.get_all_role_ids() for role_id in role_ids_after):
        await asyncio.sleep(7)  # Задержка перед архивацией
        # Проверяем, не добавился ли ранг за время ожидания
        member = after.guild.get_member(after.id)
        current_roles = {role.id for role in member.roles}
        if not any(role_id in Permissions.get_all_role_ids() for role_id in current_roles):
            await archive_user(after)
        else:
            print(f"[INFO] Пользователь {after.display_name} ({after.id}) получил ранг во время задержки. Архивация отменена.")

async def update_user_data(before, after):
    """Обновляет данные пользователя (ник и ранг) в базе данных."""
    user_id = str(after.id)
    user = User.get_user_by_id(user_id)

    if not user:
        print(f"[INFO] Пользователь {after.display_name} (ID: {user_id}) не найден в базе данных.")
        return

    # Проверяем изменение ника
    if before.nick != after.nick:
        user.name = after.nick or after.name  # Если ник отсутствует, используем имя
        print(f"[INFO] Ник пользователя {before.display_name} изменен на {after.display_name} в базе данных.")

    # Проверяем изменение ранга
    before_roles = {role.id for role in before.roles}
    after_roles = {role.id for role in after.roles}
    rank_roles = Permissions.get_all_role_ids()  # Получаем список всех ролей, которые считаются рангами

    before_rank = list(before_roles & rank_roles)
    after_rank = list(after_roles & rank_roles)

    if before_rank != after_rank:
        if len(after_rank) == 1:  # Если у пользователя есть ровно один ранг
            user.set_rang(str(after_rank[0]))  # Обновляем ранг в базе данных
            print(f"[INFO] Ранг пользователя {after.display_name} обновлен в базе данных.")
        elif len(after_rank) > 1:
            print(f"[WARNING] У пользователя {after.display_name} конфликт рангов. В базе данных изменения не применены.")
        else:
            user.set_rang(None)  # Удаляем ранг, если он отсутствует
            print(f"[INFO] Ранг пользователя {after.display_name} удален из базы данных.")

    user.save()

__all__ = ["check_and_update_users", "archive_user", "restore_user", "handle_role_update", "update_user_data"]
