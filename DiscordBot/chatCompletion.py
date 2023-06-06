import os
import openai
import json

if __name__ == "__main__":
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
                "content": "I love humans",
            },
        ],
    )

    # last_message = response["message"]["content"]
    output = response["choices"][0]["message"]["content"]
    # print("The last message is " + last_message)
    print("Which category does this message fall under?")
    print(output)
