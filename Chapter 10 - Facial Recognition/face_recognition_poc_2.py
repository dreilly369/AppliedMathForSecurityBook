#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import joblib
from nominal import associations, correlation_ratio
from random import choice, randint
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import LeaveOneOut

faces_df = pd.read_csv("facial_geometry.csv")
image_files = faces_df["file"]
faces_df.drop(["Unnamed: 0", "file"], inplace=True, axis=1)
faces_df.dropna(inplace=True, axis=1)
faces_df.replace(np.nan, 0, inplace=True)
faces_df["category"] = faces_df["name"].astype("category")
cat_columns = faces_df.select_dtypes(["category"]).columns
faces_df[cat_columns] = faces_df[cat_columns].apply(lambda x: x.cat.codes)
name_map = faces_df[["name", "category"]].set_index(["category"])


print("%d people, %d images" % (len(faces_df["name"].unique()), len(faces_df.index)))


# Creating the true holdout set

real_test = {}
while len(real_test) < 3:
    name = choice(list(faces_df["name"].unique()))
    if name not in real_test.keys():
        group = faces_df[faces_df["name"] == name]
        real_test[name] = choice(group.index.to_list())
index_list = [r[1] for r in real_test.items()]
real_X = faces_df.iloc[index_list]
faces_df.drop(index_list, inplace=True)

#Using Thiel's U for Nominal-Nominal Associations
assoc_matrix = associations(faces_df, nominal_columns=['name'], theil_u=True, return_results=True,  annot=False, cmap="Blues_r")
assoc_matrix = assoc_matrix[abs(assoc_matrix["name"]) > 0.95]
key_features = list(assoc_matrix["name"].index)[1:]

# Using association measure

assoc_matrix = associations(faces_df[key_features].drop("category", axis=1), nominal_columns=["name"], annot=False, cmap="Blues_r")

# Using Mutual Information Classification
contributing = mutual_info_classif(
        faces_df.drop(["name", "category"], axis=1),
        faces_df["category"],
        discrete_features="auto",
        n_neighbors=7
)

results = zip(faces_df.drop(["name", "category"], axis=1).columns, contributing)
cutoff = max(contributing) * 0.75
mutual_inf_feats = [f for f,v in results if v >= cutoff]
reduced_features = [k for k in mutual_inf_feats if k in key_features]
print(reduced_features)
print(len(reduced_features))

# Using Correlation Ratio
etas = {}
for feat in faces_df.columns.to_list():
    if feat not in ["category", "name"]:
        etas[feat] = correlation_ratio(faces_df[feat], faces_df["category"])
sorted_rank = sorted(etas.items(), key=lambda kv: kv[1])
reduced_key_features = []
for f in sorted_rank[-21:]:
    if f[0] in reduced_features:
        reduced_key_features.append(f[0])
reduced_key_features


# Model training

X = faces_df[reduced_key_features]
y = faces_df["category"]
loo = LeaveOneOut()
splits = list(loo.split(X))

# ## Dummy classifier

dc = DummyClassifier(strategy="uniform")
scores = []
hits = 0
misses = 0
for train_index, test_index in splits:
    X_train, y_train, = X.iloc[train_index], y.iloc[train_index]
    X_test, y_test, = X.iloc[test_index], y.iloc[test_index]  
    cvs = cross_val_score(dc, X_train, y_train, cv=4)
    score = sum(cvs) / 4
    scores.append(score)
    dc.fit(X_train, y_train)
    y_pred = dc.predict(X_test)
    if y_test.values[0]==y_pred:
        hits += 1
    else:
        misses += 1
print(sum(scores) / len(scores))
print (hits, (hits+misses))
print (hits / (hits+misses))

# Using Random Forest classification
rfc = RandomForestClassifier(n_estimators=100, min_samples_split=5, min_samples_leaf=3)
scores = []
chose = []
hits = 0
misses = 0
for i in range(50):
    split_i = randint(0, len(splits))
    while split_i in chose:
        split_i = randint(0, len(splits))
    chose.append(split_i)
    train_index, test_index = splits[split_i]
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]    
    cvs = cross_val_score(rfc, X_train, y_train, cv=4)
    score = sum(cvs) / 4
    scores.append(score)
    rfc.fit(X_train, y_train)
    y_pred = rfc.predict(X_test)
    if y_test.values[0]==y_pred:
        hits += 1
    else:
        misses += 1
print(sum(scores) / len(scores))
print (hits, (hits+misses))
print (hits / (hits+misses))

# Save the trained model for production deployment
joblib.dump(rfc, "trained_facial_model.pkl") 

# Verifying the model
real_y = real_X["category"]
test_X = real_X[reduced_key_features]
rfc = RandomForestClassifier(n_estimators=100, min_samples_split=5, min_samples_leaf=3)
rfc.fit(X, y)
y_pred = rfc.predict(test_X)
print(list(zip(y_pred, real_y)))

# You can reload the saved model with
rfc2 = joblib.load("trained_facial_model.pkl")
print(type(rfc2))
