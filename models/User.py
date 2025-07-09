from datetime import datetime, timedelta
from .BaseModel import BaseModel

class User(BaseModel):
    join_date = datetime.min
    birth_date = datetime.min
    experience = 0
    level = 1
    special_points = 0
    emblems = 'Нет данных'
    name = 'Нет данных'
    rang = None  # Поле для хранения единственной роли Rang

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

    def ensure_join_date(self, discord_join_date):
        if not self.join_date or self.join_date == datetime.min:
            self.set_join_date(discord_join_date)

    def add_experience(self, amount):
        self.experience += amount
        level_up_threshold = 1200
        while self.experience >= level_up_threshold:
            self.experience -= level_up_threshold
            self.level += 1
            self.special_points += 50

    def set_rang(self, role_id):
        """Устанавливает единственную роль Rang для пользователя."""
        self.rang = str(role_id)

    def has_rang(self, role_id):
        """Проверяет, соответствует ли роль Rang указанной."""
        return self.rang == str(role_id)

    @property
    def star_images(self):
        if not self.join_date or self.join_date == datetime.min:
            return "Нет данных"
        years_on_server = (datetime.now().date() - self.join_date.date()).days // 365
        return str(min(years_on_server, 13)) + '.png'

    def delete(self):
        from services.firebase import delete_document
        delete_document(self.collection_name, self.document_id)
        
    @classmethod
    def get_user_by_id(cls, user_id):
        user = cls(user_id)
        user.load()
        if user.name == "Нет данных":  # Признак пустого пользователя
            return None
        return user

    @classmethod
    def get_all_document_ids(cls):
        from services.firebase import get_all_document_ids
        return get_all_document_ids(cls.__name__.lower() + 's')