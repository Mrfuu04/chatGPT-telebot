import os
from typing import (
    Optional,
)

import openai
import strings
from database import (
    database,
)
from dotenv import (
    load_dotenv,
)
from telebot.types import (
    Message,
)

load_dotenv()


class ChatGPT:
    """Класс для работы с chatGPT."""

    MODEL = strings.GPT_MODEL
    SYSTEM_ROLE = strings.ASSISTANT_ROLE

    def __init__(self):
        API_KEY = os.getenv('CHAT_GPT_API_KEY')
        openai.api_key = API_KEY

        self.database = database
        self.messages = []

    def append_assistant_messages(self, user_id: int, active: Optional[bool] = True):
        """Добавить сообщения в контекст ассистента (assistant)."""

        assistant_messages = self.database.get_assistant_messages(user_id, active=active)

        for msg in assistant_messages:
            self.messages.extend([
                {
                    "role": "assistant",
                    "content": msg['user_message'],
                },
                {
                    "role": "assistant",
                    "content": msg['assistant_message'],
                },
            ])

    def append_system_role_message(self, user_id: int):
        """Добавить сообщение в контекст системы (system)."""

        system_role = self.database.get_system_role_message(user_id)
        role = system_role['system_role'] if system_role else self.SYSTEM_ROLE

        self.messages.append({'role': 'system', 'content': role})

    def ask_gpt(self, message_object: Message) -> str:
        """Основной метод. Через API OpenAI задает вопрос боту."""

        reply = strings.EXTERNAL_ERROR
        message = message_object.text

        if message:
            self.messages = []
            self.append_system_role_message(message_object.from_user.id)
            self.append_assistant_messages(message_object.from_user.id)

            self.messages.append(
                {
                    "role": "user",
                    "content": message,
                },
            )

            try:
                chat_gpt = openai.ChatCompletion.create(
                    model=self.MODEL,
                    messages=self.messages,
                )
            except openai.error.RateLimitError:
                pass
            else:
                reply = chat_gpt.choices[0].message.content
                self.database.create_message(message_object, reply)

        return reply
