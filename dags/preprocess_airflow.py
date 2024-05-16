from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator,BranchPythonOperator
from airflow.operators.bash import BashOperator
import sys
import requests
import pandas as pd
import numpy as np
from zipfile import ZipFile

training_csv_url = "https://storage.googleapis.com/kaggle-competitions-data/kaggle-v2/62891/6855609/compressed/training.csv.zip?GoogleAccessId=web-data@kaggle-161607.iam.gserviceaccount.com&Expires=1716100019&Signature=cz%2FG3wvyhW9QcUGYEAJ2bNXo6%2FIgCjqrbvxZGtyEC7%2BuoZkfBknQIlCuccOA82cjZjppreHd9XQcWXHNVvudXozi1iJJhcQzdZoqUzMux3lrBSZGGtZ%2BTYufw53k5WMQ2ByF%2Fm%2FhqJSjTlijkZOfRMJgbJkvGIcbMwIZxOwmXho%2FQjn6XGxSTsbNYaBfDl9%2FFtxqUz7eM42Y6WHzRbCbinHh0NqnRIAWNwh6ixYM7GRdSVhJiMmS7Ed9oLMvTUQBgi6qgyRB5BDejTJ6v31mCQdJcO0Nb53bbmzxl42nFMnBEtw3HhVgkD4rJcDbQXiWLRs0C1rKC5w2jGDA2c10sw%3D%3D&response-content-disposition=attachment%3B+filename%3Dtraining.csv.zip"

# here we'll include the entire preprocessing code, where we get the training.csv dataset and produce the train_new and val_new sets from it.
# Then you put it on Github
# These are later used for "training experiments" which you can run on MLFlow. Use the model you've made and add some hyperparameter tuning to it.

def _preprocess_data(**kwargs):
    data_path = "/Users/nikhilanand/BigDataLabProject/data"
    train = pd.read_csv(data_path+"/training.csv")

    # columns_4: Set of columns representing only 4 keypoints (8 coordinates)
    # columns_15: Set of columns representing all 15 keypoint (30 coordinates)
    columns_4 = ['left_eye_center_x', 'left_eye_center_y', 'right_eye_center_x', 'right_eye_center_y',
             'mouth_center_bottom_lip_x', 'mouth_center_bottom_lip_y', 'nose_tip_x', 'nose_tip_y']
    columns_15 = ['left_eye_center_x', 'left_eye_center_y', 'right_eye_center_x', 'right_eye_center_y',
              'left_eye_inner_corner_x', 'left_eye_inner_corner_y', 'left_eye_outer_corner_x',
              'left_eye_outer_corner_y', 'right_eye_inner_corner_x', 'right_eye_inner_corner_y',
              'right_eye_outer_corner_x', 'right_eye_outer_corner_y', 'left_eyebrow_inner_end_x',
              'left_eyebrow_inner_end_y', 'left_eyebrow_outer_end_x', 'left_eyebrow_outer_end_y',
              'right_eyebrow_inner_end_x', 'right_eyebrow_inner_end_y', 'right_eyebrow_outer_end_x',
              'right_eyebrow_outer_end_y', 'nose_tip_x', 'nose_tip_y', 'mouth_left_corner_x',
              'mouth_left_corner_y', 'mouth_right_corner_x', 'mouth_right_corner_y',
              'mouth_center_top_lip_x', 'mouth_center_top_lip_y', 'mouth_center_bottom_lip_x',
              'mouth_center_bottom_lip_y']
    
    difference = list(filter(lambda item: item not in columns_4,columns_15))
    assert len(difference) == 22

    # Creating train_4, the dataset where the keypoints in the "difference" are NaN
    boolseries = train[difference[0]].isna()
    for i in range(1,len(difference)):
        boolseries = boolseries & train[difference[i]].isna()

    train_4 = train[boolseries]
    assert train_4.shape == (4765,31)

    boolseries2 = ~boolseries
    train_15 = train[boolseries2]
    assert train_15.shape == (784,31)

    # Saving everything to separate csvs
    train_4.iloc[:100,:].to_csv(data_path+"/val_4.csv",index=False)
    train_4.iloc[100:,:].to_csv(data_path+"/train_4.csv",index=False)
    train_15.iloc[:100,:].to_csv(data_path+"/val_15.csv",index=False)
    train_15.iloc[100:,:].to_csv(data_path+"/train_15.csv",index=False)

    # Loading the csvs again and concatenating them; saving the concatenated dataset
    train_4new = pd.read_csv(data_path+"/train_4.csv")
    train_15new = pd.read_csv(data_path+"/train_15.csv")
    trainingnew = pd.concat([train_4new,train_15new],ignore_index=True)
    val_4new = pd.read_csv(data_path+"/val_4.csv")
    val_15new = pd.read_csv(data_path+"/val_15.csv")
    valnew = pd.concat([val_4new,val_15new],ignore_index=True)
    trainingnew.to_csv(data_path+"/training_new.csv",index=False)
    valnew.to_csv(data_path+"/val_new.csv",index=False)

def _unzip_data(**kwargs):
    with ZipFile("/Users/nikhilanand/BigDataLabProject/data/train.zip", 'r') as zObject: 
        zObject.extractall(path="/Users/nikhilanand/BigDataLabProject/data")

with DAG("keypoints_dag", start_date=datetime(2021,1,1),
         schedule_interval="@daily", catchup=False) as dag:
    print("curl -o data/training.csv \"" + training_csv_url + "\"")
    fetch_data = BashOperator(task_id="fetch_data",bash_command="curl -o /Users/nikhilanand/BigDataLabProject/data/train.zip \"" + training_csv_url + "\"")
    unzip_data = PythonOperator(task_id="unzip_data",python_callable=_unzip_data)
    preprocess_data = PythonOperator(task_id="preprocess_data",python_callable=_preprocess_data)

    fetch_data >> unzip_data >> preprocess_data