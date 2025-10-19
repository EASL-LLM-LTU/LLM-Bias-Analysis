

import pandas as pd
import numpy as np
from pathlib import Path

# read file

bt = pd.read_csv(r"C:\Users\Sumey\OneDrive\DATA Science\2025\LLM\data cleaning\bloctilt_annotations_merged.csv")

print(bt.shape)
# 540, 26

print(bt.columns)

#ensure naming of column is accurate
bt.columns = bt.columns.str.lower().str.strip().str.replace(' ', '_')


#dropping duplicates
# Drop exact duplicate rows
bt = bt.drop_duplicates()

print(bt.shape) #same shapie confirming no duplicates

#checking for nulls

bt.isnull().sum()

#gender_ange and rejection_time has no values in these columns. Will remove these as they are irrelevant to
# block tilt. 

bt.drop(columns=['gender_range', 'rejection_time'], inplace=True)

#check shape
print(bt.shape)
# (540, 24)

# checking if all the values are within range.


# Check if all values are within [0, 1] for each column
alpha_valid = bt['alpha'].between(1, 5).all()
beta_valid = bt['beta'].between(1, 5).all()
mode_valid = bt['mode'].between(0, 1).all()

print("Alpha values within range:", alpha_valid)
print("Beta values within range:", beta_valid)
print("Mode values within range:", mode_valid)

#true for all

#checking for outliers - this is interesting to note for further analysis. 
numeric_cols = bt.select_dtypes(include='number').columns
for col in numeric_cols:
    outliers = bt[(bt[col] < bt[col].quantile(0.01)) | (bt[col] > bt[col].quantile(0.99))]
    if not outliers.empty:
        print(f"Outliers in {col}:")
        print(outliers[[col]])
