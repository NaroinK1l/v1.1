import functools
import asyncio

roles_permissions = {
    "non_server_members": {
        "role_ids": [758380980217315328, 957298263684435978],  # Пример ID роли
        "user_ids": [],  # Список ID пользователей
        "permissions": {
            "user": True,
        }
    },
    "members": {
        "role_ids": [859505346246344705, 859505858795143190, 580786434601123860,
                     736595830362079273, 580785920341442571, 1295024572751417417,
                     580785634986295297, 580752849538121761, 1295024473120182292,
                     736590461686382654],  # Пример ID роли
        "user_ids": [],  # Список ID пользователей
        "permissions": {
            "RankUp": True,
            "count_exp": True,
        },
        "inherits": "non_server_members",
    },
    "advanced_members": {
        "role_ids": [1284655693592531026, 1284655644041023673, 993176597374971955,
                    1284655649598214194, 1284654927494254613, 1283675232573460502, 
                    1282650279585779733, 993176593222606878, 993176600428417025,
                    993176581801529345, 993176532338094121,993175140475080816],  # Пример ID роли
        "user_ids": [],  # Список ID пользователей
        "permissions": {
            "edit_date": True
        },
        "inherits": "members",
    },
    "administrators": {
        "role_ids": [580788199241023499,580787880398553103],  # Пример ID роли
        "user_ids": [],  # Пример ID пользователя
        "permissions": {
            "set": True,
            "edit_user": True,
        },
        "inherits": "advanced_members",
    },
    "leaders": {
        "role_ids": [1026142753169604688, 580460131859562546, 580788132211982337],  # Пример ID роли
        "user_ids": [242578640196337665],  # Список ID пользователей
        "permissions": {},
    }
}

class Permissions:

    @classmethod
    def get_role_persmisisons(cls, role_name):
        role = roles_permissions.get(role_name, {})
        permissions = role.get("permissions", {})
        inherited_permissions = {}

        # Если есть наследование, рекурсивно получаем права родительской роли
        if role.get("inherits"):
            inherited_permissions = cls.get_role_persmisisons(role.get("inherits"))

        # Объединяем текущие права с унаследованными
        combined_permissions = {**inherited_permissions, **permissions}

        # Возвращаем только те права, которые установлены в True
        return {key: value for key, value in combined_permissions.items() if value}
    
    @classmethod
    def check_permission(cls, user_role_ids, command, user_id=None):
        # Проверяем, если пользователь имеет роль "leaders"
        leaders_role_ids = roles_permissions["leaders"]["role_ids"]
        if any(role_id in user_role_ids for role_id in leaders_role_ids):
            print(f"User has leader role. Access granted to all commands.")
            return True  # Лидеры имеют доступ ко всем командам

        # Проверяем ID пользователя (приоритетная проверка)
        if user_id:
            for role_name, role_data in roles_permissions.items():
                if user_id in role_data.get("user_ids", []):
                    permissions = cls.get_role_persmisisons(role_name)
                    if command in permissions:
                        print(f"User ID {user_id} found in user_ids for role '{role_name}'. Access granted.")
                        return True

        # Обычная проверка разрешений по ролям
        for role_name, role_data in roles_permissions.items():
            if any(role_id in user_role_ids for role_id in role_data.get("role_ids", [])):
                if command in cls.get_role_persmisisons(role_name):
                    return True

        return False

    @classmethod
    async def delayed_check_permission(cls, user_role_ids, command, delay=5):
        await asyncio.sleep(delay)
        return cls.check_permission(user_role_ids, command)

    @classmethod
    def get_all_role_ids(cls):
        """Возвращает список всех ID ролей из roles_permissions."""
        all_role_ids = set()
        for role_data in roles_permissions.values():
            all_role_ids.update(role_data.get("role_ids", []))
        return all_role_ids


def permission(command):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, inter, *args, **kwargs):
            # Проверка прав пользователя
            user_role_ids = [role.id for role in inter.author.roles]
            if not Permissions().check_permission(user_role_ids, command):
                await inter.response.send_message(
                    "У вас недостаточно прав для выполнения этой команды.", ephemeral=True
                )
                return

            # Вызов оригинальной команды
            return await func(self, inter, *args, **kwargs)

        return wrapper
    return decorator
