from datetime import datetime, timedelta
from .BaseModel import BaseModel

class ArchivedUser(BaseModel):
    # Значения по умолчанию
    join_date = datetime.min
    birth_date = datetime.min
    experience = 0
    level = 1
    special_points = 0
    emblems = 'Нет данных'
    name = 'Нет данных'
    archived_at = datetime.now()
    roles = []  # Поле для хранения остальных ролей в виде списка
    rang = None  # Поле для хранения единственной роли Rang
    collection_name = 'archived_users'  # фиксированное имя коллекции

    def set_birth_date(self, birth_date):
        if isinstance(birth_date, str):
            self.birth_date = datetime.strptime(birth_date, '%d.%m.%Y')
        else:
            self.birth_date = birth_date

    def set_join_date(self, join_date):
        if isinstance(join_date, str):
            self.join_date = datetime.strptime(join_date, '%d.%m.%Y')
        else:
            self.join_date = join_date

    def set_roles(self, roles):
        """Устанавливает роли, которые не являются рангами."""
        self.roles = [str(role_id) for role_id in roles]

    def set_rang(self, role_id):
        """Устанавливает единственную роль Rang для архивированного пользователя."""
        self.rang = str(role_id)

    def save(self):
        """Сохраняет пользователя в архив."""
        self.archived_at = datetime.now().strftime('%d.%m.%Y')
        if isinstance(self.join_date, datetime):
            self.join_date = self.join_date.strftime('%d.%m.%Y')
        if isinstance(self.birth_date, datetime):
            self.birth_date = self.birth_date.strftime('%d.%m.%Y')
        super().save()

    def load(self):
        """Загружает пользователя из архива."""
        super().load()

        if isinstance(self.archived_at, str):
            try:
                self.archived_at = datetime.strptime(self.archived_at, '%d.%m.%Y')
            except Exception:
                self.archived_at = datetime.min

        if isinstance(self.join_date, str):
            try:
                self.join_date = datetime.strptime(self.join_date, '%d.%m.%Y')
            except Exception:
                self.join_date = datetime.min

        if isinstance(self.birth_date, str):
            try:
                self.birth_date = datetime.strptime(self.birth_date, '%d.%m.%Y')
            except Exception:
                self.birth_date = datetime.min

        # Если roles сохранены как строка, преобразуем их в список
        if isinstance(self.roles, str):
            self.roles = [role_id.strip() for role_id in self.roles.split(',') if role_id.strip().isdigit()]

    @classmethod
    def get_user_by_id(cls, user_id):
        from services.firebase import get_document
        data = get_document(cls.collection_name, user_id)
        if data:
            user = cls(user_id)
            user.load()
            return user
        return None

    @classmethod
    def cleanup_old_archived_users(cls):
        """Удаляет пользователей из архива, если они старше 2 лет."""
        from services.firebase import delete_document, get_document
        all_ids = cls.get_all_document_ids()
        for doc_id in all_ids:
            data = get_document(cls.collection_name, doc_id)
            if data and 'archived_at' in data:
                try:
                    archived_at = datetime.strptime(data['archived_at'], '%d.%m.%Y')
                except ValueError:
                    continue
                if datetime.now() - archived_at > timedelta(days=730):
                    delete_document(cls.collection_name, doc_id)

    def delete(self):
        """Удаляет пользователя из архива."""
        from services.firebase import delete_document
        delete_document(self.collection_name, self.document_id)