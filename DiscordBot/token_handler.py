import openai
import json
import os

def handle_tokens(model):
    token_path = "tokens.json"
    if not os.path.isfile(token_path):
        raise Exception(f"{token_path} not found!")
    with open(token_path) as f:
        # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
        tokens = json.load(f)
        if model == "google":
            google_token = tokens["google"]
            return google_token
        elif model == "open_ai":
            openai_token = tokens["open_ai"]
            return openai_token
        elif model == "chat_completion":
            openai_organization = tokens["openai_organization"]
            openai_token = tokens["open_ai"]
            return openai_organization, openai_token
        elif model == "bot":
            discord_token = tokens["discord"]
            google_token = tokens["google"]
            openai_token = tokens["open_ai"]
            return discord_token, google_token, openai_token
        elif model == "combo":
            return
