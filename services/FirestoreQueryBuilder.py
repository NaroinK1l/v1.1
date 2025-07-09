from firebase_admin import firestore

db = firestore.client()

class FirestoreQueryBuilder:
    def __init__(self, collection_name):
        """
        Инициализация QueryBuilder для указанной коллекции.
        :param collection_name: Имя коллекции Firestore.
        """
        self.collection_ref = db.collection(collection_name)
        self.query = self.collection_ref

    def where(self, field_name, operator, value):
        """
        Добавляет условие фильтрации к запросу.
        :param field_name: Имя поля для фильтрации.
        :param operator: Оператор сравнения (например, "==", ">", "<").
        :param value: Значение для фильтрации.
        :return: self (для цепочки вызовов).
        """
        self.query = self.query.where(field_name, operator, value)
        return self

    def order_by(self, field_name, direction="ASCENDING"):
        """
        Добавляет сортировку к запросу.
        :param field_name: Имя поля для сортировки.
        :param direction: Направление сортировки ("ASCENDING" или "DESCENDING").
        :return: self (для цепочки вызовов).
        """
        direction_enum = firestore.Query.ASCENDING if direction.upper() == "ASCENDING" else firestore.Query.DESCENDING
        self.query = self.query.order_by(field_name, direction=direction_enum)
        return self

    def limit(self, count):
        """
        Ограничивает количество возвращаемых документов.
        :param count: Максимальное количество документов.
        :return: self (для цепочки вызовов).
        """
        self.query = self.query.limit(count)
        return self

    def execute(self):
        """
        Выполняет запрос и возвращает результаты.
        :return: Список документов (словарей).
        """
        results = self.query.stream()
        return {doc.id: doc.to_dict() for doc in results}
    
    
    def like(self, field_name, value):
        """
        Добавляет условие фильтрации, похожее на SQL LIKE.
        Работает только для строк, которые начинаются с указанного значения.
        :param field_name: Имя поля для фильтрации.
        :param value: Значение для фильтрации (префикс строки).
        :return: self (для цепочки вызовов).
        """
        start_value = value
        end_value = value + "\uf8ff"  # Специальный символ для диапазона строк
        self.query = self.query.order_by(field_name).start_at([start_value]).end_at([end_value])
        return self