

import pandas as pd
df = pd.read_csv (r"C:\Users\Sumey\Downloads\worldview_annotations_merged.csv")


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

# rejection_time has no values in these columns. Will remove these as they are irrelevant 


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
#true for all


# true
df.to_csv(r"C:\Users\Sumey\OneDrive\DATA Science\2025\LLM\data cleaning\final_data/worldview_cleaned_data", index=False)




