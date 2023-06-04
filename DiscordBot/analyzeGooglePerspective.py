import os 
import json 
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from datasets import load_dataset
import time
import pandas as pd
from sklearn.linear_model import LogisticRegression

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
        

def main():
    hate_datasets = load_dataset('classla/FRENK-hate-en')
    train_df = hate_datasets['train'].to_pandas()
    val_df = hate_datasets['validation'].to_pandas()
    test_df = hate_datasets['test'].to_pandas()


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
    X = model_output[~model_output.isna().sum(axis=1).astype(bool)].values
    clf = LogisticRegression(random_state=0).fit(X, y)
    print(f'\nOptimal coefficients are: intercept={clf.intercept_[0]}, {model_output.columns[0]}={clf.coef_[0][0]}, {model_output.columns[1]}={clf.coef_[0][1]}, {model_output.columns[2]}={clf.coef_[0][2]}\n')
    breakpoint()
        


if __name__ == '__main__':
    main()