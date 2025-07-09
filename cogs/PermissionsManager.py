import json
from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from cogs.base_cog import BaseCog
from services.config import GUILD_ID

# Путь к JSON-файлу
ROLES_PERMISSIONS_FILE = "d:\\1App\\EUiSBot\\v1.1\\systems\\roles_permissions.json"

def load_roles_permissions():
    with open(ROLES_PERMISSIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_roles_permissions(data):
    """Сохраняет данные в roles_permissions.json."""
    with open(ROLES_PERMISSIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

roles_permissions = load_roles_permissions()  # Загрузите данные один раз при инициализации

class PermissionsManager(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        print("[DEBUG] PermissionsManager инициализирован")

    @commands.slash_command(
        name="pm_group",
        description="Управление категориями и правами",
        guild_ids=[GUILD_ID]
    )
    async def pm_group(self, inter: ApplicationCommandInteraction):
        pass

    @pm_group.sub_command(
        name="add",
        description="Добавить новую категорию"
    )
    async def add_category(
        self,
        inter: ApplicationCommandInteraction,
        category: str = commands.Param(description="Название новой категории"),
        parent_category: str = commands.Param(
            description="Родительская категория (опционально)",
            default=None,
            choices=list(roles_permissions.keys())  # Передаем готовый список
        )
    ):
        if category in roles_permissions:
            await inter.response.send_message(f"Категория `{category}` уже существует.", ephemeral=True)
            return

        roles_permissions[category] = {"role_ids": [], "user_ids": [], "permissions": {}}
        if parent_category:
            if parent_category not in roles_permissions:
                await inter.response.send_message(f"Родительская категория `{parent_category}` не существует.", ephemeral=True)
                return
            roles_permissions[category]["inherits"] = parent_category

        save_roles_permissions(roles_permissions)
        await inter.response.send_message(f"Категория `{category}` добавлена.")

    @pm_group.sub_command(
        name="edit",
        description="Редактировать существующую категорию"
    )
    async def edit_category(
        self,
        inter: ApplicationCommandInteraction,
        category: str = commands.Param(choices=list(roles_permissions.keys())),
        action: str = commands.Param(choices=["add_group", "remove_group", "add_user", "remove_user", "add_perm", "remove_perm"]),
        target: str = commands.Param(
            description="ID роли, пользователя или название права",
            autocomplete=True
        )
    ):
        async def autocomplete_target(inter, user_input):
            print(f"[DEBUG] Autocomplete called with user_input: {user_input}")
            guild = inter.guild  # Получаем текущий сервер
            if not guild:
                return []

            if action in ["add_group", "remove_group"]:
                # Возвращаем список ролей на сервере
                result = [
                    role.name for role in guild.roles
                    if user_input.lower() in role.name.lower()
                ][:25]  # Ограничиваем до 25 результатов
            elif action in ["add_user", "remove_user"]:
                # Возвращаем список пользователей на сервере
                result = [
                    member.display_name for member in guild.members
                    if user_input.lower() in member.display_name.lower()
                ][:25]  # Ограничиваем до 25 результатов
            elif action in ["add_perm", "remove_perm"]:
                permissions = roles_permissions.get(category, {}).get("permissions", {})
                result = list(permissions.keys()) if isinstance(permissions, dict) else []
            else:
                result = []
            print(f"[DEBUG] Autocomplete result: {result}")
            return result

        roles_permissions = load_roles_permissions()

        if category not in roles_permissions:
            await inter.response.send_message(f"Категория `{category}` не существует.", ephemeral=True)
            return

        if action in ["add_group", "remove_group"]:
            role_id = int(target)
            if action == "add_group":
                if role_id in roles_permissions[category]["role_ids"]:
                    await inter.response.send_message(f"Роль `{role_id}` уже добавлена в категорию `{category}`.", ephemeral=True)
                    return
                roles_permissions[category]["role_ids"].append(role_id)
                await inter.response.send_message(f"Роль `{role_id}` добавлена в категорию `{category}`.")
            else:
                if role_id not in roles_permissions[category]["role_ids"]:
                    await inter.response.send_message(f"Роль `{role_id}` отсутствует в категории `{category}`.", ephemeral=True)
                    return
                roles_permissions[category]["role_ids"].remove(role_id)
                await inter.response.send_message(f"Роль `{role_id}` удалена из категории `{category}`.")

        elif action in ["add_user", "remove_user"]:
            user_id = int(target)
            if action == "add_user":
                if user_id in roles_permissions[category]["user_ids"]:
                    await inter.response.send_message(f"Пользователь `{user_id}` уже добавлен в категорию `{category}`.", ephemeral=True)
                    return
                roles_permissions[category]["user_ids"].append(user_id)
                await inter.response.send_message(f"Пользователь `{user_id}` добавлен в категорию `{category}`.")
            else:
                if user_id not in roles_permissions[category]["user_ids"]:
                    await inter.response.send_message(f"Пользователь `{user_id}` отсутствует в категории `{category}`.", ephemeral=True)
                    return
                roles_permissions[category]["user_ids"].remove(user_id)
                await inter.response.send_message(f"Пользователь `{user_id}` удален из категории `{category}`.")

        elif action in ["add_perm", "remove_perm"]:
            permission = target
            if action == "add_perm":
                if permission in roles_permissions[category]["permissions"]:
                    await inter.response.send_message(f"Право `{permission}` уже существует в категории `{category}`.", ephemeral=True)
                    return
                roles_permissions[category]["permissions"][permission] = True
                await inter.response.send_message(f"Право `{permission}` добавлено в категорию `{category}`.")
            else:
                if permission not in roles_permissions[category]["permissions"]:
                    await inter.response.send_message(f"Право `{permission}` отсутствует в категории `{category}`.", ephemeral=True)
                    return
                del roles_permissions[category]["permissions"][permission]
                await inter.response.send_message(f"Право `{permission}` удалено из категории `{category}`.")

        save_roles_permissions(roles_permissions)

def setup(bot):
    bot.add_cog(PermissionsManager(bot))