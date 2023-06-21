import os
from datetime import (
    datetime,
)
from typing import (
    Optional,
)

from dotenv import (
    load_dotenv,
)
from pymongo import (
    MongoClient,
)
from telebot.types import (
    Message,
)

load_dotenv()


class Database:
    """Работа с базой."""

    client = MongoClient(
        f'mongodb://{os.getenv("MONGO_INITDB_ROOT_USERNAME")}:{os.getenv("MONGO_INITDB_ROOT_PASSWORD")}@mongodb:27017/')
    db = client['db']
    message_collection = db['messages']

    def get_messages_collection_data(
            self, user_id: int,
            message_id: int,
            user_message: str,
            assistant_message: str,
            active: Optional[bool] = True,
    ) -> dict:
        """Получить стандартную структуру сообщения для mongoDB."""

        messages_collection_data = {
            'user_id': user_id,
            'message_id': message_id,
            'user_message': user_message,
            'assistant_message': assistant_message,
            'active': active,
            'date': datetime.utcnow(),
            'system_role': None,
        }

        return messages_collection_data

    def get_assistant_messages(self, user_id: int, active: Optional[bool] = True):
        """Получить сообщения ассистента."""

        assistant_messages = self.message_collection.find(
            {'user_id': user_id, 'active': active, 'system_role': None}
        )

        return assistant_messages

    def get_system_role_message(self, user_id: int):
        """Получить системную роль chatGPT."""

        system_role = self.message_collection.find_one(
            {'user_id': user_id, 'system_role': {'$ne': None}}
        )

        return system_role

    def create_message(self, message_object: Message, assistant_message: str):
        """Создать сообщение."""

        message = self.get_messages_collection_data(
            user_id=message_object.from_user.id,
            message_id=message_object.message_id,
            user_message=message_object.text,
            assistant_message=assistant_message,
        )

        self.message_collection.insert_one(message)

    def create_system_role_message(self, user_id, role):
        """Создать системную роль."""

        message = {
            'user_id': user_id,
            'system_role': role,
            'active': True,
        }

        self.message_collection.insert_one(message)

    def deactivate_message(self, message_id: int):
        """Деактивация сообщения."""

        query = {
            'message_id': message_id,
        }
        new_value = {
            '$set':
                {'active': False},
        }

        self.message_collection.update_one(query, new_value)

    def deactivate_all_messages(self, user_id: int):
        """Деактивация всех сообщений пользователя."""

        query = self._get_active_user_query(user_id)
        new_value = {
            '$set':
                {'active': False},
        }

        result = self.message_collection.update_many(query, new_value)

        return result.modified_count

    def set_new_role(self, user_id: int, role: str):
        """Установить новую роль бота."""
        
        query = self._get_active_user_query(user_id)
        new_value = {
            '$set':
                {'system_role': role},
        }

        exists = self.message_collection.find_one(query)

        if not exists:
            self.create_system_role_message(user_id, role)
        else:
            self.message_collection.update_one(query, new_value)

    def _get_active_user_query(self, user_id: int):
        """Получить фильтр активного пользователя."""

        query = {
            'user_id': user_id,
            'active': True,
        }

        return query


database = Database()
