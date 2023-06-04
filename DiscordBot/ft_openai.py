import openai
import datasets
from bot import ModBot



# class OpenAI_Mod:
#     openai.organization = "org-YVZe9QFuR0Ke0J0rqr7l2R2L"
#     openai.api_key = "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"
#     # print(openai.Model.list())
#     def ds_test(self):
#         ds = datasets.load_dataset("classla/FRENK-hate-en","multiclass")
#         # print(ds['test'][0]['text'])
#
#         messages = [example["test"] for example in ds["test"]]
#         for i in messages:
#             response = openai.Moderation.create(input = i)
#             output = response["results"]
#             for key in output:
#                 for type in key["categories"]:
#                     if key["categories"][type] == True:
#                         return type
#
#     def discord_eval(self, message):
#         response = openai.Moderation.create(input = message)
#         output = response["results"]
#         for key in output:
#             print(key)
#

class OpenAIMod:
    openai.organization = "org-YVZe9QFuR0Ke0J0rqr7l2R2L"
    openai.api_key = "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"

    def discord_eval(self, message):
        response = openai.Moderation.create(message)
        output = response["results"]
        eval = []
        for key in output:
            for type in key["category_scores"]:
                if key["category_scores"][type] > 0.5:
                    eval.append(type + ": " + str(key['category_scores'][type]))
        return eval

    