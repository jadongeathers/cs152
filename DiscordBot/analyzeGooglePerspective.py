import os 
import json 
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from datasets import load_dataset
import time
import pandas as pd
from sklearn.linear_model import LogisticRegression
import numpy as np
import math
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

def eval_text(google, message):
    analyze_request = {
        'comment': {'text': message},
        'requestedAttributes': {
            'IDENTITY_ATTACK': {},
            'INSULT': {},
            'THREAT': {}
        }
    }
    try:
        response = google.comments().analyze(body=analyze_request).execute()
        probs = {flag: response['attributeScores'][flag]['summaryScore']['value'] for flag in response['attributeScores']}
        return probs
    except HttpError as e:
        this_error = e
        if 'LANGUAGE_NOT_SUPPORTED_BY_ATTRIBUTE' in str(e):
            return {}
        breakpoint()
        # if  "Attribute THREAT does not support request languages":
        #     return 
        

def trainGooglePerspective():
    hate_datasets = load_dataset('classla/FRENK-hate-en',"multiclass")
    val_df = hate_datasets['validation'].to_pandas()


    token_path = 'tokens.json'
    if not os.path.isfile(token_path):
        raise Exception(f"{token_path} not found!")
    with open(token_path) as f:
        # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
        tokens = json.load(f)
        google_token = tokens['google']

    API_KEY = google_token

    google = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
    )

    model_output = []
    for i in range(val_df.shape[0]):
        print(i)
        time.sleep(1)
        model_output.append(eval_text(google, val_df.loc[val_df.index[i],'text']))
    
    model_output = pd.DataFrame(model_output)
    y = val_df[~model_output.isna().sum(axis=1).astype(bool)].label.values
    y = np.where((y == 1) | (y == 2), 1, 0)
    X = model_output[~model_output.isna().sum(axis=1).astype(bool)].values
    clf = LogisticRegression(random_state=0).fit(X, y)
    print(f'\nOptimal coefficients are: intercept={clf.intercept_[0]}, {model_output.columns[0]}={clf.coef_[0][0]}, {model_output.columns[1]}={clf.coef_[0][1]}, {model_output.columns[2]}={clf.coef_[0][2]}\n')
    breakpoint()

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

def evaluateGooglePerspective():
    COEFFS = {
        'intercept': -1.8430630461127375,
        'INSULT': 3.0665049605198584,
        'IDENTITY_ATTACK': 0.21195243081036308,
        'THREAT': 0.16239476863923974
    }
    hate_datasets = load_dataset('classla/FRENK-hate-en',"multiclass")
    test_df = hate_datasets['test'].to_pandas()
    test_df = test_df.iloc[:100,]


    token_path = 'tokens.json'
    if not os.path.isfile(token_path):
        raise Exception(f"{token_path} not found!")
    with open(token_path) as f:
        # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
        tokens = json.load(f)
        google_token = tokens['google']

    API_KEY = google_token

    google = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
    )

    model_output = []
    for i in range(test_df.shape[0]):
        print(i)
        time.sleep(1)
        output = eval_text(google, test_df.loc[test_df.index[i],'text'])

        score = 0
        for key in output:
            score += COEFFS[key] * output[key]
        score += COEFFS['intercept']

        score = sigmoid(score)

        pred = int(score > 0.5)
        model_output.append(pred)

    model_output = np.array(model_output)
    y_true = test_df[~np.isnan(model_output).astype(bool)].label.values
    y_true = np.where((y_true == 1) | (y_true == 2), 1, 0)
    y_pred = model_output[~np.isnan(model_output)]

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    cm = cm / cm.sum()
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
    disp.plot()
    plt.title('Google Perspective Confusion Matrix')
    plt.show()

    breakpoint()

    

if __name__ == '__main__':
    # trainGooglePerspective()
    evaluateGooglePerspective()