from services.firebase import get_document, set_document, get_all_document_ids
from datetime import datetime

class BaseModel:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.collection_name = self.__class__.__name__.lower() + 's'

    def load(self):
        """Загружает данные объекта из базы данных."""
        data = get_document(self.collection_name, self.document_id)
        if data:
            # print(f"[DEBUG] Загружены данные для {self.document_id}: {data}")
            for key, value in data.items():
                if hasattr(type(self), key) and isinstance(getattr(type(self), key), property) and not getattr(type(self), key).fset:
                    continue  # Пропускаем свойства без сеттера

                # Автоматическая конвертация дат
                if key in ['join_date', 'birth_date', 'archived_at'] and isinstance(value, str):
                    try:
                        value = datetime.strptime(value, '%d.%m.%Y')
                    except ValueError:
                        value = datetime.min

                setattr(self, key, value)
        else:
            print(f"[WARNING] Данные для {self.document_id} не найдены в коллекции {self.collection_name}.")

    def save(self):
        """Сохраняет объект в базу данных."""
        self.document_id = str(self.document_id)  # Убедимся, что document_id строка
        data = self.to_dict()
        try:
            # print(f"[DEBUG] Сохраняем данные для {self.document_id}: {data}")
            set_document(self.collection_name, self.document_id, data)
        except Exception as e:
            print(f"[BaseModel] Ошибка при сохранении документа {self.document_id}: {e}")

    def delete(self):
        """Удаляет текущий объект из коллекции."""
        from services.firebase import delete_document
        delete_document(self.collection_name, self.document_id)

    @classmethod
    def get_all_document_ids(cls):
        """Получает все document_id из коллекции."""
        return get_all_document_ids(cls.__name__.lower() + 's')

    def to_dict(self):
        """Преобразует объект в словарь для сохранения."""
        data = {}
        for attr in self.__class__.__dict__:
            if not callable(getattr(self, attr, None)) and not attr.startswith("__"):
                value = getattr(self, attr)
                if isinstance(value, datetime):
                    value = value.strftime('%d.%m.%Y')
                data[attr] = value
        return data