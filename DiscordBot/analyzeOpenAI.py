import os
import openai
import datasets
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import math
import time
from tqdm import tqdm
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# from bot import ModBot


class OpenAIMod:
    def __init__(self):
        self.ds = datasets.load_dataset("classla/FRENK-hate-en", "multiclass")

    def eval_text(self, message):
        token_path = "tokens.json"
        if not os.path.isfile(token_path):
            raise Exception(f"{token_path} not found!")
        with open(token_path) as f:
            # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
            tokens = json.load(f)
            openai_token = tokens["open_ai"]

        # API_KEY = openai_token
        openai.api_key = openai_token
        response = openai.Moderation.create(input=message)
        output = response["results"]
        # eval = []

        detecting = ["hate", "hate/threatening", "violence"]
        for key in output:
            probs = {type: key["category_scores"][type] for type in detecting}
        #
        #         # run logR to get the coeffs
        #         if key["category_scores"][type] > 0.5:
        #             eval.append(type + ": " + str(key['category_scores'][type]))
        #
        #           probs = {flag: response['attributeScores'][flag]['summaryScore']['value'] for flag in response['attributeScores']}
        return probs

    def trainOpenAI(self):
        valset = self.ds["validation"].to_pandas()

        model_output = []
        for i in tqdm(range(valset.shape[0])):
            # time.sleep(1)
            open_ai = OpenAIMod.eval_text(self, valset.loc[valset.index[i], "text"])
            model_output.append(open_ai)

        model_output = pd.DataFrame(model_output)
        y = valset[~model_output.isna().sum(axis=1).astype(bool)].label.values
        y = np.where((y == 1) | (y == 2), 1, 0)
        X = model_output[~model_output.isna().sum(axis=1).astype(bool)].values
        clf = LogisticRegression(random_state=0).fit(X, y)
        print(
            f"\nOptimal coefficients are: intercept={clf.intercept_[0]}, {model_output.columns[0]}={clf.coef_[0][0]}, {model_output.columns[1]}={clf.coef_[0][1]}, {model_output.columns[2]}={clf.coef_[0][2]}\n"
        )
        breakpoint()

        # Optimal coefficients are: intercept=-1.6949516955386068,
        # hate=2.514414538130454,
        # hate/threatening=-0.11870110156245899,
        # violence=-0.7040727776293726

    def sigmoid(x):
        return 1 / (1 + math.exp(-x))

    def evalOpenAI(self):
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))

        COEFFS = {
            "intercept": -1.6949516955386068,
            "hate": 2.514414538130454,
            "hate/threatening": -0.11870110156245899,
            "violence": -0.7040727776293726,
        }
        testset = self.ds["test"].to_pandas()
        testset = testset.iloc[:100,]

        token_path = "tokens.json"
        if not os.path.isfile(token_path):
            raise Exception(f"{token_path} not found!")
        with open(token_path) as f:
            # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
            tokens = json.load(f)
            openai_token = tokens["open_ai"]

        # API_KEY = openai_token
        openai.api_key = openai_token

        # TODO: change model
        openai_model = openai.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=openai.api_key,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )

        model_output = []
        for i in range(testset.shape[0]):
            print(i)
            time.sleep(1)
            output = eval_text(openai_model, testset.loc[testset.index[i], "text"])

            score = 0
            for key in output:
                score += COEFFS[key] * output[key]
            score += COEFFS["intercept"]

            score = sigmoid(score)

            pred = int(score > 0.5)
            model_output.append(pred)

        model_output = np.array(model_output)
        y_true = testset[~np.isnan(model_output).astype(bool)].label.values
        y_true = np.where((y_true == 1) | (y_true == 2), 1, 0)
        y_pred = model_output[~np.isnan(model_output)]

        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        cm = cm / cm.sum()
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
        disp.plot()
        plt.title("OpenAI Model Confusion Matrix")
        plt.show()

        breakpoint()

    # need to write a column to the csv with predictions

    def ds_test(self):
        messages = [example["test"] for example in self.ds["test"]]
        for i in messages:
            response = openai.Moderation.create(input=i)
            output = response["results"]
            for key in output:
                for type in key["categories"]:
                    if key["categories"][type] == True:
                        return type


if __name__ == "__main__":
    openai_model = OpenAIMod()
    coeffs = openai_model.trainOpenAI()

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
