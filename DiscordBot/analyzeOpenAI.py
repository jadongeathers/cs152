import os
import openai
import datasets
import json
import pandas as pd
import numpy as np
import math
from tqdm import tqdm
import time
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib
import matplotlib.pyplot as plt
# from token_handler import handle_tokens

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

        openai.api_key = openai_token
        response = openai.Moderation.create(input=message)
        output = response["results"]

        detecting = ["hate", "hate/threatening", "violence"]
        for key in output:
            probs = {type: key["category_scores"][type] for type in detecting}

        return probs

    def trainOpenAI(self):
        # additional training specifically on a dataset involving LGBT-related speech in hopes of further improving at those types of speech

        valset = self.ds["validation"].to_pandas()

        output = []
        for i in tqdm(range(valset.shape[0])):
            time.sleep(1)
            open_ai = self.eval_text(valset.loc[valset.index[i], "text"])
            output.append(open_ai)

        output = pd.DataFrame(output)
        y = valset[~output.isna().sum(axis=1).astype(bool)].label.values
        y = np.where((y == 1) | (y == 2), 1, 0)
        X = output[~output.isna().sum(axis=1).astype(bool)].values
        clf = LogisticRegression(random_state=0).fit(X, y)
        print(
            f"\nOptimal coefficients are: intercept={clf.intercept_[0]}, {model_output.columns[0]}={clf.coef_[0][0]}, {model_output.columns[1]}={clf.coef_[0][1]}, {model_output.columns[2]}={clf.coef_[0][2]}\n"
        )
        breakpoint()

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def get_cm(self, ds, model_output, title):
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        # edited it to see what I could do (this is the commented out section beneath this)
        # and wasn't able to change anything
        model_output = np.array(model_output)
        y_true = ds[~np.isnan(model_output).astype(bool)].label.values
        y_true = np.where((y_true == 1) | (y_true == 2), 1, 0)
        y_pred_scores = model_output[~np.isnan(model_output)]
        y_pred = np.where(y_pred_scores > 0.5, 1, 0)

        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        cm = cm / cm.sum()
        matplotlib.rcParams.update({'font.size': 18})
        fig, ax = plt.subplots()
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
        disp.plot(cmap='Reds', ax=ax)
        plt.title(title, fontdict={'family': '.Keyboard', 'size': 16})
        plt.xlabel('Predicted Label', fontdict={'family': '.Keyboard', 'size': 15})
        plt.ylabel('True Label', fontdict={'family': '.Keyboard', 'size': 15})
        plt.show()
        # model_output = np.array(model_output)
        # y_true = ds[~np.isnan(model_output).astype(bool)].label.values
        # y_true = np.where((y_true == 1) | (y_true == 2), 1, 0)
        # y_pred_scores = model_output[~np.isnan(model_output)]
        # y_pred = np.where(y_pred_scores > 0.5, 1, 0)
        #
        # cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        # cm = cm / cm.sum()
        # matplotlib.rcParams.update({'font.size': 18})
        # fig, ax = plt.subplots()
        # # ax.set_facecolor('white')
        # ax.spines['bottom'].set_color('black')
        # ax.spines['top'].set_color('black')
        # ax.spines['right'].set_color('black')
        # ax.spines['left'].set_color('black')
        # ax.tick_params(colors='black', which='both')
        # # ax.set_ylabel(color='white')
        # # ax.set_xlabel(color='white')
        # disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
        # # ax.yaxis.label.set_color('w')
        # # ax.xaxis.label.set_color('w')
        # # ax.title.set_color('w')
        # disp.plot(cmap='Reds', ax=ax)
        # plt.title(title, fontdict={'family': '.Keyboard', 'size': 16, 'color': 'black'})
        # plt.xlabel('Predicted Label', fontdict={'family': '.Keyboard', 'size': 15, 'color': 'black'})
        # plt.ylabel('True Label', fontdict={'family': '.Keyboard', 'size': 15, 'color': 'black'})
        # plt.show()
        return y_true, y_pred_scores, y_pred

    def evalOpenAI(self):
        COEFFS = {
            "intercept": -1.6949516955386068,
            "hate": 2.514414538130454,
            "hate/threatening": -0.11870110156245899,
            "violence": -0.7040727776293726,
        }

        testset = self.ds["test"].to_pandas()
        testset = testset.iloc[:100,]

        model_output = []
        for i in tqdm(range(testset.shape[0])):
            time.sleep(1)
            output = self.eval_text(testset.loc[testset.index[i], "text"])

            score = 0
            for key in output:
                score += COEFFS[key] * output[key]

            score += COEFFS["intercept"]
            score = self.sigmoid(score)
            model_output.append(score)

        # print(len(model_output))
        # print(testset.shape)

        y_true, y_pred_scores, y_pred = self.get_cm(testset, model_output, title="OpenAI")

        samples = pd.read_csv("test_samples.csv")
        samples["openai_prediction"] = y_pred
        samples["openai_scores"] = y_pred_scores
        samples.to_csv("test_samples.csv")

        # samples.to_csv("test_samples2.csv")
        # samples.to_csv("test_samples.csv", mode="a")

    # testing two types of combinations to see if confusion matrix changes:
    # combo1: adding scores output by both models, reverifying if the combined score > 5
    # combo2: inputting messages flagged by Google Perspective into OpenAI
    def evalCombos(self):
        COEFFS = {
            "intercept": -1.6949516955386068,
            "hate": 2.514414538130454,
            "hate/threatening": -0.11870110156245899,
            "violence": -0.7040727776293726,
        }

        testset = self.ds["test"].to_pandas()
        testset = testset.iloc[:100,]

        test_samples = pd.read_csv("test_samples.csv")

        model_output1 = []
        model_output2 = []
        for idx, row in test_samples.iterrows():
            model_output1.append(row["perspective_scores"] + row["openai_scores"])

            if row["perspective_prediction"] == 1 and row["openai_prediction"] == 1:
                model_output2.append(row["openai_scores"])
            else: model_output2.append(0)

        y_true, y_pred_scores, y_pred = self.get_cm(testset, model_output1, title="Combination 1")
        test_samples["combo1_prediction"] = y_pred
        test_samples['combo1_scores'] = y_pred_scores
        # breakpoint()

        y_true_other, y_pred_scores_other, y_pred_other = self.get_cm(testset, model_output2, title="Combination 2")
        test_samples["combo2_prediction"] = y_pred_other
        # don't need scores here because it's the same as samples['openai_scores']
        # breakpoint()

        test_samples.to_csv("test_samples.csv")


if __name__ == "__main__":
    openai_model = OpenAIMod()
    openai_model.evalCombos()


##############################
# Commented functions below were for a previous version of our evaluation plan
# They just print categories flagged by the Moderator model and corresponding category scores

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
