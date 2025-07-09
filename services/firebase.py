import firebase_admin
from firebase_admin import credentials, firestore
from services.config import FIREBASE_CREDENTIALS

cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_document(collection, document_id):
    doc_ref = db.collection(collection).document(document_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data.pop('collection_name', None)  # Удаляем ненужные поля
        data.pop('document_id', None)
        return data
    else:
        return None

def set_document(collection, document_id, data):
    data['document_id'] = document_id  # Добавляем только document_id
    db.collection(collection).document(document_id).set(data)

def delete_document(collection, document_id):
    db.collection(collection).document(document_id).delete()

def get_all_document_ids(collection):
    """Получает все document_id из указанной коллекции."""
    collection_ref = db.collection(collection)
    docs = collection_ref.stream()
    return [doc.id for doc in docs]

# def get_archived_user(document_id):
#     """Получает данные пользователя из коллекции archived_users."""
#     return get_document('archived_users', document_id)

# def set_archived_user(document_id, data):
#     """Сохраняет данные пользователя в коллекцию archived_users."""
#     set_document('archived_users', document_id, data)

# def delete_archived_user(document_id):
#     """Удаляет данные пользователя из коллекции archived_users."""
#     delete_document('archived_users', document_id)

def get_all_archived_user_ids():
    """Получает все document_id из коллекции archived_users."""
    return get_all_document_ids('archived_users')

def debug_check_user_data(user_id):
    data = get_document('users', user_id)
    if data:
        print(f"[DEBUG] Данные пользователя {user_id}: {data}")
    else:
        print(f"[WARNING] Пользователь {user_id} не найден в базе данных.")
