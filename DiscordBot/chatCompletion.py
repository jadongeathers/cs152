import os
import openai
import json
from token_handler import handle_tokens


class ChatCompletionMod:
    def __init__(self):
        pass

    def eval_text(self, message):
        openai.organization, openai.api_key = handle_tokens("chat_completion")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a content moderation system. Classify each input as either violent speech, hateful speech, or not threatening.",
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )

        output = response["choices"][0]["message"]["content"]
        return output
