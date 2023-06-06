import os
import openai
import json


class ChatCompletionMod:
    def __init__(self):
        pass

    def eval_text(self, message):
        token_path = "tokens.json"
        if not os.path.isfile(token_path):
            pass
        with open(token_path) as f:
            # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
            tokens = json.load(f)
            openai.organization = tokens["openai_organization"]
            openai.api_key = tokens["open_ai"]

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
