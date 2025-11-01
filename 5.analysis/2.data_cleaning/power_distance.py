# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 15:10:27 2025

@author: Sumey """

import pandas as pd
df = pd.read_csv (r"C:\Users\Sumey\Downloads\powerdistance_annotations_merged.csv")


print(df.shape)




print(df.shape)
# 540, 26

print(df.columns)
#ensure naming of column is accurate
df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')


#dropping duplicates
# Drop exact duplicate rows
df = df.drop_duplicates()



print(df.shape) #same shape confirming no duplicates

#checking for nulls

df.isnull().sum()

#rejection_time has no values in these columns. Will remove these as they are irrelevant to power_distance


df.drop(columns=[ 'rejection_time'], inplace=True)

#check shape
print(df.shape)
# (540, 25)

# Check if all values are within [0, 1] and [1,5] for each column
alpha_valid = df['alpha'].between(1, 5).all()
beta_valid = df['beta'].between(1, 5).all()
mode_valid = df['mode'].between(0, 1).all()

print("Alpha values within range:", alpha_valid)
print("Beta values within range:", beta_valid)
print("Mode values within range:", mode_valid)
# false for alpha


# Show rows where alpha is out of range
alpha_outliers = df[(df['alpha'] < 1) | (df['alpha'] > 5)]
print("Out-of-range alpha values:")
print(alpha_outliers[['prompt_id', 'output_id', 'model', 'alpha']])

# alpha is = t 5.25

#changing it to the possible maximum of 5.
df['alpha'] = df['alpha'].clip(lower=1, upper=5)

print("Alpha values within range:", df['alpha'].between(1, 5).all())

# true
df.to_csv(r"C:\Users\Sumey\OneDrive\DATA Science\2025\LLM\data cleaning\final_data/powerdistance_cleaned_data", index=False)




