import openai
import datasets
# from bot import ModBot

class OpenAIMod:
    def __init__(self):
        self.ds = datasets.load_dataset("classla/FRENK-hate-en","multiclass")

    def discord_eval(self, message):
        response = openai.Moderation.create(message)
        output = response["results"]
        eval = []
        for key in output:
            for type in key["category_scores"]:
                if key["category_scores"][type] > 0.5:
                    eval.append(type + ": " + str(key['category_scores'][type]))
        return eval

    # testing to see abuse categories detected/determined by OpenAI's Moderator API matches
    # the attr
    def ds_test(self):
        messages = [example["test"] for example in self.ds["test"]]
        for i in messages:
            response = openai.Moderation.create(input = i)
            output = response["results"]
            for key in output:
                for type in key["categories"]:
                    if key["categories"][type] == True:
                        return type


# ds = datasets.load_dataset("classla/FRENK-hate-en","multiclass")
# for example in ds["test"]:
#     message = example["text"]
#     topic = example["topic"]
#     label = example["label"]
#
#     for message in example:
#         response = openai.Moderation.create(input = message)
#         output = response["results"]
#         eval = []
#         for key in output:
#             for type in key["category_scores"]:
#                 if key["category_scores"][type] > 0.5:
#                     eval.append(type + ": " + str(key['category_scores'][type]))


    
# messages = [example["text"] for example in ds["test"]]
# for i in messages:
#     response = openai.Moderation.create(input = i)
#     output = response["results"]
#     for key in output:
#         for type in key["categories"]:
#             if key["categories"][type] == True:
#                 print(type)
